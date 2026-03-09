"""
card_builder.py
构造飞书消息卡片（interactive 类型）。

支持两种模式：
  1. 模板卡片：传入 template_id + template_variable（推荐，需提前在飞书卡片搭建器创建）
  2. 简单文本卡片：只传文本内容，自动生成 markdown 卡片（无需提前建模板）

文档：https://open.feishu.cn/document/common-capabilities/message-card/message-cards-content/card-structure/card-content
"""
from __future__ import annotations


def build_template_card(
    template_id: str,
    template_variable: dict,
    template_version: str = "1.0.0",
) -> dict:
    """
    基于飞书卡片模板构造 interactive 消息体。

    Args:
        template_id:       飞书卡片搭建器中的模板 ID
        template_variable: 模板变量字典，key/value 与模板中定义的变量对应
        template_version:  模板版本号

    Returns:
        完整的飞书消息体字典（可直接传给 webhook_post）

    Example:
        card = build_template_card(
            template_id="AAqkeNyiypMLb",
            template_variable={"title": "岗位播报", "content": "今日 10 个新岗位"},
        )
    """
    return {
        "msg_type": "interactive",
        "card": {
            "type": "template",
            "data": {
                "template_id": template_id,
                "template_version_name": template_version,
                "template_variable": template_variable,
            },
        },
    }


def build_simple_card(title: str, content: str, color: str = "blue") -> dict:
    """
    构造一个无需模板的简单文本卡片（markdown 格式）。

    Args:
        title:   卡片标题
        content: 卡片正文（支持 markdown，换行用 \\n）
        color:   标题颜色标签，可选 blue | green | red | yellow | grey | purple

    Returns:
        完整的飞书消息体字典

    Example:
        card = build_simple_card(
            title="🔍 今日岗位搜索结果",
            content="**前端工程师** - 字节跳动 - 30k\\n**后端工程师** - 腾讯 - 35k",
        )
    """
    return {
        "msg_type": "interactive",
        "card": {
            "schema": "2.0",
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "body": {
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content,
                    }
                ]
            },
        },
    }


def build_text_message(text: str) -> dict:
    """
    构造纯文本消息体。

    Args:
        text: 消息文本

    Returns:
        完整的飞书消息体字典
    """
    return {
        "msg_type": "text",
        "content": {"text": text},
    }
