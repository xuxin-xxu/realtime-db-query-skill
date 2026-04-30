# SECURITY.md — db-query 安全设计说明 (v2.0 thin driver)

> 本文件详细说明 v2.0 的安全架构设计。
> **所有用户必须阅读此文件。**

---

## 🔴 已修复的高风险问题

### Issue 1: `sudo apt-get install` 提权风险（VirusTotal 🔴 高危）

**旧版本：**
```python
subprocess.run(["sudo", "apt-get", "install", "-y", "fonts-noto-cjk", "-q"])
```
攻击者通过 Agent prompt injection 可在目标机器执行任意系统命令。

**v2.0 修复 — 三级降级，用户级双轨安装（无 sudo）：**
```
1. 检查系统字体  /usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc
2. 检查用户目录  ~/.local/share/fonts/
3. 首次出图遇缺，通过脚本并轨向 GitHub 凭空下载 Regular 及 Bold 变体的 OTF 到 ~/.local/share/fonts/
   https://github.com/notofonts/noto-cjk/.../NotoSansCJKsc-Regular.otf
   https://github.com/notofonts/noto-cjk/.../NotoSansCJKsc-Bold.otf
```

**验证：**
```bash
grep -rn "sudo\|apt-get" skills/db-query/
# 返回空
```

---

### Issue 2: 明文密码存储（VirusTotal 🔴 高危）

**旧版本：**
```json
// memory/connections.json
{ "alias": "生产库", "password": "Jessica820608", ... }
```
机器被入侵 → 攻击者直接拿到所有数据库密码。

**v2.0 架构延续 — Zero-Disk Credential 机制：**

```
┌─────────────────────────────────────────────────────────┐
│            openclaw.json (Single Source of Truth)        │
│                                                         │
│  skills.env:                                            │
│    CONN____  = '{"db_type":"oracle","user":"wksp_xuxin", │
│                  "password":"Jessica820608",             │
│                  "jdbc_url":"jdbc:oracle:thin:@..."}'    │
│                                                         │
│    CONN_PROD_MYSQL = '{"db_type":"mysql","user":"root", │
│                        "password":"xxx",                │
│                        "jdbc_url":"jdbc:mysql://..."}'   │
└─────────────────────────────────────────────────────────┘
                           │
                           │ runtime read-only (os.environ)
                           ▼
              ┌────────────────────────────┐
              │  connection_manager.py     │
              │  get_active() → dict        │
              │  (仅存在于进程内存)           │
              └────────────────────────────┘
                           │
                           │ thin driver connect
                           ▼
              ┌────────────────────────────┐
              │      Oracle / MySQL         │
              │      (真实数据源)            │
              └────────────────────────────┘

memory/connections.json  ←  仅 legacy fallback，零密码保证
memory/schema_*.md       ←  仅元数据（表结构），无凭据
disk: 无任何密码落地
```

---

## 📋 完整的 alias → env key 映射表

| Alias | Env Key | 说明 |
|-------|---------|------|
| `生产库` | `CONN____` | 中文别名 |
| `测试库` | `CONN____` | 冲突时自动加后缀区分 |
| `prod-db` | `CONN_PROD_DB` | 英文别名 |
| `MySQL开发库` | `CONN_MYSQL____` | 类型前缀 |
| `Oracle报数库` | `CONN_ORACLE____` | 类型前缀 |

别名中的非字母数字字符 → `_`，前缀 `CONN_`，全大写。

若存在别名冲突（两个库别名映射到相同的 `CONN____`），`add_connection()` 会输出警告并建议使用有区分度的别名。

---

## 🛠 从 v1.x 升级步骤

### Step 1: 安装 thin driver 依赖

```bash
cd ~/.openclaw/skills-ins/db-query
python install.py --auto-pip
# 或
pip install -r requirements.txt
```

### Step 2: 确认当前配置兼容

