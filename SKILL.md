---
name: db-query
version: 2.1.0
description: Query Oracle and MySQL databases via Python thin drivers using natural language. Supports chart generation and Feishu integration.
---

# db-query (v2.1)

**READ-ONLY 数据库查询技能**。纯 Python 实现，凭据本地安全隔离。

## 🧠 Agent 交互与查询意图处理守则 (核心指令)
作为 OpenClaw 服务大模型，你在承接用户查询意图时，**必须严格遵守**：
1. **零连接强制询问**：查询前必须调用 `connection_manager.list_connections()`。若返回空，立刻停止解析并回复要求用户提供完整连接信息 (数据库类型、IP、端口、库名、账号、密码)。待用户提供后，调用 `add_connection` 录入。
2. **多库会话锁定**：若存在**超过 1 个**库别名且用户未明确指定，必须立刻停下，列出所有库别名让用户选择。选定后，在该连续会话周期内，所有查询**必须**显式调用 `db_query.query(..., alias="用户选择的别名")` 锁死上下文。

## API 速查

### 1. 连接管理 & Schema 缓存
连接明文自动保存至 `memory/connections.json` (0600权限)。
```python
from connection_manager import add_connection, get_active
# 录入并自动设置为活跃连接
add_connection(alias="生产库", db_type="oracle", user="u", password="p", host="10.0.0.1", port=1521, database="orcl")

from schema_discovery import discover_oracle, discover_mysql
# 发现表结构并写入 memory/schema_<alias>.md，避免重复扫描
discover_oracle(get_active())
```

### 2. 执行查询
```python
from db_query import query
# 底层强拦截：无 WHERE 且超 10 万行的大表拒绝；默认追加 FETCH FIRST 100 ROWS。
rows = query("SELECT ...", alias="生产库")
```

### 3. 图表渲染与推送
优先产出 Markdown 图片，若在飞书通道支持 Open API 直发：
```python
from chart_utils import render_bar_chart
# 生成图表
chart_path = render_bar_chart(labels=["A", "B"], values=[10, 20], title="分布")

# 标准回显：Agent 应组装 Markdown 返回：![图表](/绝对路径/chart_path.png)

# 飞书直发 (需要时)：
from feishu_uploader import FeishuUploader
FeishuUploader().upload_and_send(chart_path, "om_xxxxxx", is_message_id=True)
```
