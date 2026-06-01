# 幻梦数字人

当前版本：`v0.18.2-fixed`  
当前定位：MVP Release Candidate

幻梦数字人是一个面向剧本杀 / 恋陪数字人的小程序与后端工程骨架。当前版本已经打通从剧本项目、资料上传解析、Script Intelligence Pipeline、证据驱动角色候选、角色关系、角色生成、知识库检索、聊天、长期记忆、角色调教、Q版桌宠、内容安全到自动化测试的 MVP 主链路。

请注意：当前系统不会在未上传正式剧本时自动知道真实人物关系。人物关系只来自用户填写、上传文本规则抽取或测试文本。没有 API Key 时不会调用真实模型，会使用 MockLLMProvider。

## 技术栈

- 前端：UniApp、Vue 3、Vite，支持 H5 与微信小程序构建
- 后端：Python、FastAPI、SQLAlchemy
- 数据库：默认 SQLite，可通过 `DATABASE_URL` 切换
- 存储：默认 local uploads，预留 S3-compatible / custom
- AI Provider：mock / openai_compatible / custom_http
- OCR Provider：mock / paddleocr
- 图片生成 Provider：mock / custom

## 已完成功能

- dev_mock 用户体系与 `user_id` 数据隔离
- 剧本项目空间 `ScriptProject`
- 文件上传与 TXT / DOCX / PDF 真实文本解析
- 图片 OCR Provider 骨架
- CharacterProfile 角色设定抽取
- 项目内证据驱动角色候选识别与批量生成
- Script Intelligence Pipeline：文本清洗、文档分层、script chunk、候选复核和关系短句抽取
- 角色关系图 / 关系网络
- KnowledgeChunk 知识库骨架与关键词检索
- Chat Engine、PromptBuilder、聊天会话与消息落库
- Multi-LLM Provider 骨架
- 长期记忆系统
- 角色自定义 / 调教配置
- PetAsset Q版桌宠资产系统
- StorageProvider 与部署生产化骨架
- 微信小程序适配骨架
- 内容安全与隐私合规骨架
- 自动化验收脚本与交付包安全检查

## 当前 mock / 骨架能力

- 角色生成、聊天、记忆抽取：当前默认规则 + mock
- LLM：未配置 `LLM_API_KEY` 时使用 MockLLMProvider
- OCR：默认 MockOCRProvider，PaddleOCR 需部署环境选择安装
- 图片生成：默认 MockImageProvider
- 内容安全：规则版 safety，不是真实内容审核 API
- 用户登录：dev_mock，不是真实微信登录
- RAG：SQLite + 文本分块 + 关键词检索，未接向量数据库
- Storage：默认 local uploads，对象存储为骨架

## v0.18.2 真实剧本资料识别增强

- 项目详情页和创建页支持一次选择多个资料文件，逐个上传、逐个解析，单个失败不会阻断整包资料。
- 角色候选从 keyword-driven 改为 evidence-driven：只有对白标签、身份字段、关系句、当前角色检测、反复行动主体等证据足够时才进入候选。
- `X的声音 / X的照片 / X的日记` 等结构不会生成独立角色；如果 `X` 已是高置信角色，会把整句归入 `X` 的证据片段。
- 候选会区分 `person / organization / place / prop / clue / document_term / structure_term / noise / unknown`，前端按高置信、待确认、非人物 / 噪声分层展示。
- 有真实 `openai_compatible` 配置时，候选复核可调用当前模型 Provider；没有 API Key 或调用失败时回退 `RuleCandidateReviewer`，不阻断主流程。
- LLM reviewer 只接收候选摘要、证据片段和统计信息，不把完整商业剧本文本无限制发送给模型。
- `relationship_sentence` 只作为关系证据，不能单独把候选提升为高置信人物；必须结合对白、身份字段、文件/标题、当前角色检测或 reviewer 高置信结论。
- `personhood_validator` 会把代词短语、抽象概念、章节结构、线索/真相/玩家/主持人、`X的Y` 结构和从句碎片降级为非人物或待确认。
- reviewer 不会长期停留在 `pending`：真实模型不可用时同步回退 `rule_fallback`，前端可明确看到复核状态。
- 当前目标是显著减少误识别，不是做到完美剧本理解；复杂剧本仍需要用户确认候选后再批量生成。

## 本地启动后端

