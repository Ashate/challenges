[中文文档](README.zh-CN.md) | English

# Benchmark Challenges

[benchmark-platform](https://github.com/wgpsec/benchmark-platform) 的挑战数据仓库。

## 目录结构

```
xbow/          # 来自 xbow-validation-benchmarks 的 74 个挑战
custom/        # 4 个自定义挑战（XSS、Auth 等）
argus/         # 来自 argus-validation-benchmarks 的 60 个挑战
```

## 挑战来源

| 来源 | 数量 | 链接 | 描述 |
|--------|-------|------|-------------|
| xbow | 74 | [xbow-validation-benchmarks](https://github.com/xbow-dev/xbow-validation-benchmarks) | 覆盖多种框架的 Web 应用漏洞 |
| argus | 60 | [argus-validation-benchmarks](https://github.com/pensarai/argus-validation-benchmarks) | SSRF、XSS、SQLi、RCE、IDOR、反序列化（Next.js、Flask、Express、Go、Django、Rails、Spring Boot） |
| custom | 4 | — | 针对特定场景手工打造的挑战 |

## 使用方法

本仓库由 benchmark-platform 的挑战商店（Challenge Store）功能消费。每次推送时，挑战会自动打包并作为 GitHub Release 资产发布。

您可以直接在平台 Web 界面的侧边栏（**Challenge Store**）中浏览和下载挑战，也可以手动克隆：

```bash
git clone https://github.com/wgpsec/benchmark-challenges /tmp/benchmarks
cp -r /tmp/benchmarks/xbow challenges/xbow
cp -r /tmp/benchmarks/custom challenges/custom
cp -r /tmp/benchmarks/argus challenges/argus
```

## 添加挑战

1. 在相应的分类下创建目录：`xbow/XBEN-XXX-24/`、`argus/APEX-XXX-25/` 或 `custom/MY-CHALLENGE/`
2. 至少包含以下文件：`docker-compose.yml`、`benchmark.json`、`.env`
3. 推送到 main 分支 — GitHub Action 将自动打包并发布

## 创建自定义挑战

想要构建自定义挑战？以下两个资源可以帮到您：

- **[格式规范](docs/challenge-spec.md)** — 所有必需文件、字段和约束的完整参考。将此文档复制到任何 AI 工具即可生成符合规范的挑战。
- **[Claude Code 技能](.claude/skills/create-challenge.md)** — 面向 Claude Code 用户的交互式技能。只需描述您的攻击场景，它就能生成所有可直接导入的文件。

AI 快速上手：

```
1. 将 docs/challenge-spec.md 的内容复制给您的 AI 助手
2. 描述您想要的漏洞场景
3. 获得一个完整的挑战目录
4. 运行 `docker compose up --build` 进行本地测试
5. 打包为 `category--name.zip` 并通过平台 UI 导入
```

## 挑战格式

```
XBEN-001-24/
├── docker-compose.yml    # 必需
├── benchmark.json        # 元数据（名称、描述、等级、分值）
├── benchmark.yaml        # 可选，多 FLAG 定义
├── .env                  # FLAG 环境变量
└── app/ mysql/ ...       # 应用代码
```

## CI/CD

每次推送到 `main` 分支时，GitHub Action 将：

1. 检测哪些挑战目录发生了变更
2. 将每个变更的挑战打包为 zip 归档
3. 生成包含所有挑战的 `manifest.json`
4. 将资产上传到 `latest` GitHub Release

仅重新打包发生变更的挑战（增量构建）。

## WgpSec 智能体生态系统

benchmark-challenges 是 **WgpSec 智能体生态系统** 的数据层 — 为评估 AI 智能体攻击能力提供真实世界的脆弱环境。

```
┌───────────────────── WgpSec 智能体生态系统 ─────────────────────┐
│                                                                     │
│  知识 ➜ 服务 ➜ 执行 ➜ 评估                                      │
│                                                                     │
│  AboutSecurity ──▶ context1337 ──▶ tchkiller ──▶ benchmark-platform │
│  (知识库)          (MCP 服务器)    (渗透测试智能体)  (平台)        │
│                                         ▲                           │
│                                    PoJun (通用求解器)               │
│                                         │                           │
│                              benchmark-challenges (本仓库)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

| 项目 | 角色 |
|---------|------|
| [AboutSecurity](https://github.com/wgpsec/AboutSecurity) | 结构化渗透测试知识库（技能、字典、Payload、漏洞） |
| [context1337](https://github.com/wgpsec/context1337) | MCP 服务器 — 将 AboutSecurity 转化为可供 AI 智能体搜索的 API |
| [tchkiller](https://github.com/wgpsec/tchkiller) | 具备多轮决策和团队协作能力的自主渗透测试智能体 |
| [benchmark-platform](https://github.com/wgpsec/benchmark-platform) | HunXiang CTF 挑战平台，用于评估智能体攻击能力 |
| [benchmark-challenges](https://github.com/wgpsec/benchmark-challenges) | 挑战数据仓库 — 通过 GitHub Releases 打包分发 |
| PoJun | 通用 AI 问题求解引擎（私有） |

## 许可证

[MIT](LICENSE)
