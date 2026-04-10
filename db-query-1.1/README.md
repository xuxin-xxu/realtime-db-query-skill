# 🚀 db-query (v1.1) — 大模型 Agent 智能查库大管家

基于 **OpenClaw** 生态深度定制的读写隔离级交互数据库查询技能 (Skill)。
全面优化了对话连贯性、沉浸式自然语言配置交互、以及极低门槛的环境依赖热修复。

> **🌟 版本定位：Agentic 工作流升级版**
> 告别繁琐的命令行配置，不再使用脆弱且碎片化的查询脚本。当您缺少 Java 环境或 JDBC 驱动包时，大模型会温柔地弹窗询问并全自动为您于后台静默下载、环境剥离！

---

## 💎 v1.1 核心全新特性

| 特性分类 | 说明 |
|------|--------|
| **🤖 Agent 会话管家状态管理** | 针对 LLM 的上下文缓存做了深度定调：**1. 破冰探测**：如果是纯净空环境查询，系统立刻拦截阻断，大模型会用极具人情味的话语索要您的账号串。**2. 多库会话锁定**：如果您挂载了 2 个以上的库，大模型会乖乖弹出选单，只要您本会话敲定了一次，之后的关联提问将在此 Session 内永久绑死该 Alias 别名！ |
| **💡 无缝无痛底层环境部署** | 引入 `install.py` 无头驱动命令。大模型如果检测到缺 Java (>=18)，能沙盒化使用 `pip install-jdk` (Mac) 或原生安全提权 (Linux) 下载 JDK 21 和 JDBC 21.21.0.0。并增设 `requirements.txt` 以配合 OpenClaw 自运维原生启动。 |
| **🔗 多核原生大一统查询入口** | 彻底抛弃旧版的 `query_optimizer.py` 正则拼接，下架隔离的 `oracle_query` 和 `mysql_query`。如今**全球收敛唯一查询组件 -> `scripts/db_query.py`**！通过 `jaydebeapi` 和 `JPype` 智能侦测底层连接。 |
| **🔒 严格“无痕”云安全机制** | 坚守 v1.0.1 成功验证的核心机密性原则。您的任何数据库账号密码**统统不写入磁盘**，全采用 `openclaw.json -> skills.env` 映射读取。 |
| **📊 解耦的原生图表引擎** | 移除了内置硬编码的旧版飞书机器人秘钥。升级为 `Agent 原生接管 Markdown 投递`，图表通过 `chart_utils.py` 无痕渲染，补齐了包含 Regular 及 Bold 变体的一整套 CJK 中文字体自动安装流程，彻底告别乱码豆腐块现象！ |

---

## ⚙️ 第一步：让它立刻跑起来！(开箱即装)

如果您之前在 `v1.0.0` 版本已经有了相应的 JAR 环境，您可以直接平滑将其 copy 到该 `lib/` 目录下即可。

如果你在使用纯净的宿主机首次部署该新系统，直接允许/召唤 Agent 在终端触发以下任意**引导参数**, 完美搞定一切繁杂的运维配置：
```bash
# 解决没安装合适高级架构的 Java 的问题，将自行装载 JDK21
python install.py --auto-java

# 完美从 Maven 官链同步拉取并校验所需的 4组极难伺候的 Oracle TCPS Jars 及 MySQL Connector
python install.py --auto-jdbc 
```
*备注：Agent 大模型会在侦测到确实缺环境时主动运行以上脚本请求配置。所有依赖均落盘至本 Skill 内的 `lib/`，或 `~/.jdk` 下完全隔离！*

---

## 🗣️ 第二步：随心所欲的大模型对话配库

传统的 DB 探针配置繁冗。但在 `db-query-1.1` 中，您**完全不需要手动找文件**！

当你完成了驱动热下载直接命令 OpenClaw 大模型进行查库动作：
> **你：**“帮我瞅瞅最新的销售额记录表行数。”

> **Agent：**“抱歉，由于目前系统尚未配置任何数据库连接记录，我无法马上为您查询。请您提供将要连接的数据库信息：1. 数据库类型 2. 连接地址 3. 登录账号和密码...”

直接提供后，大模型作为高阶代理会自动调用 `add_connection()` 的后端，利用它将这些数据安全格式化写入内存环境！

如果您希望**硬核后台配置**，进入 `openclaw config edit`：
在 `skills.env` 中添加您的串（所有特俗字符如中文在 Env 里由 Agent 换算成特定统配映射）：
```json
{
  "skills": {
    "env": {
      "CONN_PROD_ORACLE": "{\"db_type\":\"oracle\",\"user\":\"wksp_super\",\"password\":\"Passwd123!\",\"jdbc_url\":\"jdbc:oracle:thin:@(description=(address=(protocol=tcps)(port=1522)(host=adb.ca-toronto-1.oraclecloud.com))(connect_data=(service_name=your_instance_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))\",\"wallet_path\":\"/home/ubuntu/adbwallet\"}",
      "CONN_REPORT_MYSQL": "{\"db_type\":\"mysql\",\"user\":\"root\",\"password\":\"root\",\"jdbc_url\":\"jdbc:mysql://localhost:3306/report\"}"
    }
  }
}
```

---

## 🔑 安全配置与调试指南

### 文件权限声明
| 文件或目录层级 | 建议权限要求 |
|------|---------|
| `openclaw.json` (核心宿主环境凭证) | `0600`（内部保管含密码流） |
| `lib/*.jar` | `0644` |
| `memory/connections.json` | `0600`（无密码回溯旧版适配版列表） |

### 常见 Agent 交互说明
**Q: 如果我有 5 个不同数据源，大模型每次都要我写 alias 名称吗？**
→ **完全不用！** 这正是 v1.1 针对 Agent 调优的核心骄傲。基于 `SKILL.md` 配置的“一次性询问强制锁流”：只要开启了新网页（或上下文）。大模型只会在您第一句话发出时罗列当前可用的 5 个资源名单让您回“1/2/3/4/5”。紧接着长达几小时的所有问题，系统会锁死在此连接上直到您明确下令要求跨库查询。

**Q: 连接失败报 `ORA-12560/Network Adapter` 怎么办？**
→ 请查验如果您在使用 Oracle 特有的 Wallet 加密 (TCPS) 时，您的 `TNS_ADMIN / wallet_path` 是正确写入并在同一主机下的！由于隔离策略，请尽量给入该宿主的**绝对路径**。

**Q: 输出的图表中文变成方块怎么办？遇到飞书发不了图片的问题？**
→ 不用担心，1.1 版本已从底层修复：如果您刚装箱，它会自动无感去 GitHub 预载缺失的 `Noto CJK` 完整中文字库（包含粗体/常规双规制）到宿主舱位。对于图片下发，已全面剔除了内置绑死的 API 后台，现在所有图片路径将直接以 Markdown 的方式呈递由 OpenClaw 本身进行动态收发分发！

---

## 📄 关联内部核心档案

- [SKILL.md](./SKILL.md) — 决定大模型行为流、AI 状态准则。
- [scripts/db_query.py](./scripts/db_query.py) — 唯一的原生防注入跨源查询统一基座。
