from flask import Flask
from src.api.routes import api
from config.settings import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from src.services.dingtalk import send_dingtalk_message
from src.services.excel_handler import get_original_duty_person, get_today_date, get_bug_assignment_person
from src.utils.logger import get_logger, log_execution_time, LogContext
import schedule
import time
from threading import Thread
import threading
import os

# 获取日志器
logger = get_logger('app')

# 全局变量，确保定时任务只启动一次
_scheduler_started = False
_scheduler_lock = threading.Lock()
_process_id = os.getpid()  # 获取当前进程ID


def create_app():
    """创建Flask应用"""
    with LogContext("创建Flask应用"):
        app = Flask(__name__)
        app.register_blueprint(api, url_prefix='/api')

        # 添加兼容路由，处理 /dingtalk/webhook 请求
        @app.route('/dingtalk/webhook', methods=['GET', 'POST'])
        def direct_webhook():
            from src.api.routes import dingtalk_webhook
            return dingtalk_webhook()

        logger.info("Flask应用创建成功")
        return app


@log_execution_time
def send_bug_assignment_notification(test_data=None):
    """发送每日禅道指派人员通知"""
    logger.info('发送每日禅道指派人员通知')

    with LogContext("发送禅道指派通知"):
        today = get_today_date()
        logger.info(f'发送日期：{today}')
        bug_person = get_bug_assignment_person(today)

        if bug_person:
            content = f"【今日禅道指派】\n日期：{today}\n指派人员：{bug_person}"
            logger.info(f"准备发送钉钉通知，内容：{content}")

            # 发送钉钉通知
            try:
                send_dingtalk_message(content)
                logger.info(f"✅ 已发送{today}禅道指派通知给{bug_person}")
            except Exception as e:
                logger.error(f"❌ 发送{today}禅道指派通知失败: {str(e)}")
                raise
        else:
            logger.warning(f"⚠️ 未找到{today}的禅道指派人员")


@log_execution_time
def send_daily_notification(test_data=None):
    """发送每日值班通知"""
    logger.info(f"[进程{os.getpid()}] 开始发送值班通知 - {time.strftime('%Y-%m-%d %H:%M:%S')}")

    with LogContext("发送每日值班通知"):
        today = get_today_date()
        logger.info(f"查询{today}的值班人员")
        oncall_person = get_original_duty_person(today)

        if oncall_person:
            content = f"【今日值班通知】\n日期：{today}\n值班人：{oncall_person}"
            logger.info(f"准备发送钉钉通知，内容：{content}")

            # 发送钉钉通知
            try:
                send_dingtalk_message(content)
                logger.info(f"✅ [进程{os.getpid()}] 已发送{today}值班通知给{oncall_person}")
            except Exception as e:
                logger.error(f"❌ [进程{os.getpid()}] 发送{today}值班通知失败: {str(e)}")
                raise
        else:
            logger.warning(f"⚠️ [进程{os.getpid()}] 未找到{today}的值班人员")


@log_execution_time
def send_combined_notification(test_data=None):
    """发送综合通知（值班+禅道指派）"""
    logger.info(f"[进程{os.getpid()}] 开始发送综合通知 - {time.strftime('%Y-%m-%d %H:%M:%S')}")

    with LogContext("发送综合工作安排通知"):

        if test_data is None:
            today = get_today_date()
            logger.debug("使用今天作为目标日期")
        else:
            today = test_data
            logger.debug(f"使用指定日期: {test_data}")

        logger.info(f"查询{today}的工作安排")

        oncall_person = get_original_duty_person(today)
        bug_person = get_bug_assignment_person(today)

        logger.info(f"值班人员: {oncall_person or '未找到'}, 禅道指派: {bug_person or '未找到'}")

        content_parts = [f"【OnCall】\n日期：{today}"]

        if oncall_person:
            content_parts.append(f"值班人：{oncall_person}")

        if bug_person:
            content_parts.append(f"禅道指派：{bug_person}")

        if len(content_parts) > 1:  # 除了标题还有其他内容
            content = "\n".join(content_parts)
            logger.info(f"准备发送综合通知，内容：{content}")

            try:
                send_dingtalk_message(content)
                logger.info(f"✅ [进程{os.getpid()}] 已发送{today}综合工作安排通知")
            except Exception as e:
                logger.error(f"❌ [进程{os.getpid()}] 发送{today}综合通知失败: {str(e)}")
                raise
        else:
            logger.warning(f"⚠️ [进程{os.getpid()}] 未找到{today}的工作安排信息")


def run_scheduler():
    """运行定时任务调度器"""
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            logger.info(f"[进程{os.getpid()}] 定时任务已启动，跳过重复启动")
            return
        _scheduler_started = True
        logger.info(f"[进程{os.getpid()}] 启动定时任务调度器")

    # 清除所有现有的定时任务
    schedule.clear()
    logger.info(f"[进程{os.getpid()}] 已清除所有现有定时任务")

    # 分别设置不同的时间发送不同类型的通知
    schedule.every().day.at("08:30").do(send_bug_assignment_notification)
    schedule.every().day.at("17:20").do(send_combined_notification)

    logger.info("�� 定时任务配置完成:")
    logger.info("  - 08:30 发送禅道指派通知")
    logger.info("  - 17:20 发送综合工作安排通知")
    logger.info("开始运行调度器...")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"定时任务执行异常: {str(e)}")
            time.sleep(60)  # 继续运行，不中断


# if __name__ == "__main__":
#     try:
#         logger.info("🚀 === OnCall系统启动 ===")
#         logger.info(f"进程ID: {os.getpid()}")
#         logger.info(f"Flask配置: {FLASK_HOST}:{FLASK_PORT}, Debug: {FLASK_DEBUG}")
#
#         app = create_app()
#
#         # 启动定时任务线程
#         logger.info("启动定时任务线程...")
#         scheduler_thread = Thread(target=run_scheduler, daemon=True)
#         scheduler_thread.start()
#         logger.info("定时任务线程启动成功")
#
#         logger.info(f"✅ 应用启动成功，监听端口 {FLASK_PORT}")
#         logger.info("系统已就绪，等待请求...")
#
#         app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
#
#     except KeyboardInterrupt:
#         logger.info("�� 收到中断信号，正在关闭系统...")
#     except Exception as e:
#         logger.critical(f"�� 应用启动失败: {str(e)}")
#         raise
#     finally:
#         logger.info("👋 OnCall系统已关闭")


# # 测试代码
# test_data = '2025-09-16'
# send_bug_assignment_notification(test_data)

# test_data = '2025-09-16'
# send_combined_notification(test_data)