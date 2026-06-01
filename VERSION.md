# 幻梦数字人版本信息

- 当前版本：`v0.18.3-rc1`
- 项目名称：幻梦数字人
- 当前定位：MVP Release Candidate
- 交付日期：2026-05-31

## 已完成阶段

- 第 0-17 阶段：项目骨架、解析、Profile、Chat Engine、Multi-LLM、RAG 骨架、长期记忆、角色调教、OCR、项目隔离、候选、关系图、PetAsset、用户隔离、存储部署骨架、小程序骨架、安全合规、自动化测试。
- v0.18.1-rc1：修复角色卡片跳转 `character_id=[object Object]`。
- v0.18.2-fixed：增强 evidence-driven 剧本资料识别、候选分层、X的Y 归属、候选质量测试。
- v0.18.3-rc1：新增 LLM-first 剧本理解与角色生成链路。

## v0.18.3-rc1 本次更新

- 新增 LLM-first Script Understanding 总控服务。
- 新增 Corpus Analyzer、Character Extractor、Character Merger、Relationship Extractor、Profile Builder、Spoiler Classifier 服务骨架。
- 新增结构化 LLM 客户端，支持当前 `openai_compatible` Provider；无 API Key 或调用失败时明确回退 `rule_fallback`。
- 新增 LLM 调用日志表 `llm_extraction_runs` 和分析任务表 `script_analysis_jobs`。
- 新增 Prompt 模板目录 `backend/app/prompts/`，约束 JSON 输出、证据驱动、避免全文复述、剧透保护和角色本视角。
- 新增 `/api/projects/{project_id}/script-intelligence/llm-analyze`、status、result、confirm 接口。
- 项目详情页新增“AI 理解剧本资料”区域，展示隐私/版权提示、文件归属提示、候选、关系、剧透摘要和 fallback 状态。
- 新增 LLM-first 和 Prompt 模板自动化测试。

## 当前仍是 mock / 骨架的能力

- 未配置真实 API Key 时不调用真实模型，使用 MockLLMProvider 或 rule_fallback。
- LLM-first 只发送摘要和证据，不无限制发送完整剧本文本。
- OCR、图片生成、内容安全、微信登录仍为 Provider / mock / 规则骨架。
- 当前不是模型训练、微调、LoRA，也不是正式微信上线版本。

## 不包含

- 不包含任何真实 API Key、云服务密钥或微信密钥。
- 不包含正式微信登录、支付、正式上线部署。
- 不包含真实模型训练、向量数据库、完整商业内容审核服务。
