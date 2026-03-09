"""
auth.py
飞书应用鉴权：获取 tenant_access_token（内建应用模式）
文档：https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
"""
import time
import requests

# 简单内存缓存，避免频繁刷新 token（有效期约 2 小时）
_cache: dict = {
    "token": "",
    "expire_at": 0,
}

FEISHU_BASE_URL = "https://open.feishu.cn"


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """
    获取 tenant_access_token，带内存缓存（提前 5 分钟刷新）。

    Args:
        app_id:     飞书应用的 App ID
        app_secret: 飞书应用的 App Secret

    Returns:
        有效的 tenant_access_token 字符串
    """
    now = int(time.time())
    if _cache["token"] and now < _cache["expire_at"] - 300:
        return _cache["token"]

    url = f"{FEISHU_BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"获取 tenant_access_token 失败: {data}")

    _cache["token"] = data["tenant_access_token"]
    _cache["expire_at"] = now + data.get("expire", 7200)
    return _cache["token"]
