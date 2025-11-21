# # 钉钉企业机器人配置
# DINGTALK_APP_KEY = "dingeekmytdfqs3qy8sn"  # 替换为您的实际APP_KEY
# DINGTALK_APP_SECRET = "Ni8v5yLLKAAVArgFpoKSrjTXlY15ED2FYniqcTZhiTSGE4uBA4E99CNJMZi_H9Nk"  # 替换为您的实际APP_SECRET

# 钉钉企业机器人配置(本地环境)
DINGTALK_APP_KEY = "dingeekmytdfqs3qy8sn"  # 替换为您的实际APP_KEY
DINGTALK_APP_SECRET = "Ni8v5yLLKAAVArgFpoKSrjTXlY15ED2FYniqcTZhiTSGE4uBA4E99CNJMZi_H9Nk"  # 替换为您的实际APP_SECRET

# 钉钉API配置
DINGTALK_GET_TOKEN_URL = "https://oapi.dingtalk.com/gettoken"
DINGTALK_SEND_MESSAGE_URL = "https://oapi.dingtalk.com/chat/send"

# 钉钉自定义机器人配置（测试小群）
DINGTALK_ROBOT_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=a09c321dd246a4228483b2c58cd08bde3cf6f18edea7ab51362f6a75600f37ef"
# 钉钉自定义机器人配置（新测试群）
# DINGTALK_ROBOT_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=d1806cbc1785407d474a388815863f5e3b471aa5539295cc5ffd24d918ba7109"

# 钉钉机器人配置
DINGTALK_BOT_NAME = "OnCall机器人"  # 机器人名称
DINGTALK_WEBHOOK_URL = "http://39.174.95.42:5008/api/dingtalk/webhook"  # 需要替换为您的服务器地址

# Flask配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 6000
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

ORIGINAL_DUTY_EXCEL = './data/值班计划表.xlsx'

# 日志配置
LOG_CONFIG = {
    # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'level': 'INFO',

    # 日志格式
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',

    # 日志文件配置
    'log_dir': './logs',
    'log_file': 'oncall.log',
    'error_log_file': 'oncall_error.log',

    # 文件轮转配置
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,  # 保留5个备份文件

    # 控制台输出
    'console_output': True,
    'console_level': 'INFO',

    # 是否记录到文件
    'file_output': True,
    'file_level': 'DEBUG',
}




