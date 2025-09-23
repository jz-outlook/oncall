
from flask import Flask
from routes import api
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from dingtalk import send_dingtalk_message
from excel_handler import get_original_duty_person, get_today_date, get_bug_assignment_person
import schedule
import time
from threading import Thread
import threading
import os
import time

# 全局变量，确保定时任务只启动一次
_scheduler_started = False
_scheduler_lock = threading.Lock()
_process_id = os.getpid()  # 获取当前进程ID


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.register_blueprint(api, url_prefix='/api')
    return app


def send_bug_assignment_notification(test_data=None):
    """发送每日禅道指派人员通知"""
    today = get_today_date()
    bug_person = get_bug_assignment_person(today)
    if bug_person:
        content = f"【今日禅道指派】\n日期：{today}\n指派人员：{bug_person}"
        # 发送钉钉通知
        send_dingtalk_message(content)
        print(f"已发送{today}禅道指派通知")
    else:
        print(f"未找到{today}的禅道指派人员")


def send_daily_notification(test_data=None):
    """发送每日值班通知"""
    print(f"[进程{os.getpid()}] 开始发送值班通知 - {time.strftime('%Y-%m-%d %H:%M:%S')}")

    today = get_today_date()
    oncall_person = get_original_duty_person(today)
    if oncall_person:
        content = f"【今日值班通知】\n日期：{today}\n值班人：{oncall_person}"
        # 发送钉钉通知
        send_dingtalk_message(content)
        print(f"[进程{os.getpid()}] 已发送{today}值班通知")
    else:
        print(f"[进程{os.getpid()}] 未找到{today}的值班人员")


def send_combined_notification(test_data=None):
    """发送综合通知（值班+禅道指派）"""
    print(f"[进程{os.getpid()}] 开始发送综合通知 - {time.strftime('%Y-%m-%d %H:%M:%S')}")

    today = get_today_date()
    oncall_person = get_original_duty_person(today)
    bug_person = get_bug_assignment_person(today)

    content_parts = [f"【OnCall】\n日期：{today}"]

    if oncall_person:
        content_parts.append(f"值班人：{oncall_person}")

    if bug_person:
        content_parts.append(f"禅道指派：{bug_person}")

    if len(content_parts) > 1:  # 除了标题还有其他内容
        content = "\n".join(content_parts)
        send_dingtalk_message(content)
        print(f"[进程{os.getpid()}] 已发送{today}综合工作安排通知")
    else:
        print(f"[进程{os.getpid()}] 未找到{today}的工作安排信息")


def run_scheduler():
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            print(f"[进程{os.getpid()}] 定时任务已启动，跳过重复启动")
            return
        _scheduler_started = True
        print(f"[进程{os.getpid()}] 启动定时任务调度器")

    # 清除所有现有的定时任务
    schedule.clear()
    print(f"[进程{os.getpid()}] 已清除所有现有定时任务")

    # 分别设置不同的时间发送不同类型的通知
    schedule.every().day.at("08:30").do(send_bug_assignment_notification)

    schedule.every().day.at("17:20").do(send_combined_notification)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    app = create_app()

    # 启动定时任务线程
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # 启动Flask应用
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

# # 测试代码
# test_data = '2025-09-20'
# send_bug_assignment_notification(test_data)
#
#
# test_data = '2026-01-22'
# send_combined_notification(test_data)
