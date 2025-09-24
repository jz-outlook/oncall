from flask import Blueprint, request, jsonify, send_file, abort
from src.services.excel_handler import get_original_duty_person, get_bug_assignment_person, get_today_date
from src.utils.logger import get_logger
import json
import os
from datetime import datetime

# 获取日志器
logger = get_logger('api')

# 创建蓝图
api = Blueprint('api', __name__)


@api.route('/dingtalk/webhook', methods=['GET', 'POST'])
def dingtalk_webhook():
    """钉钉企业机器人Webhook接口，处理@机器人的消息"""

    # 记录请求信息
    client_ip = request.remote_addr
    logger.info(f"收到钉钉Webhook请求 - IP: {client_ip}, 方法: {request.method}")

    # 处理GET请求（钉钉连接测试）
    if request.method == 'GET':
        logger.info("钉钉连接测试请求")
        return jsonify({"status": "success", "message": "webhook连接正常"})

    # 处理POST请求（实际消息处理）
    try:
        data = request.json
        logger.info(f"收到钉钉消息数据: {json.dumps(data, ensure_ascii=False)}")

        # 检查消息类型
        msg_type = data.get('msgtype', '')
        logger.debug(f"消息类型: {msg_type}")

        if msg_type == 'text':
            # 获取消息内容
            text_content = data.get('text', {}).get('content', '').strip()
            logger.info(f"收到文本消息: {text_content}")

            # 检查是否包含关键词
            if '值班' in text_content or '今天谁值班' in text_content:
                logger.info("匹配到关键词，开始处理")
                # 获取今天的工作安排
                today = get_today_date()
                duty_person = get_original_duty_person(today)
                bug_person = get_bug_assignment_person(today)

                logger.info(f"查询结果 - 值班人: {duty_person or '未找到'}, 禅道指派: {bug_person or '未找到'}")

                # 构建回复内容
                reply_parts = [f"📅 {today} 工作安排："]

                if duty_person:
                    reply_parts.append(f"🔧 值班人：{duty_person}")
                else:
                    reply_parts.append("❌ 未找到值班人员")

                if bug_person:
                    reply_parts.append(f"🐛 禅道指派：{bug_person}")

                reply_content = "\n".join(reply_parts)
                logger.info(f"准备回复内容: {reply_content}")

                # 返回回复消息
                return jsonify({
                    "msgtype": "text",
                    "text": {"content": reply_content}
                })

        # 其他消息的默认回复
        logger.info("未匹配到关键词，返回默认回复")
        return jsonify({
            "msgtype": "text",
            "text": {"content": "您好！我是OnCall值班机器人🤖\n\n发送「值班」或「今天谁值班」可以查询今日工作安排"}
        })

    except Exception as e:
        logger.error(f"处理钉钉消息失败: {str(e)}")
        return jsonify({
            "msgtype": "text",
            "text": {"content": "处理消息时出现错误，请稍后重试"}
        })


@api.route('/download_duty_schedule', methods=['GET'])
def download_duty_schedule():
    """下载值班计划表Excel文件"""
    logger.info("收到下载值班计划表请求")

    try:
        # 值班计划表文件路径
        excel_file_path = './data/值班计划表.xlsx'

        # 检查文件是否存在
        if not os.path.exists(excel_file_path):
            logger.error(f"值班计划表文件不存在: {excel_file_path}")
            return jsonify({
                "status": "error",
                "message": "值班计划表文件不存在"
            }), 404

        # 生成下载文件名（包含当前日期）
        current_date = datetime.now().strftime("%Y%m%d")
        download_filename = f"值班计划表_{current_date}.xlsx"

        logger.info(f"准备下载文件: {excel_file_path} -> {download_filename}")

        # 使用send_file发送文件，设置正确的MIME类型和下载文件名
        return send_file(
            excel_file_path,
            as_attachment=True,  # 强制下载
            download_name=download_filename,  # 下载时的文件名
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # Excel文件MIME类型
        )

    except Exception as e:
        logger.error(f"下载值班计划表失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"下载文件失败: {str(e)}"
        }), 500


@api.route('/update_duty_replace', methods=['POST'])
def update_duty_replace():
    """更新值班替换记录的接口"""
    logger.info("收到更新值班替换记录请求")

    data = request.json
    logger.info(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

    # 校验必填参数
    required_fields = ["date", "replace_person"]
    if not all(field in data for field in required_fields):
        logger.warning("参数校验失败：缺少必填参数")
        return jsonify({"status": "error", "message": "缺少必填参数（date/replace_person）"}), 400

    # 获取原值班人
    original_person = get_original_duty_person(data["date"])
    if not original_person:
        logger.warning(f"未找到{data['date']}的原始值班记录")
        return jsonify({"status": "error", "message": f"未找到{data['date']}的原始值班记录"}), 404


@api.route('/get_bug_assignment', methods=['GET'])
def get_bug_assignment():
    """获取指定日期的禅道指派人员"""
    logger.info("收到获取禅道指派人员请求")

    date = request.args.get('date')
    logger.info(f"请求参数 - 日期: {date}")

    if not date:
        logger.warning("参数校验失败：缺少日期参数")
        return jsonify({"status": "error", "message": "缺少日期参数"}), 400

    bug_person = get_bug_assignment_person(date)
    if bug_person:
        logger.info(f"找到禅道指派人员: {bug_person}")
        return jsonify({
            "status": "success",
            "data": {
                "date": date,
                "bug_assignment_person": bug_person
            }
        })
    else:
        logger.warning(f"未找到{date}的禅道指派人员")
        return jsonify({"status": "error", "message": f"未找到{date}的禅道指派人员"}), 404


@api.route('/get_daily_work', methods=['GET'])
def get_daily_work():
    """获取指定日期的完整工作安排（值班+禅道指派）"""
    logger.info("收到获取每日工作安排请求")

    date = request.args.get('date')
    logger.info(f"请求参数 - 日期: {date}")

    if not date:
        logger.warning("参数校验失败：缺少日期参数")
        return jsonify({"status": "error", "message": "缺少日期参数"}), 400

    duty_person = get_original_duty_person(date)
    bug_person = get_bug_assignment_person(date)

    logger.info(f"查询结果 - 值班人: {duty_person or '未找到'}, 禅道指派: {bug_person or '未找到'}")

    result = {
        "status": "success",
        "data": {
            "date": date,
            "duty_person": duty_person,
            "bug_assignment_person": bug_person
        }
    }

    return jsonify(result)