```bash
cd fantasy-role-ai/backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

健康检查：

```text
http://127.0.0.1:8000/health
```

也可以在项目根目录运行：

```bash
scripts/dev_backend.bat
```

或：

```bash
sh scripts/dev_backend.sh
```

## 本地启动前端 H5

```bash
cd fantasy-role-ai/frontend
npm install
npm run dev:h5
```

也可以在项目根目录运行：

```bash
scripts/dev_frontend_h5.bat
```

或：

```bash
sh scripts/dev_frontend_h5.sh
```

## 微信小程序构建

```bash
cd fantasy-role-ai/frontend
npm run build:mp-weixin
```

构建后用微信开发者工具导入 `frontend/dist/build/mp-weixin`。当前微信登录接口只是预留，不会伪造 openid，也不会调用微信真实接口。

## 环境变量说明

复制 `.env.example` 为 `.env` 后配置。`.env` 不允许提交或打包。

常用配置：

```env
DATABASE_URL=sqlite:///./fantasy_role_ai.db
LLM_PROVIDER=mock
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=mock-model
OCR_PROVIDER=mock
IMAGE_PROVIDER=mock
STORAGE_PROVIDER=local
ENABLE_DEBUG_OUTPUT=true
SAFETY_MODE=rule
```

生产环境建议：

- 配置生产数据库和对象存储
- 配置 HTTPS 域名与 CORS 白名单
- 配置正式微信登录
- 配置真实内容安全服务
- 设置 `ENABLE_DEBUG_OUTPUT=false`
- 迁移或关闭 legacy `user_id=null` 数据访问

## 自动化测试

先启动后端，再运行：

```bash
python tests/run_backend_smoke.py
python tests/run_project_isolation.py
python tests/run_safety_checks.py
python tests/run_candidate_extraction_checks.py
```

或：

```bash
scripts/run_tests.bat
```

```bash
sh scripts/run_tests.sh
```

交付包检查：

```bash
python tests/run_package_check.py --zip fantasy-role-ai-v0.18.2-fixed.zip
```

报告输出到 `tests/reports/`，该目录为本地运行产物，不进入交付压缩包。

## 交付目录说明

- `backend/`：FastAPI 后端
- `frontend/`：UniApp 前端
- `docs/`：设计文档、API 文档、交付文档
- `tests/`：自动化验收脚本和测试数据
- `scripts/`：本地启动和测试辅助脚本
- `VERSION.md`：版本信息
- `.env.example`：环境变量示例，不包含真实密钥

## 安全提醒

- 不要把真实 API Key 写入代码、文档、截图或压缩包
- 不要打包 `.env`
- 不要打包数据库、真实上传文件、`node_modules`、构建产物或测试报告
- 生产环境关闭 debug 输出
- 正式上线前需要隐私协议、用户协议、内容安全策略和合法域名

## 下一步开发建议

1. 接入正式微信登录和用户协议 / 隐私协议流程。
2. 接入真实内容安全服务。
3. 接入真实 LLM Provider，并保留 mock fallback。
4. 将关键词检索升级为 embedding + 向量数据库。
5. 接入真实 OCR 与图片生成服务。
6. 增加 CI，把 `tests/` 脚本纳入每次交付前检查。
# v0.18.3-rc1：LLM-first 剧本理解增强

本版本在 v0.18.2-fixed 的 evidence-driven 基础上增加 LLM-first Script Understanding 链路：多文件资料包解析后，系统先构建 corpus manifest，再通过结构化 Prompt 让当前配置的大模型复核文档类型、角色候选、别名合并、关系、角色档案和剧透级别。没有 `LLM_API_KEY` 或模型调用失败时，系统明确使用 `rule_fallback`，不会伪造成真实 AI 理解。

重要边界：

- 当前不是模型训练、微调或 LoRA。
- 测试集只用于自动化验收，不会写进业务规则。
- LLM 只接收文件摘要、chunk 摘要和证据片段，不无限制发送完整剧本文本。
- 复杂商业剧本仍需要用户确认候选、关系、文件归属和剧透模式。
- 未配置真实 API Key 时不会调用真实模型；DeepSeek / OpenAI-compatible 配置仍由 `.env` 控制。

新增接口：

- `POST /api/projects/{project_id}/script-intelligence/llm-analyze`
- `GET /api/projects/{project_id}/script-intelligence/status`
- `GET /api/projects/{project_id}/script-intelligence/result`
- `POST /api/projects/{project_id}/script-intelligence/confirm`
