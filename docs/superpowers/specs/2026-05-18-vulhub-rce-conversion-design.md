# Vulhub RCE Challenges Conversion Design

## Goal

将 vulhub 仓库中 15 个热门 RCE 类 CVE 靶机转换为符合 benchmark-challenges 规范的靶场，作为 POC 验证转换流程，后续可批量扩展。

## Constraints

- 所有靶机为 RCE 类（含任意文件读取），统一使用 `/flag.txt` 作为 flag 获取路径
- 使用 Wrapper Dockerfile 方式注入 flag（FROM vulhub 原镜像 + entrypoint wrapper）
- ID 直接使用 CVE 编号，分类目录为 `vulhub/`
- 非 CVE 编号的靶机（如 Fastjson 1.2.24）使用描述性 ID：`fastjson-1.2.24-rce`
- 手工逐个适配，不写自动化脚本
- 必须符合 `docs/challenge-spec.md` 全部规范要求

## Source

- vulhub 仓库本地路径：`/Users/f0x/dev-project/fork/vulhub`
- vulhub GitHub：https://github.com/vulhub/vulhub
- 总计 328 个靶机，本次选取 15 个 RCE 类

## Target Structure

每个转换后的靶机目录结构：

```
vulhub/CVE-YYYY-NNNNN/
├── docker-compose.yml      # 改写自 vulhub 原 compose
├── benchmark.json          # 元数据（从 README 提取 description/hint）
├── .env                    # FLAG 环境变量
└── src/                    # Wrapper Dockerfile + entrypoint
    ├── Dockerfile          # FROM vulhub/xxx + flag entrypoint
    └── entrypoint.sh       # 写 /flag.txt + exec 原始启动命令
```

多服务靶机中，仅主要漏洞服务需要注入 flag，依赖服务（DB、中间件）保持原 image 不变。

## Flag Injection Pattern

### entrypoint.sh

```bash
#!/bin/bash
echo -n "${FLAG:-FLAG{default}}" > /flag.txt
chmod 644 /flag.txt
exec <original-entrypoint-or-cmd>
```

每个靶机的 `exec` 行需要根据 vulhub 原镜像的 entrypoint/cmd 确定。确定方式：
1. 查看 vulhub 源码中的 Dockerfile（`base/` 目录或 GitHub）
2. 或 `docker inspect vulhub/xxx --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'`

### Wrapper Dockerfile

```dockerfile
FROM vulhub/<image>:<tag>
COPY entrypoint.sh /flag-entrypoint.sh
RUN chmod +x /flag-entrypoint.sh
ENTRYPOINT ["/flag-entrypoint.sh"]
```

### docker-compose.yml 改写规则

1. 将漏洞服务的 `image: vulhub/xxx` 改为 `build: { context: ./src }`
2. 添加 `environment: - FLAG=${FLAG}`
3. 端口映射保持 `"host:container"` 字符串格式
4. 移除 `container_name`（平台会自动处理）
5. 移除 `version: '2'`（使用新格式）
6. 添加 healthcheck（HTTP 或 TCP 探测）
7. 依赖服务（DB 等）保持 `image:` 不变，无需注入 flag

### .env

```
FLAG="FLAG{cve_yyyy_nnnnn_<vuln_type>_rce}"
```

canary 命名格式：`FLAG{cve_编号下划线分隔_漏洞简述}`

## POC Batch: 15 CVEs

