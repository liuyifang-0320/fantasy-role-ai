# LLM-first 剧本理解设计

## 目标

v0.18.3-rc1 将剧本资料识别从“规则优先”升级为“LLM-first + 规则兜底”。系统不再把短词命中直接当成人物，而是先构建文档摘要、chunk 摘要和证据集合，再交给结构化 LLM 复核；没有 API Key 或调用失败时使用 rule_fallback，并明确提示结果仅供测试。

## 总体流程

1. 多文件资料包上传并解析为 ParsedDocument。
2. 文本清洗、文档分层、script_chunks 生成。
3. Corpus Analyzer 构建资料包清单：文件名、长度、preview、chunk 摘要、文档类型提示、角色本归属提示。
4. Character Extractor 根据证据提取角色候选。
5. Character Merger 合并同名、别名和 OCR 变体，处理 `X的Y` 归属。
6. Relationship Extractor 抽取干净关系短句。
7. Profile Builder 生成角色档案草案。
8. Spoiler Classifier 标注 none / mild / heavy 与 visibility。
9. 用户在项目详情页确认候选和关系后，再批量生成数字人。

## StructuredLLMClient

`backend/app/services/structured_llm_client.py` 统一处理：

- 使用当前 `openai_compatible` 配置调用模型。
- 输入长度裁剪，不发送完整商业剧本文本。
- 提取 JSON / 处理 markdown fenced JSON。
- 失败时回退 rule_fallback。
- 写入 `llm_extraction_runs`，只保存 input/output preview，不保存 API Key。

## Prompt 模板

模板位于 `backend/app/prompts/`：

- `script_corpus_analyzer.md`
- `character_extractor.md`
- `character_merger.md`
- `relationship_extractor.md`
- `profile_builder.md`
- `spoiler_classifier.md`
- `roleplay_system_prompt.md`

所有抽取 Prompt 都要求严格 JSON 输出、不要复述完整剧本、证据不足时标记 `needs_human_review`。

## Fallback 策略

- 未配置 `LLM_API_KEY`：不调用真实模型，返回 `rule_fallback`。
- LLM 调用失败、超时或 JSON 解析失败：不阻塞主流程，回退规则结果。
- fallback 结果不声称真实 AI 理解，前端显示“结果仅供测试”。

## 隐私与版权

项目详情页会提示：AI 理解剧本资料会将部分解析文本片段发送给当前配置的大模型服务。请勿上传无授权商业剧本或敏感隐私资料。生产环境应配置隐私协议、用户协议和可审计的数据处理流程。

## 与 v0.18.2 的关系

v0.18.2 的 evidence-driven 规则链路仍保留，用于：

- 文档预处理；
- 候选证据收集；
- 无 Key / 失败时 fallback；
- 输出校验；
- 自动化测试。

v0.18.3 的重点是让真实 LLM API 在可用时参与结构化复核，而不是继续单靠正则和分词。
