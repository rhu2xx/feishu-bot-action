"""
webhook.py
向飞书群机器人 Webhook 发送消息。

支持消息类型：
  - text        纯文本
  - interactive 卡片（可使用模板或简单卡片）
  - post        富文本

文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
"""
from __future__ import annotations

import json

from core.sign import gen_sign
from core.http_client import webhook_post
from bot.card_builder import build_text_message, build_simple_card, build_template_card


def send_message(
    webhook_url: str,
    msg_type: str,
    msg_content: str,
    sign_key: str = "",
) -> dict:
    """
    发送消息到飞书群机器人。

    Args:
        webhook_url: 飞书机器人 webhook 完整 URL
        msg_type:    text | interactive | post
        msg_content: 消息内容
            - text:        纯文本字符串
            - interactive: JSON 字符串，支持以下两种格式
                a) 完整 card 结构（含 msg_type）→ 直接发送
                b) {"title": "...", "content": "..."}  → 自动构造 simple card
                c) {"template_id": "...", "template_variable": {...}} → 模板卡片
            - post:        飞书富文本 JSON 字符串
        sign_key:    签名密钥（不填则不签名）

    Returns:
        飞书 webhook 返回的响应 JSON
    """
    payload = _build_payload(msg_type, msg_content)

    # 如果配置了签名密钥，注入 timestamp + sign
    if sign_key:
        timestamp, sign = gen_sign(sign_key)
        payload["timestamp"] = str(timestamp)
        payload["sign"] = sign

    return webhook_post(webhook_url, payload)


# ─── 内部辅助 ────────────────────────────────────────────────────────────────

def _build_payload(msg_type: str, msg_content: str) -> dict:
    """根据 msg_type 和 msg_content 构造请求体。"""
    if msg_type == "text":
        return build_text_message(msg_content)

    if msg_type == "interactive":
        return _build_interactive_payload(msg_content)

    if msg_type == "post":
        # msg_content 应为符合飞书富文本格式的 JSON 字符串
        data = json.loads(msg_content)
        return {
            "msg_type": "post",
            "content": {"post": data},
        }

    raise ValueError(f"不支持的 msg_type: {msg_type}，可选值为 text | interactive | post")


def _build_interactive_payload(msg_content: str) -> dict:
    """
    解析 interactive 消息内容，支持三种输入格式：

    格式 A - 完整 card 结构（含 msg_type 字段）：
        {"msg_type": "interactive", "card": {...}}

    格式 B - 简单 title + content：
        {"title": "标题", "content": "正文", "color": "blue"}

    格式 C - 模板卡片：
        {"template_id": "AAqke...", "template_variable": {...}, "template_version": "1.0.0"}
    """
    try:
        data = json.loads(msg_content)
    except json.JSONDecodeError:
        # 纯文本降级为 simple card
        return build_simple_card(title="消息通知", content=msg_content)

    # 格式 A：已是完整 card 结构
    if "msg_type" in data and "card" in data:
        return data

    # 格式 C：模板卡片
    if "template_id" in data:
        return build_template_card(
            template_id=data["template_id"],
            template_variable=data.get("template_variable", {}),
            template_version=data.get("template_version", "1.0.0"),
        )

    # 格式 B：简单 title + content
    return build_simple_card(
        title=data.get("title", "消息通知"),
        content=data.get("content", str(data)),
        color=data.get("color", "blue"),
    )
