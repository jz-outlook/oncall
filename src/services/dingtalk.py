import requests
import time
import json
import hmac
import hashlib
import base64
import urllib.parse
from config.settings import DINGTALK_ROBOT_WEBHOOK


def send_dingtalk_message(content, webhook_url=None, at_all=True, secret=None):
    """发送文本消息到钉钉群（使用自定义机器人方式）"""

    # 使用配置中的Webhook URL
    if not webhook_url:
        webhook_url = DINGTALK_ROBOT_WEBHOOK

    # 构建消息数据
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    # 如果需要@所有人
    if at_all:
        data["at"] = {
            "isAtAll": True
        }

    headers = {"Content-Type": "application/json;charset=utf-8"}

    # 如果配置了签名密钥，需要添加签名
    if secret:
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        # 在URL中添加签名参数
        if '?' in webhook_url:
            webhook_url += f'&timestamp={timestamp}&sign={sign}'
        else:
            webhook_url += f'?timestamp={timestamp}&sign={sign}'

    try:
        response = requests.post(webhook_url, json=data, headers=headers)
        result = response.json()
        print(f"发送消息结果: {result}")
        return result
    except Exception as e:
        print(f"发送消息异常: {str(e)}")
        return {"errcode": -1, "errmsg": str(e)}


# 保留原有的企业应用API方式作为备用
def send_dingtalk_message_enterprise(content, chat_id=None, at_all=True):
    """发送文本消息到钉钉群（企业应用API方式）"""
    from config.settings import DINGTALK_APP_KEY, DINGTALK_APP_SECRET, DINGTALK_GET_TOKEN_URL, DINGTALK_SEND_MESSAGE_URL

    # 全局变量存储访问令牌
    global _access_token, _token_expire_time
    _access_token = None
    _token_expire_time = 0

    def get_access_token():
        """获取钉钉访问令牌"""
        global _access_token, _token_expire_time

        # 如果令牌还有效，直接返回
        if _access_token and time.time() < _token_expire_time:
            return _access_token

        # 获取新的访问令牌
        url = DINGTALK_GET_TOKEN_URL
        params = {
            'appkey': DINGTALK_APP_KEY,
            'appsecret': DINGTALK_APP_SECRET
        }

        try:
            response = requests.get(url, params=params)
            result = response.json()

            if result.get('errcode') == 0:
                _access_token = result.get('access_token')
                # 设置令牌过期时间（提前5分钟刷新）
                _token_expire_time = time.time() + result.get('expires_in', 7200) - 300
                print(f"获取访问令牌成功: {_access_token}")
                return _access_token
            else:
                print(f"获取访问令牌失败: {result}")
                return None
        except Exception as e:
            print(f"获取访问令牌异常: {str(e)}")
            return None

    access_token = get_access_token()
    if not access_token:
        print("无法获取访问令牌")
        return {"errcode": -1, "errmsg": "无法获取访问令牌"}

    # 构建请求URL
    url = f"{DINGTALK_SEND_MESSAGE_URL}?access_token={access_token}"

    # 构建消息数据
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    # 如果需要@所有人
    if at_all:
        data["at"] = {
            "isAtAll": True
        }

    # 如果有指定的群ID
    if chat_id:
        data["chatid"] = chat_id

    headers = {"Content-Type": "application/json;charset=utf-8"}

    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        print(f"发送消息结果: {result}")
        return result
    except Exception as e:
        print(f"发送消息异常: {str(e)}")
        return {"errcode": -1, "errmsg": str(e)}