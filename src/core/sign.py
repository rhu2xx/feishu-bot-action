"""
sign.py
飞书自定义机器人 Webhook HMAC-SHA256 签名
文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot#30e1e50e
"""
import hashlib
import hmac
import base64
import time


def gen_sign(sign_key: str, timestamp: int | None = None) -> tuple[int, str]:
    """
    生成飞书 webhook 请求体中需要的 timestamp 和 sign。

    Args:
        sign_key:  飞书机器人后台配置的签名密钥
        timestamp: Unix 时间戳（秒），不传则取当前时间

    Returns:
        (timestamp, signature) 需一并放入请求体
    """
    if timestamp is None:
        timestamp = int(time.time())

    # 签名串 = "{timestamp}\n{key}"
    string_to_sign = f"{timestamp}\n{sign_key}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    signature = base64.b64encode(hmac_code).decode("utf-8")
    return timestamp, signature