现有配置中的 `jdbc_url` 字段仍然兼容，thin driver 会自动解析：
- Oracle `jdbc:oracle:thin:@host:port/service` → 提取 DSN
- MySQL `jdbc:mysql://host:port/db` → 提取 host/port/db

### Step 3: 可选清理

```bash
# 旧版 JAR 文件不再需要，可以安全删除
rm -rf ~/.openclaw/skills-ins/db-query/lib/
```

### Step 4: 验证

```python
from connection_manager import diagnose, get_active
print(diagnose())
print("当前活跃:", get_active()["alias"])

from db_query import query
rows = query("SELECT 1 FROM DUAL")
print(rows)  # 应返回 [{"1": 1}]
```

---

## 🔒 文件权限清单

| 文件 | 内容 | 权限 | 敏感度 |
|------|------|------|--------|
| `openclaw.json` | 全部连接配置（含密码） | 0600（网关配置） | 🔴 最高 |
| `memory/connections.json` | 仅连接别名（无密码） | 0600 | 🟡 中 |
| `memory/schema_*.md` | 表结构元数据 | 0644 | 🟢 低 |
| `~/.local/share/fonts/` | CJK 字体文件 | 0700 | 🟢 低 |

---

## ⚠️ 重要安全提醒

1. **openclaw.json 包含所有密码**：确保网关配置文件的 OS 文件权限为 `0600`，切勿提交到 git。
2. **重启后 env 生效**：`openclaw.json` 修改后需 `openclaw gateway restart`。
3. **日志脱敏**：查询日志和错误信息可能包含 SQL 片段，避免在公开渠道分享。
4. **多租户注意**：若多人共用网关，每个人应使用独立的 `accountId` 隔离连接配置。
5. **connections.json 可删除**：升级完成后，若确认所有连接都迁移到了 `openclaw.json`，可删除 `memory/connections.json`，`connection_manager` 会自动回退到纯 env var 模式。
6. **v2.0 去除了 Java 依赖**：不再需要 JDK/JRE、JDBC JAR 文件，安装配置大幅简化。

---

## ✅ 安全进化轨迹对比

| 检查项 | v1.0 | v2.0 (thin driver) |
|--------|------|--------|
| `sudo apt-get install` 字体漏洞 | ✅ 移除 | ✅ 移除无痕下载 |
| 字体库渲染缺字/豆腐块现象 | ✅ 完整获取双轨库 | ✅ 完整获取双轨库 |
| 明文密码在磁盘 | ✅ 仅存 openclaw.json env | ✅ 仅存 openclaw.json env |
| Oracle JDBC JAR 下载/依赖 | ⚠️ 需 Maven 下载 JAR | ✅ 无 JAR，纯 Python |
| MySQL JDBC JAR 下载/依赖 | ⚠️ 需 Maven 下载 JAR | ✅ 无 JAR，纯 Python |
| Java/JDK 运行时依赖 | ❌ 必须安装 JDK >=18 | ✅ 无需 Java |
| 总依赖大小 | ~30MB (JRE + JARs) | ~15MB (纯 Python) |

---

## 🚀 v2.0 架构变更亮点

1. **去掉 JPype1/JayDeBeApi/JDBC** — 全部改用 Python native thin driver
2. **去掉 Java 检测/安装** — `install.py` 简化为纯 `pip install`
3. **去掉 JDBC JAR 下载** — 不再需要 Maven 下载 `ojdbc11.jar` 等
4. **兼容旧配置** — 仍然读取 `jdbc_url` 字段，自动解析为 thin driver 格式
5. **安装更简单** — 只需 `pip install oracledb mysql-connector-python matplotlib`

---

## 📦 依赖清单 (v2.0)

| 包 | 用途 | 协议 |
|----|------|------|
| `oracledb>=2.0.0` | Oracle 数据库连接（thin mode） | Apache 2.0 |
| `mysql-connector-python>=8.0.0` | MySQL 数据库连接 | GPL 2.0 |
| `matplotlib>=3.7.0` | 图表生成 | PSF |
