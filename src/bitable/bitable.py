"""
bitable.py
飞书多维表格操作：新增行、更新行。

文档：
  新增行 - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create
  更新行 - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/update
"""
from __future__ import annotations

from core.auth import get_tenant_access_token
from core.http_client import api_post, api_patch


def append_row(
    app_id: str,
    app_secret: str,
    app_token: str,
    table_id: str,
    fields: dict,
) -> str:
    """
    向多维表格追加一行记录。

    Args:
        app_id:     飞书应用 App ID
        app_secret: 飞书应用 App Secret
        app_token:  多维表格的 app_token（在多维表格 URL 中获取）
        table_id:   多维表格中具体表的 table_id
        fields:     要写入的字段字典，key 为列名，value 为写入值
                    例：{"职位": "前端工程师", "公司": "字节跳动", "薪资": "30k"}

    Returns:
        新增行的 record_id（可传给后续 step 用于更新）

    Example:
        record_id = append_row(
            app_id="cli_xxx",
            app_secret="xxx",
            app_token="bascnxxxxxxxx",
            table_id="tblxxxxxxxx",
            fields={"职位": "前端工程师", "公司": "字节跳动"},
        )
    """
    token = get_tenant_access_token(app_id, app_secret)
    path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    result = api_post(path, token, {"fields": fields})
    record_id: str = result["data"]["record"]["record_id"]
    return record_id


def update_row(
    app_id: str,
    app_secret: str,
    app_token: str,
    table_id: str,
    record_id: str,
    fields: dict,
) -> str:
    """
    更新多维表格中已有的一行记录。

    Args:
        app_id:     飞书应用 App ID
        app_secret: 飞书应用 App Secret
        app_token:  多维表格的 app_token
        table_id:   多维表格中具体表的 table_id
        record_id:  要更新的行的 record_id
        fields:     要更新的字段字典（只传需要修改的列即可）

    Returns:
        更新后的 record_id

    Example:
        update_row(
            app_id="cli_xxx",
            app_secret="xxx",
            app_token="bascnxxxxxxxx",
            table_id="tblxxxxxxxx",
            record_id="recxxxxxxxx",
            fields={"状态": "已投递"},
        )
    """
    token = get_tenant_access_token(app_id, app_secret)
    path = (
        f"/open-apis/bitable/v1/apps/{app_token}"
        f"/tables/{table_id}/records/{record_id}"
    )
    result = api_patch(path, token, {"fields": fields})
    return result["data"]["record"]["record_id"]
