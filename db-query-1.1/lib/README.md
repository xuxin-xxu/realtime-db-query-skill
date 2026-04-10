# lib/

此目录需要从 db-query v1.0.0 复制以下 JAR 文件：

```
ojdbc11.jar          # Oracle JDBC Thin Driver (Java 21 compatible)
oraclepki.jar         # Oracle PKI for wallet/TCPS operations
osdt_core.jar         # Oracle Security Core
osdt_cert.jar         # Oracle Security Certificate
mysql-connector-java.jar  # MySQL JDBC Driver
```

**来源**：从 Oracle 官方下载或从 db-query v1.0.0 的 lib/ 目录复制。

**复制命令**（在有权限的环境下执行）：
```bash
cp /home/ubuntu/.openclaw/workspace_mayu/skills/db-query/lib/*.jar \
   /home/ubuntu/.openclaw/workspace_mayu/skills/db-query-1.0.1/lib/
```
