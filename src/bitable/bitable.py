"""
bitable.py
飞书多维表格操作：新增行、更新行、初始化表字段。

文档：
  新增行    - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create
  更新行    - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/update
  字段列表  - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/list
  更新字段  - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/update
  新增字段  - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/create
  查询记录  - https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/search
"""
from __future__ import annotations

from core.auth import get_tenant_access_token
from core.http_client import api_post, api_patch, api_get, api_put


def _get_fields(token: str, app_token: str, table_id: str) -> list[dict]:
    """获取表格当前所有字段定义列表。"""
    path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    result = api_get(path, token)
    return result["data"]["items"]


def _get_record_count(token: str, app_token: str, table_id: str) -> int:
    """获取表格当前数据行数（最多取 1 条，只判断是否为空）。"""
    path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    result = api_get(path, token, params={"page_size": 1})
    return result["data"].get("total", 0)


def _check_blank_table(token: str, app_token: str, table_id: str, existing_fields: list[dict]) -> None:
    """
    严格检查是否为空白初始表，不满足则抛出 RuntimeError。

    空白表的判断标准（同时满足）：
      1. 只有 1 个字段
      2. 没有任何数据行

    这确保用户传入的是一张全新的、未被使用过的表格。
    """
    if len(existing_fields) != 1:
        raise RuntimeError(
            f"Not an empty table — 表格已有 {len(existing_fields)} 个字段 "
            f"({[f['field_name'] for f in existing_fields]})，"
            "请提供一张空白的初始多维表格。"
        )
    record_count = _get_record_count(token, app_token, table_id)
    if record_count > 0:
        raise RuntimeError(
            f"Not an empty table — 表格已有 {record_count} 行数据，"
            "请提供一张空白的初始多维表格。"
        )


def _is_initial_table(existing: list[dict]) -> bool:
    """
    判断是否为"可初始化"状态：只有 1 列时视为初始化阶段，允许覆盖。
    """
    return len(existing) == 1


def init_table_fields(
    token: str,
    app_token: str,
    table_id: str,
    desired_fields: list[str],
) -> None:
    """
    检查表格是否为初始空表，若是则自动覆盖字段名。
    若表格已有自定义字段，则抛出 RuntimeError('Not an empty table')。

    判断"初始表"的标准：
      - 只有 1 个字段，且字段类型为文本（field_type=1）

    覆盖策略：
      - 将第一列重命名为 desired_fields[0]
      - 其余 desired_fields[1:] 逐一新增为文本列

    Args:
        token:          tenant_access_token
        app_token:      多维表格 app_token
        table_id:       表格 table_id
        desired_fields: 期望的字段名列表，例如 ["职位", "公司", "薪资", "日期"]
    """
    existing = _get_fields(token, app_token, table_id)

    # 判断是否为初始空表（只有默认的'文本'列）
    if not _is_initial_table(existing):
        raise RuntimeError("Not an empty table")

    # 重命名第一列
    first_field_id = existing[0]["field_id"]
    path_update = (
        f"/open-apis/bitable/v1/apps/{app_token}"
        f"/tables/{table_id}/fields/{first_field_id}"
    )
    api_put(path_update, token, {
        "field_name": desired_fields[0],
        "type": existing[0].get("type", 1),
    })
    print(f"[feishu-bot-action] 字段初始化：重命名第一列为 '{desired_fields[0]}'")

    # 新增其余列
    path_create = (
        f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    )
    for name in desired_fields[1:]:
        api_post(path_create, token, {
            "field_name": name,
            "type": 1,  # 1 = 多行文本（飞书默认文本类型）
        })
        print(f"[feishu-bot-action] 字段初始化：新增列 '{name}'")


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

    # 检查表字段：
    #   - 初始空表（1列+0行） → 自动初始化列名后写入
    #   - 已初始化的表（列名匹配） → 直接写入
    #   - 非空表 / 列名不匹配 → 报错提示用户
    existing = _get_fields(token, app_token, table_id)
    if _is_initial_table(existing):
        # 严格验证：必须同时满足"1列+0行"才允许初始化
        _check_blank_table(token, app_token, table_id, existing)
        init_table_fields(token, app_token, table_id, list(fields.keys()))
    else:
        # 已有多列：验证字段名是否匹配
        existing_names = {f["field_name"] for f in existing}
        unknown = [k for k in fields if k not in existing_names]
        if unknown:
            raise RuntimeError(
                f"Not an empty table — 字段 {unknown} 在表格中不存在，"
                f"现有字段：{sorted(existing_names)}"
            )

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
