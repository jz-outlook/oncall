# from flask import Blueprint, request, jsonify
# from excel_handler import get_original_duty_person
#
# # 创建蓝图
# api = Blueprint('api', __name__)
#
#
# @api.route('/update_duty_replace', methods=['POST'])
# def update_duty_replace():
#     """更新值班替换记录的接口"""
#     data = request.json
#     # 校验必填参数
#     required_fields = ["date", "replace_person"]
#     if not all(field in data for field in required_fields):
#         return jsonify({"status": "error", "message": "缺少必填参数（date/replace_person）"}), 400
#
#     # 获取原值班人
#     original_person = get_original_duty_person(data["date"])
#     if not original_person:
#         return jsonify({"status": "error", "message": f"未找到{data['date']}的原始值班记录"}), 404




# --------


from flask import Blueprint, request, jsonify
from excel_handler import get_original_duty_person, get_bug_assignment_person

# 创建蓝图
api = Blueprint('api', __name__)


@api.route('/update_duty_replace', methods=['POST'])
def update_duty_replace():
    """更新值班替换记录的接口"""
    data = request.json
    # 校验必填参数
    required_fields = ["date", "replace_person"]
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "缺少必填参数（date/replace_person）"}), 400

    # 获取原值班人
    original_person = get_original_duty_person(data["date"])
    if not original_person:
        return jsonify({"status": "error", "message": f"未找到{data['date']}的原始值班记录"}), 404


@api.route('/get_bug_assignment', methods=['GET'])
def get_bug_assignment():
    """获取指定日期的禅道指派人员"""
    date = request.args.get('date')
    if not date:
        return jsonify({"status": "error", "message": "缺少日期参数"}), 400

    bug_person = get_bug_assignment_person(date)
    if bug_person:
        return jsonify({
            "status": "success",
            "data": {
                "date": date,
                "bug_assignment_person": bug_person
            }
        })
    else:
        return jsonify({"status": "error", "message": f"未找到{date}的禅道指派人员"}), 404


@api.route('/get_daily_work', methods=['GET'])
def get_daily_work():
    """获取指定日期的完整工作安排（值班+禅道指派）"""
    date = request.args.get('date')
    if not date:
        return jsonify({"status": "error", "message": "缺少日期参数"}), 400

    duty_person = get_original_duty_person(date)
    bug_person = get_bug_assignment_person(date)

    result = {
        "status": "success",
        "data": {
            "date": date,
            "duty_person": duty_person,
            "bug_assignment_person": bug_person
        }
    }

    return jsonify(result)