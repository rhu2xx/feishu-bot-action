"""
main.py
feishu-bot-action 主入口。

从环境变量读取 GitHub Actions inputs，分发到对应功能模块执行，
并将结果通过 GITHUB_OUTPUT 写回给后续 step。

支持的 action 值：
  send_message        → 推送消息到飞书群（webhook）
  append_bitable_row  → 向多维表格追加一行
  update_bitable_row  → 更新多维表格中的指定行
"""
from __future__ import annotations

import json
import os
import sys

# 将 src/ 加入路径，使子模块可以互相导入
sys.path.insert(0, os.path.dirname(__file__))

from bot.webhook import send_message
from bitable.bitable import append_row, update_row


# ─── 读取 inputs ─────────────────────────────────────────────────────────────

def get_input(name: str, required: bool = False) -> str:
    """读取 GitHub Actions input（对应环境变量 INPUT_<NAME>）。"""
    value = os.environ.get(f"INPUT_{name.upper().replace('-', '_')}", "").strip()
    if required and not value:
        print(f"::error::缺少必填参数: {name}")
        sys.exit(1)
    return value


def set_output(name: str, value: str) -> None:
    """将输出值写入 GITHUB_OUTPUT 文件（GitHub Actions 标准方式）。"""
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    else:
        # 本地调试时直接打印
        print(f"OUTPUT {name}={value}")


# ─── 主逻辑 ──────────────────────────────────────────────────────────────────

def run() -> None:
    action = get_input("action", required=True)

    print(f"[feishu-bot-action] 执行操作: {action}")

    if action == "send_message":
        _handle_send_message()

    elif action == "append_bitable_row":
        _handle_append_bitable_row()

    elif action == "update_bitable_row":
        _handle_update_bitable_row()

    else:
        print(f"::error::不支持的 action 值: {action}")
        print("可选值：send_message | append_bitable_row | update_bitable_row")
        sys.exit(1)


def _handle_send_message() -> None:
    webhook_url = get_input("webhook_url", required=True)
    msg_type    = get_input("msg_type") or "text"
    msg_content = get_input("msg_content", required=True)
    sign_key    = get_input("webhook_sign_key")

    print(f"[feishu-bot-action] 发送消息类型: {msg_type}")
    result = send_message(
        webhook_url=webhook_url,
        msg_type=msg_type,
        msg_content=msg_content,
        sign_key=sign_key,
    )
    set_output("response", json.dumps(result, ensure_ascii=False))
    print("[feishu-bot-action] 消息发送成功 ✓")


def _handle_append_bitable_row() -> None:
    app_id      = get_input("app_id",      required=True)
    app_secret  = get_input("app_secret",  required=True)
    app_token   = get_input("bitable_app_token", required=True)
    table_id    = get_input("bitable_table_id",  required=True)
    fields_raw  = get_input("bitable_fields",    required=True)

    try:
        fields = json.loads(fields_raw)
    except json.JSONDecodeError as e:
        print(f"::error::bitable_fields 不是合法的 JSON: {e}")
        sys.exit(1)

    print(f"[feishu-bot-action] 写入多维表格，字段: {list(fields.keys())}")
    record_id = append_row(
        app_id=app_id,
        app_secret=app_secret,
        app_token=app_token,
        table_id=table_id,
        fields=fields,
    )
    set_output("record_id", record_id)
    set_output("response", json.dumps({"record_id": record_id}, ensure_ascii=False))
    print(f"[feishu-bot-action] 新增行成功，record_id: {record_id} ✓")


def _handle_update_bitable_row() -> None:
    app_id      = get_input("app_id",      required=True)
    app_secret  = get_input("app_secret",  required=True)
    app_token   = get_input("bitable_app_token", required=True)
    table_id    = get_input("bitable_table_id",  required=True)
    record_id   = get_input("bitable_record_id", required=True)
    fields_raw  = get_input("bitable_fields",    required=True)

    try:
        fields = json.loads(fields_raw)
    except json.JSONDecodeError as e:
        print(f"::error::bitable_fields 不是合法的 JSON: {e}")
        sys.exit(1)

    print(f"[feishu-bot-action] 更新多维表格行 {record_id}，字段: {list(fields.keys())}")
    updated_id = update_row(
        app_id=app_id,
        app_secret=app_secret,
        app_token=app_token,
        table_id=table_id,
        record_id=record_id,
        fields=fields,
    )
    set_output("record_id", updated_id)
    set_output("response", json.dumps({"record_id": updated_id}, ensure_ascii=False))
    print(f"[feishu-bot-action] 更新行成功，record_id: {updated_id} ✓")


if __name__ == "__main__":
    run()
