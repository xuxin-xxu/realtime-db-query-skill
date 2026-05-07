# db-query 安全设计说明 (v2.1)

## 1. 核心安全机制
- **凭据本地隔离**: 密码明文及连接配置统一存放在 `memory/connections.json` 中，系统会自动锁定该文件权限为 `0600`。
  - 🔴 **警告**: 切勿将此文件提交到 Git 或随日志泄露。
- **无 sudo 提权**: 依赖的 CJK 字体通过双轨机制（优先找系统，缺失则自动无痕下载至 `~/.local/share/fonts/`）实现用户级安装，阻断了 `apt-get` 等提权注入风险。
- **强制只读**: 数据库驱动层强限制，主动拦截任何包含 `INSERT / UPDATE / DELETE / DROP` 的修改请求。
- **大表防 OOM**: 无 `WHERE` 条件且预测超过 10 万行的全表扫描会被直接拒绝，查询默认自动追加 `FETCH FIRST 100 ROWS` 限制。

## 2. 升级注意事项 (v1.x / v2.0 -> v2.1)
由于全面转向纯 Python thin driver（`oracledb`, `mysql-connector-python`），已移除了所有 Java 和 JDBC 依赖。
升级步骤：
1. `pip install -r requirements.txt` (或执行 `install.py --auto-pip`)
2. 旧版 JAR 依赖目录 (`lib/`) 可安全删除。
3. 运行 `python scripts/connection_manager.py` 或调用 `diagnose()` 检查本地数据迁移情况。

## 3. 文件权限清单
| 文件/目录 | 描述 | 权限要求 | 风险等级 |
|-----------|------|----------|----------|
| `memory/connections.json` | 包含所有连接配置及密码明文 | `0600` (自动强制) | 🔴 最高 |
| `memory/schema_*.md` | 抓取的表结构元数据 | `0644` | 🟢 低 |
| `~/.local/share/fonts/` | 运行时下载的字体文件 | `0700` | 🟢 低 |
