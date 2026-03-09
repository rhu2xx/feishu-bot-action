"""
http_client.py
统一 HTTP 封装：
  - webhook_post : 发到飞书机器人 webhook（无需鉴权，可带签名）
  - api_post     : 调用飞书开放平台 API（需 tenant_access_token）
  - api_patch    : 调用飞书开放平台 API（PATCH 方法，用于更新）
"""
import json
import requests

FEISHU_BASE_URL = "https://open.feishu.cn"


def webhook_post(webhook_url: str, payload: dict) -> dict:
    """
    向飞书机器人 webhook 发送 POST 请求。

    Args:
        webhook_url: 完整的 webhook URL
        payload:     请求体字典（会被序列化为 JSON）

    Returns:
        飞书返回的响应 JSON
    """
    resp = requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") not in (0, None) and result.get("StatusCode") not in (0, None):
        raise RuntimeError(f"飞书 webhook 返回错误: {result}")
    return result


def api_post(path: str, token: str, payload: dict) -> dict:
    """
    调用飞书开放平台 POST 接口。

    Args:
        path:    API 路径，例如 /open-apis/bitable/v1/apps/{token}/tables/{id}/records
        token:   tenant_access_token
        payload: 请求体字典

    Returns:
        飞书返回的响应 JSON
    """
    url = f"{FEISHU_BASE_URL}{path}"
    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") != 0:
        raise RuntimeError(f"飞书 API 返回错误: {result}")
    return result


def api_patch(path: str, token: str, payload: dict) -> dict:
    """
    调用飞书开放平台 PATCH 接口（用于更新多维表格行）。

    Args:
        path:    API 路径
        token:   tenant_access_token
        payload: 请求体字典

    Returns:
        飞书返回的响应 JSON
    """
    url = f"{FEISHU_BASE_URL}{path}"
    resp = requests.patch(
        url,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") != 0:
        raise RuntimeError(f"飞书 API 返回错误: {result}")
    return result
