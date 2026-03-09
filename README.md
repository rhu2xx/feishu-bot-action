# feishu-bot-action

插拔式飞书机器人 GitHub Action，用 Python 实现，可被任意业务项目 `uses:` 复用。

## 功能

| 操作 | 说明 |
|------|------|
| `send_message` | 推送消息到飞书群（支持文本 / 卡片 / 富文本，可启用签名校验） |
| `append_bitable_row` | 向飞书多维表格追加一行，返回 `record_id` |
| `update_bitable_row` | 更新飞书多维表格中的指定行 |

## 项目结构

```
feishu-bot-action/
├── action.yml              # GitHub Action 定义
├── requirements.txt        # Python 依赖（仅 requests）
├── src/
│   ├── main.py             # 主入口，读取 inputs 分发操作
│   ├── core/
│   │   ├── sign.py         # HMAC-SHA256 签名
│   │   ├── auth.py         # tenant_access_token 获取与缓存
│   │   └── http_client.py  # 统一 HTTP 封装
│   ├── bot/
│   │   ├── webhook.py      # 群消息发送
│   │   └── card_builder.py # 卡片构造（模板卡片 / 简单卡片）
│   └── bitable/
│       └── bitable.py      # 多维表格新增 / 更新行
└── examples/
    └── job-notify.yml      # 完整示例：岗位搜索 + 飞书通知
```

## 快速开始

### 1. 配置 Secrets

在你的业务项目仓库 → **Settings → Secrets and variables → Actions** 中添加：

| Secret 名称 | 用途 |
|-------------|------|
| `FEISHU_WEBHOOK_URL` | 飞书群机器人 Webhook URL |
| `FEISHU_SIGN_KEY` | 签名密钥（未开启签名可不填） |
| `FEISHU_APP_ID` | 飞书应用 App ID（多维表格时必填） |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret（多维表格时必填） |
| `BITABLE_APP_TOKEN` | 多维表格 app_token |
| `BITABLE_TABLE_ID` | 多维表格 table_id |

### 2. 在 workflow 中使用

#### 发送文本消息

```yaml
- uses: your-name/feishu-bot-action@v1
  with:
    action: send_message
    webhook_url: ${{ secrets.FEISHU_WEBHOOK_URL }}
    msg_type: text
    msg_content: "构建成功 ✓"
```

#### 发送卡片消息（无需提前建模板）

```yaml
- uses: your-name/feishu-bot-action@v1
  with:
    action: send_message
    webhook_url:      ${{ secrets.FEISHU_WEBHOOK_URL }}
    webhook_sign_key: ${{ secrets.FEISHU_SIGN_KEY }}
    msg_type: interactive
    msg_content: |
      {
        "title": "🔍 每日岗位播报",
        "content": "今日共找到 **5** 个前端岗位\n- 字节跳动 前端工程师 30k\n- 腾讯 前端工程师 35k",
        "color": "blue"
      }
```

#### 向多维表格追加一行

```yaml
- name: 写入多维表格
  id: write_bitable
  uses: your-name/feishu-bot-action@v1
  with:
    action: append_bitable_row
    app_id:            ${{ secrets.FEISHU_APP_ID }}
    app_secret:        ${{ secrets.FEISHU_APP_SECRET }}
    bitable_app_token: ${{ secrets.BITABLE_APP_TOKEN }}
    bitable_table_id:  ${{ secrets.BITABLE_TABLE_ID }}
    bitable_fields:    '{"职位":"前端工程师","公司":"字节跳动","薪资":"30k"}'

# 后续 step 可用 ${{ steps.write_bitable.outputs.record_id }} 获取新行 ID
```

#### 更新多维表格中的行

```yaml
- uses: your-name/feishu-bot-action@v1
  with:
    action: update_bitable_row
    app_id:            ${{ secrets.FEISHU_APP_ID }}
    app_secret:        ${{ secrets.FEISHU_APP_SECRET }}
    bitable_app_token: ${{ secrets.BITABLE_APP_TOKEN }}
    bitable_table_id:  ${{ secrets.BITABLE_TABLE_ID }}
    bitable_record_id: ${{ steps.write_bitable.outputs.record_id }}
    bitable_fields:    '{"状态":"已投递"}'
```

## 完整示例

见 [`examples/job-notify.yml`](examples/job-notify.yml)，演示了定时岗位搜索 + 飞书群通知 + 多维表格存档的完整流程。

## 飞书配置说明

### 获取群机器人 Webhook

飞书群 → 群设置 → 机器人 → 添加机器人 → 自定义机器人 → 复制 Webhook 地址

### 获取多维表格 app_token 和 table_id

打开多维表格，URL 格式为：
```
https://xxx.feishu.cn/base/{app_token}?table={table_id}
```

### 创建飞书应用（多维表格写入需要）

1. 前往 [飞书开放平台](https://open.feishu.cn/) 创建自建应用
2. 获取 App ID 和 App Secret
3. 在「权限管理」中开启 `bitable:app` 相关权限
4. 在多维表格中将该应用添加为协作者（有编辑权限）
