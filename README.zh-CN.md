# AI Product Intelligence

**一个整理产品研究证据、探索 AI 辅助研究的工程作品集原型。**

[English](README.md) · [架构说明](docs/architecture.md) · [公开数据政策](docs/privacy.md) · [安全边界](SECURITY.md)

产品研究需要把品牌、资料来源、参考产品、图片和分析结果连接起来。本项目使用 FastAPI 建立这些数据关系，并将本地证据查询与可选的 AI 调用分开。示例领域为帽饰；演示品牌 **Northstar** 及 `northstar.example` 地址均为虚构内容。

这个仓库展示工程设计和可验证的功能，不宣称真实客户采用、量化业务收益、生产可用性或经过验证的 AI 准确率。

## 主要功能

| 功能 | 实现内容 |
| --- | --- |
| 产品开发资料管理 | 客户、品牌、客户与品牌关系、项目、项目条目 |
| 可追溯的参考资料 | 品牌来源、素材、参考产品与产品分析记录 |
| 本地品牌查询 | 按字面匹配名称，处理大小写与首尾空白，明确报告重名 |
| 证据汇总 | 汇总有效来源、参考产品及允许用于分析的有效素材 |
| 可选联网研究 | 返回带来源链接、检索信息和人工复核标记的品牌摘要 |
| 可选产品分析 | 将产品文字与可选图片转换成结构化帽饰属性 |
| 离线演示与测试 | 使用虚构样本、内存数据库和模拟 AI 响应 |

**技术栈：** Python 3.13、FastAPI、Pydantic、SQLAlchemy、SQLite，以及可选的 OpenAI SDK。

## 快速开始

在仓库根目录运行以下命令。安装依赖需要网络；演示和测试使用本地虚构数据及模拟响应。

### 1. 创建环境

Windows PowerShell：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS / Linux：

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

API 密钥可以留空，本地功能仍可运行。`requirements.txt` 记录具体依赖版本，`requirements.in` 列出直接依赖。

### 2. 运行离线演示

```bash
python scripts/demo.py
```

演示在独立的 SQLite 内存数据库中使用虚构 Northstar 数据，并完全模拟 AI 响应。无需密钥，不产生付费模型调用，也不使用真实客户资料。进程结束后演示记录即消失，不会写入服务使用的数据库。

### 3. 运行检查

```bash
python -m unittest discover -s tests -v
python scripts/check_public_release.py
```

测试覆盖名称匹配、重名处理、证据过滤、引用解析、缓存和上游错误等选定场景。公开发布检查会检查被排除的文件和可疑文本模式；这种启发式检查不能保证发现所有敏感信息。

### 4. 启动本地 API

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

打开 [交互式 API 文档](http://127.0.0.1:8000/docs)。服务会在当前目录创建 `portfolio_demo.db`；数据库不会自动包含离线演示的数据，可在 API 文档中建立自己的虚构记录。上传文件保存在 `uploads/`，数据库和上传目录均不纳入版本控制。

| 接口 | 用途 |
| --- | --- |
| `GET /` | 检查服务是否运行 |
| `GET /brands/by-name?brand_name=Northstar` | 查询已存在的本地品牌 |
| `GET /brand-intelligence/by-name/evidence?brand_name=Northstar` | 汇总该品牌的本地证据，不调用 AI |
| `GET /brand-research?brand_name=...` | 执行可选的联网品牌研究 |
| `POST /product-analyses/product/{product_reference_id}/analyze` | 执行并保存可选的产品 AI 分析 |

服务数据库中还没有对应品牌时，本地名称查询返回 `404`。

## 可选：连接真实 AI

在本地 `.env` 中填写以下配置：

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=
```

自行填写密钥，并明确指定当前 API 账号可用的模型。联网品牌研究需要模型支持网页搜索；图片分析需要支持图片输入。修改后重启服务。即使配置了密钥，离线演示也始终使用模拟 AI。

真实调用可能产生费用。联网研究会向服务商发送品牌名称；产品分析会发送产品文字，以及提供的图片地址或图片内容。启用前请阅读 [数据处理说明](docs/privacy.md)。

引用链接便于核查，不代表结论已经正确。品牌研究预览带有 `needs_review: true`，不会写入数据库；产品分析通过专门接口保存，仍需人工复核。模型输出的置信度尚未校准。

## 工程设计要点

- **本地证据与联网研究分开：** 查询已存资料不依赖模型或网络。
- **明确处理重名：** 多个记录匹配时返回 `409` 和候选项，避免任意选取记录。
- **保留研究依据：** 摘要附带来源、检索时间、模型和缓存状态。
- **离线验证服务边界：** 使用模拟上游响应检验失败路径，减少外部服务状态对测试的影响。
- **控制公开范围：** 通过白名单选择源码、测试、文档和虚构示例，排除运行数据和私有材料。

更多数据关系与取舍见 [架构说明](docs/architecture.md)。

## 当前限制

这是后端作品集原型，尚无登录认证、权限控制、限流和完整产品前端。SQLite、启动时建表和进程内缓存服务于小规模本地演示；数据库迁移、并发处理、部署控制和运行恢复仍需完善。测试覆盖选定流程，不构成完整安全审计或性能评估。

AI 输出质量尚未独立评估或校准。文件上传、外部地址、模型结果校验和错误处理仍需加固。示例服务应仅绑定本机地址；代码公开并不意味着应用可以安全地直接对外部署。
