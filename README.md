# db-query v1.2

Oracle/MySQL 数据库自然语言查询技能，基于 Python thin driver，**无需 Java/JDK/JDBC**。

## 特性

- **自然语言 → SQL**：用大白话查数据库
- **Oracle + MySQL**：双数据库支持
- **图表生成**：直方图、饼图、折线图自动渲染
- **Schema 缓存**：自动发现表结构，避免重复扫描
- **飞书直发**：图表生成后直接发送到飞书聊天窗口

## 文件结构

```
db-query-1.2/
  install.py             安装脚本（pip 安装依赖）
  requirements.txt       Python 依赖清单
  SKILL.md               技能文档（Agent 行为指南）
  SECURITY.md            安全设计说明
  scripts/
    db_query.py          查询入口（thin driver 实现）
    chart_utils.py       图表生成引擎
    connection_manager.py 连接管理
    schema_discovery.py  Schema 自动发现
    feishu_uploader.py   飞书图片直发工具
  memory/                Schema 缓存目录（自动生成）
```

## 快速安装

```bash
cd ~/.openclaw/skills-ins/db-query-1.2
python install.py --auto-pip
```

## 依赖

- Python 3.8+
- `oracledb>=2.0.0` — Oracle thin driver
- `mysql-connector-python>=8.0.0` — MySQL driver
- `matplotlib>=3.7.0` — 图表渲染

## 安全

- 密码仅存于 `openclaw.json` 环境变量，不落磁盘
- 仅支持 SELECT 查询（只读强制）
- 大表自动拦截 + LIMIT 保护
- 无 sudo 要求

## 变更历史

| 版本 | 说明 |
|------|------|
| v1.2 | 改用 Python thin driver，新增飞书直发，去掉 Java/JDBC 依赖 |
| v1.1 | 安全升级：无 sudo 字体安装，密码零落地 |
| v1.0 | 初始版本 |
