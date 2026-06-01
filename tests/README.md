# 自动化验收脚本

本目录存放项目级验收脚本，用于每个阶段交付前快速回归核心接口。当前脚本只使用 Python 标准库，不依赖 pytest 或 requests。

## 运行前提

必须先启动后端：

```bash
cd fantasy-role-ai/backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

默认测试地址是 `http://127.0.0.1:8000`，也可以用 `--base-url` 指定。

## 推荐运行顺序

```bash
cd fantasy-role-ai
python tests/run_backend_smoke.py
python tests/run_project_isolation.py
python tests/run_safety_checks.py
python tests/run_candidate_extraction_checks.py
```

也可以运行：

```bash
scripts/run_tests.bat
```

或：

```bash
sh scripts/run_tests.sh
```

## 后端 Smoke Test

```bash
python tests/run_backend_smoke.py
```

覆盖健康检查、用户隔离、项目创建、文件上传与解析、角色生成、知识库命中、聊天、记忆、安全、PetAsset、Storage/OCR/Image 状态接口。

报告输出：

```text
tests/reports/backend_smoke_report.json
```

## 项目隔离测试

```bash
python tests/run_project_isolation.py
```

该测试不只检查“不命中其他项目资料”，也检查“必须命中当前项目自己的正确资料”：

- 项目 A 必须命中“戴丽拉 / 情侣”，且不能命中“小雪 / 宿敌”。
- 项目 B 必须命中“小雪 / 宿敌”，且不能命中“戴丽拉 / 情侣”。
- `retrieval_project_scope` 必须为 `project_bound`。

报告 detail 会包含 `retrieved_chunk_count`、`retrieved_chunks_preview`、`expected_keywords`、`forbidden_keywords`，方便排查检索质量。

报告输出：

```text
tests/reports/project_isolation_report.json
```

## 内容安全测试

```bash
python tests/run_safety_checks.py
```

覆盖普通输入、自伤输入、Prompt 注入、剧透追问、偏好疑问不保存、明确偏好保存。

报告输出：

```text
tests/reports/safety_report.json
```

## 候选抽取质量测试

```bash
python tests/run_candidate_extraction_checks.py
```

覆盖 v0.18.2 的 evidence-driven 角色候选链路：

- 两套不同人名测试集都能识别高置信 `person`。
- `X的声音 / X的照片` 不会被当成独立角色。
- 第一幕、线索、真相、主持人、玩家、资料、日记等功能词不会成为 `person`。
- 重复抽取不重复创建候选。
- `relationship_hints` 是短关系句。
- 低置信候选不能默认批量生成。
- v0.18.2-fixed 还会检查 `relationship_sentence` 单独命中不能成为高置信人物、reviewer 不停留在 `pending`、代词短语 / 抽象词 / 功能词 / `X的Y` 不成为人物候选。

报告输出：

```text
tests/reports/candidate_extraction_report.json
```

## 压缩包检查

```bash
python tests/run_package_check.py --zip fantasy-role-ai-v0.18.2-fixed.zip
```

检查交付包是否排除了 `node_modules`、构建目录、数据库、`.env`、真实上传文件、测试报告、IDE 配置和高风险密钥文件名等，并确认必要目录与文件存在。

报告输出：

```text
tests/reports/package_check_report.json
```

## 测试数据和清理

- 测试会在本地数据库创建 dev_mock 用户、项目、角色、聊天和记忆测试数据。
- 测试不会上传真实用户文件，只使用 `tests/test_data/` 或脚本内置测试文本。
- 如果需要干净测试，可以先删除 `backend/fantasy_role_ai.db` 后重启后端再运行脚本。
- `tests/reports/` 是本地测试产物，不应打包进交付 zip。

## API Key 说明

- 测试不需要真实 API Key。
- 测试不会调用真实 LLM。
- 测试不会调用真实 OCR、图片生成、微信登录或内容审核 API。
- 没有 API Key 时使用 mock provider。
# v0.18.3-rc1 测试补充

新增测试：

```bash
python tests/run_llm_first_script_understanding_checks.py
python tests/run_prompt_template_checks.py
```

`run_llm_first_script_understanding_checks.py` 覆盖 LLM-first 分析接口、无 API Key fallback、status/result/confirm、旧候选接口兼容和高置信垃圾候选控制。`run_prompt_template_checks.py` 检查 Prompt 模板是否要求严格 JSON、避免复述完整剧本、包含剧透保护和角色本视角要求。两者都不需要真实 API Key。
