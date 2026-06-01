# MVP交付说明

## 项目当前能做什么

当前 MVP RC 支持从剧本项目空间内上传资料、解析文本、规则抽取角色候选、生成单个或多个数字人、构建知识片段、进行项目内隔离检索、聊天、长期记忆、角色调教、角色关系图、Q版桌宠资产管理、内容安全规则检查和自动化回归验收。

用户体系当前为 `dev_mock`，所有新建项目、文件、角色、聊天、记忆和桌宠资产会写入 `user_id`，用于验证多用户数据隔离。

v0.18.2-fixed 增强了真实剧本资料识别链路：资料解析后可进入 Script Intelligence Pipeline，依次完成文本清洗、文档分层、script chunk、证据驱动候选抽取、候选 reviewer 复核和关系短句抽取。该链路不是模型训练，也不是把测试集写进业务规则；目标是减少章节词、线索词、OCR 碎片、页眉页脚、`X的声音 / X的照片` 这类非人物文本被误识别为角色。
本次 fixed 版进一步收紧：单独 `relationship_sentence` 不会进入高置信人物区；代词短语、抽象词、功能词和从句碎片由 `personhood_validator` 降级；无真实 API Key 时 reviewer 同步回退 `rule_fallback`，前端不应再显示长期 pending。

## 当前不能做什么

- 不做正式微信登录
- 不做支付
- 不做正式上线部署
- 不接真实 API Key
- 不声明真实理解剧本关系
- 不做真实 LLM 角色抽取
- 不做真实 embedding / 向量数据库
- 不做真实 3D / Live2D

人物关系当前来自用户填写、上传文本规则抽取或测试文本，不代表系统在未上传正式剧本时自动知道真实关系。

复杂剧本仍需要用户在候选确认页人工确认后再批量生成数字人。LLM reviewer 只复核候选摘要和证据片段，不会无限制读取完整商业剧本全文；没有 API Key 或 reviewer 失败时会回退规则复核。扫描版 PDF 或图片资料仍依赖 OCR Provider，默认 mock OCR 不代表真实识别图片文字。

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

## 本地启动前端 H5

```bash
cd fantasy-role-ai/frontend
npm install
npm run dev:h5
```

默认 H5 地址通常为：

```text
http://127.0.0.1:5173
```

## 构建微信小程序

```bash
cd fantasy-role-ai/frontend
npm run build:mp-weixin
```

构建后用微信开发者工具导入 `frontend/dist/build/mp-weixin`。当前小程序登录只是预留，不会调用微信真实接口。

## 运行自动化测试

先启动后端，再运行：

```bash
cd fantasy-role-ai
python tests/run_backend_smoke.py
python tests/run_project_isolation.py
python tests/run_safety_checks.py
python tests/run_candidate_extraction_checks.py
```

测试报告输出到 `tests/reports/`。该目录是本地运行产物，不进入交付 zip。

## 配置 `.env`

复制 `.env.example` 为 `.env` 后按需修改。真实密钥只允许放在部署环境或本地 `.env`，不要提交或打包。

## 切换模型 Provider

关键变量：

```env
LLM_PROVIDER=mock
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=mock-model
```

未配置 `LLM_API_KEY` 或调用失败时自动 fallback 到 mock。

## 切换 OCR Provider

关键变量：

```env
OCR_PROVIDER=mock
OCR_LANG=ch
```

`paddleocr` 为可选能力，未安装时不影响后端启动。

## 切换图片生成 Provider

关键变量：

```env
IMAGE_PROVIDER=mock
IMAGE_API_KEY=
IMAGE_BASE_URL=
IMAGE_MODEL=mock-image-model
```

当前默认 mock，不调用真实绘图服务。

## 切换 Storage Provider

关键变量：

```env
STORAGE_PROVIDER=local
STORAGE_ENDPOINT_URL=
STORAGE_BUCKET=
STORAGE_PUBLIC_BASE_URL=
```

当前默认 local uploads。生产环境建议接对象存储，并配置 HTTPS public URL。

## 上线前还缺什么

- 正式数据库和备份策略
- 正式对象存储
- HTTPS 域名与 CORS 白名单
- 正式微信登录与用户协议
- 隐私政策与内容安全审核服务
- 关闭生产环境 debug 输出
- 迁移或禁止访问 `user_id=null` 的 legacy 数据
- 更完整的 CI / E2E / 安全审计
# v0.18.3-rc1 交付补充：LLM-first 剧本理解

本版本新增大模型优先的剧本理解链路，但仍不要求真实 API Key。若没有 Key，系统使用规则 fallback，并在前端和接口中明确提示“结果仅供测试”。该能力用于减少角色误识别、关系误判和剧透混入，不代表已经做到完美商业剧本理解。

使用建议：

1. 在项目详情页上传多文件资料包并解析。
2. 在“AI 理解剧本资料”区域填写可选的文件归属角色 / 文档范围提示。
3. 点击“让 AI 理解剧本资料”。
4. 检查候选、关系和剧透摘要。
5. 先确认候选和关系，再批量生成数字人。
