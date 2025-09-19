import requests
import time
import hmac
import hashlib
import base64
from urllib.parse import quote
from config import DINGTALK_WEBHOOK, DINGTALK_SECRET


def get_dingtalk_signature():
    """生成钉钉加签签名（如果设置了密钥）"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = DINGTALK_SECRET.encode('utf-8')
    string_to_sign = f"{timestamp}\n{DINGTALK_SECRET}"
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = quote(base64.b64encode(hmac_code))
    return timestamp, sign


def send_dingtalk_message(content, at_all=True):
    """发送文本消息到钉钉"""
    # 构建请求URL（带签名）
    if DINGTALK_SECRET:
        timestamp, sign = get_dingtalk_signature()
        url = f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}"
    else:
        url = DINGTALK_WEBHOOK

    # 发送请求
    headers = {"Content-Type": "application/json;charset=utf-8"}
    data = {
        "msgtype": "text",
        "text": {"content": content + '\n'},
        "at": {
            "isAtAll": at_all  # 控制是否@所有人
        }
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()