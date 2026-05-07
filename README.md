# db-query v2.1

Oracle/MySQL 自然语言查询技能（纯 Python 实现）。

## 核心特性
- **功能**：自然语言转 SQL 查询，自动发现与缓存 Schema，直方/饼/折线图动态渲染并支持飞书原窗直发。
- **安全**：凭据明文存本地 `memory/connections.json` (0600权限)；强制只读 (仅支持 SELECT)；大表拒绝及自动 LIMIT 保护；无 sudo 字体安装。
- **环境要求**：Python 3.8+ (`oracledb>=2.0.0`, `mysql-connector-python>=8.0.0`, `matplotlib>=3.7.0`)。

## 快速安装
```bash
cd ~/.openclaw/skills-ins/db-query
python install.py --auto-pip
```

## 使用说明
本技能设计为由大语言模型（Agent）自动调用，支持多数据库连接环境。
初次使用或未配置连接时，请直接使用自然语言向 Agent 提供信息，例如：
> "帮我连接 Oracle 数据库，IP 是 10.0.0.1，端口 1521，服务名 orcl，账号 admin，密码 xxx，别名记为『生产库』"

Agent 接收到指令后，会自动解析并持久化保存至 `memory/connections.json` 文件中。配置完成后，您即可直接提问：
> "查询一下生产库里的员工表，按部门统计一下平均工资，并帮我画个柱状图"

## 变更历史
| 版本 | 说明 |
|------|------|
| v2.1 | **架构调整**：取消基于环境变量的凭据存储机制，全面转向本地隔离的 Local File Credential (`memory/connections.json`) 模式并自动锁定 0600 权限。 |
| v2.0 | **重大升级**：全面移除 Java/JDBC 依赖，转为纯 Python thin driver 实现；大幅压缩文档 Token 消耗。 |
| v1.2 | 改用 Python thin driver 测试版，新增飞书原窗图片直发。 |
| v1.1 | 安全升级：移除所有系统级的 `sudo apt-get` 依赖安装，改为双轨静默字库。 |
| v1.0 | 初始版本发布。 |
