# 钉钉配置
# DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=7bc8eb87427a8f930652d536c7036fb2853f243e806b469f576e7485b1307406"
# DINGTALK_SECRET = "SECb543e65306f7de90f92589c852bbc2c7d521b9e56f01e69a219b485e08eb9bbe"

# 测试对接群配置
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=cc83f6f282335c930625d8956ed339a88d83c6bc2b49d068668feea9fd8b79bf"
DINGTALK_SECRET = "SECf47d74d3c6df68c257b38436dd0a5ebd9ec3e85458c278a154cb1e48d6019cb3"


# Flask配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5008
FLASK_DEBUG = False


# 值班人员列表
duty_persons = [
    {"id": 1, "name": "武恒"},
    {"id": 2, "name": "马刘磊"},
    {"id": 3, "name": "代瑞林"},
    {"id": 4, "name": "魏来"},
    {"id": 5, "name": "王朝霞"},
    {"id": 6, "name": "毕恩宇"},
    {"id": 7, "name": "魏以铭"},
    {"id": 8, "name": "张笑笑"},
    {"id": 9, "name": "何立强"}
]


# 禅道指派
bug_persons = [
    {"id": 1, "name": "张笑笑"},
    {"id": 2, "name": "马刘磊"}
]


ORIGINAL_DUTY_EXCEL = '值班计划表.xlsx'