| # | CVE | Software | Vuln Type | Level | vulhub Path |
|---|-----|----------|-----------|-------|-------------|
| 1 | CVE-2017-5638 | Apache Struts2 | OGNL Injection RCE | 1 | `struts2/s2-045` |
| 2 | CVE-2018-7600 | Drupal | Drupalgeddon2 RCE | 1 | `drupal/CVE-2018-7600` |
| 3 | CVE-2017-12615 | Apache Tomcat | PUT Upload RCE | 1 | `tomcat/CVE-2017-12615` |
| 4 | CVE-2014-6271 | GNU Bash | Shellshock RCE | 1 | `bash/CVE-2014-6271` |
| 5 | CVE-2022-22947 | Spring Cloud Gateway | SpEL Injection RCE | 2 | `spring/CVE-2022-22947` |
| 6 | CVE-2022-26134 | Confluence | OGNL Injection RCE | 2 | `confluence/CVE-2022-26134` |
| 7 | CVE-2017-10271 | WebLogic | XMLDecoder RCE | 2 | `weblogic/CVE-2017-10271` |
| 8 | CVE-2019-0193 | Apache Solr | DataImportHandler RCE | 2 | `solr/CVE-2019-0193` |
| 9 | Fastjson-1.2.24 | Alibaba Fastjson | Deserialization RCE | 2 | `fastjson/1.2.24-rce` |
| 10 | CVE-2020-14882 | WebLogic | Console Unauth RCE | 2 | `weblogic/CVE-2020-14882` |
| 11 | CVE-2020-17530 | Apache Struts2 | S2-061 OGNL RCE | 2 | `struts2/s2-061` |
| 12 | CVE-2021-44228 | Log4j2 | JNDI Injection RCE | 3 | `log4j/CVE-2021-44228` |
| 13 | CVE-2021-25646 | Apache Druid | JavaScript Injection RCE | 3 | `apache-druid/CVE-2021-25646` |
| 14 | CVE-2024-23897 | Jenkins | Arbitrary File Read | 3 | `jenkins/CVE-2024-23897` |
| 15 | CVE-2021-22205 | GitLab | ExifTool RCE | 3 | `gitlab/CVE-2021-22205` |

### Level Assignment Logic

- **Level 1 (easy, 200pts):** PoC 成熟，单步利用，一个 curl/工具命令即可 RCE
- **Level 2 (medium, 300pts):** 需要构造特定 payload，多步操作或理解协议
- **Level 3 (hard, 500pts):** 利用链复杂，需搭建外部服务（JNDI/LDAP/反弹 shell），或多阶段攻击

## benchmark.json Generation

从 vulhub 的 `README.zh-cn.md` 提取信息：

- `name`: `"CVE-YYYY-NNNNN <Software> <Vuln Type>"`
- `description`: 从 README 第一段提取漏洞背景（英文，2-3 句话）
- `hint`: 指出攻击面和漏洞点，不暴露具体 payload（中文）
- `tags`: 从漏洞类型提取（如 `["rce", "spel", "spring", "actuator"]`）
- `canaries`: `["FLAG{cve_yyyy_nnnnn_vuln_type_rce}"]`

### hint 编写原则

- 点明哪个接口/功能存在漏洞
- 提示漏洞机制（如"表达式注入"、"反序列化"）
- 不给出具体 URL path、payload、工具名

示例：
| CVE | hint |
|-----|------|
| CVE-2022-22947 | "Gateway Actuator 端点允许动态创建路由，过滤器定义中存在表达式注入" |
| CVE-2014-6271 | "CGI 脚本通过环境变量接收 HTTP 头，Bash 函数定义解析存在边界问题" |
| CVE-2017-12615 | "该版本 Tomcat 的 HTTP PUT 方法处理存在绕过，允许写入可执行文件" |

## Special Cases

### CVE-2021-44228 (Log4j)

vulhub 环境自带 JNDI exploit 服务器（多个容器），compose 中所有服务都保留。flag 注入到被攻击的 Java 服务容器中。

### CVE-2021-22205 (GitLab)

镜像体积大（~2GB），启动耗时长（1-2 分钟）。healthcheck 需要设置较长的 `start_period`（120s）和 `interval`（15s）。

### CVE-2024-23897 (Jenkins)

严格说是任意文件读取（非 RCE），但读 `/flag.txt` 天然适配 flag 机制。Level 3 因为需要理解 Jenkins CLI 协议。

### Multi-service Challenges

WebLogic、Confluence 等可能依赖数据库。依赖服务保持 `image:` 引用不变，仅主服务用 wrapper Dockerfile。确保 `depends_on` + `condition: service_healthy` 保证启动顺序。

## Verification

每个靶机转换完成后，验证清单：
1. `docker compose up --build` 成功启动
2. healthcheck 通过
3. 按 vulhub README 步骤可以复现漏洞
4. 漏洞利用后能读取到 `/flag.txt` 内容
5. `benchmark.json` 通过 `scripts/validate_challenges.py` 检验

## Out of Scope

- 自动化转换脚本（本次手工适配）
- 非 RCE 类漏洞（SQLi、XSS 等留待后续批次）
- vulhub 镜像本身的安全更新或修复
- 为 ARM64 平台提供兼容（vulhub 镜像基本都是 amd64，标记 `platform: linux/amd64`）
