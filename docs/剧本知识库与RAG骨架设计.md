# 剧本知识库与 RAG 骨架设计

## 1. 为什么需要知识库

角色档案适合描述稳定设定，但长剧本中的场景、对白、线索和事件细节需要另一层结构来承载。知识库的作用，就是把长文本整理成可以检索、可以过滤、可以注入 Prompt 的片段。

当前 `KnowledgeChunk` 仍属于“用户输入 + 上传文本规则抽取 + mock 补全”的工程骨架阶段。它不会让系统在未上传正式剧本时自动知道真实人物关系；开发自测中出现的阿奇、戴丽拉关系，来自测试 TXT 内容或手填 `relationship_hint`。

## 2. 当前为什么先不用向量数据库

第 5 阶段先验证工程管道，而不是追求最终检索效果：

- SQLite 已经存在，接入成本低
- 文本分块和 metadata 结构需要先稳定下来
- 关键词检索足够支撑 MVP 验证
- 后续升级到 embedding 和向量数据库时，可以沿用现有 chunk 结构

## 3. KnowledgeChunk 字段说明

- `chunk_id`：知识片段业务 ID
- `parsed_document_id`：来源解析文档
- `file_id`：来源上传文件
- `character_id`：已绑定角色时记录角色 ID
- `target_character_name`：目标数字人角色名
- `user_persona_name`：用户扮演身份
- `chapter`：章节标记
- `chunk_index`：文档内片段顺序
- `content`：完整片段
- `content_preview`：前 120 字摘要
- `keywords`：逗号分隔关键词
- `visibility`：`public / self_only / hidden / unknown`
- `source_type`：`parsed_text / mock_ocr / manual`

## 4. chunk 分块策略

- 目标长度约 500-800 个中文字符
- 优先保留自然段边界
- 长段落再按句子拆分
- 自动识别：
  - `第一幕`
  - `第二幕`
  - `第1章`
  - `第2章`
  - `Chapter 1`
- 隐藏信息段落与普通段落尽量分开，避免把可回答信息和剧透信息混在同一片段里

## 5. visibility 设计

- `public`：公共背景
- `self_only`：涉及目标角色自身视角
- `hidden`：含有真相、凶手、秘密等不应主动暴露的信息
- `unknown`：当前无法判断时的保留值

## 6. hidden / restricted 防剧透策略

- `hidden` chunk 默认不进入普通 Prompt
- 只有当用户明确追问 `真相 / 凶手 / 秘密` 时，检索器才会返回它
- 即使返回，也会标记 `restricted=true`
- PromptBuilder 对 `restricted` 片段只写入“用于判断是否保留悬念”的说明，不把原文直接送入可自由复述区域

## 7. 关键词检索策略

当前检索分两步：

1. 优先依据当前 `character_id` 过滤候选 chunk
2. 用 SQLite 候选集加 Python 轻量打分：
   - query 词命中 `content`
   - query 词命中 `keywords`
   - 角色名命中
   - 用户身份命中

最终按分数倒序返回前 N 个片段。

## 8. 检索范围与串库风险控制

不能只按角色名检索。剧本杀项目里很容易出现同名角色、不同剧本复用角色名或测试数据残留。如果只使用 `target_character_name == 当前角色名`，就可能把旧剧本、未绑定片段或其他角色的知识混入当前聊天，造成串剧本、串资料和剧透风险。

第 5.1 阶段采用以下规则：

- 如果当前 `character_id` 已有绑定 chunk，只检索 `character_id == 当前角色` 的片段，`retrieval_scope = character_bound`
- 只有当前角色没有任何绑定 chunk 时，才 fallback 到 `character_id is null` 且 `target_character_name == 当前角色名` 的历史未绑定片段，`retrieval_scope = fallback_by_character_name`
- 如果没有候选片段，`retrieval_scope = none`
- 对完全相同的 `content` 做去重，优先保留当前角色绑定片段，再按 score 排序

`fallback_by_character_name` 只是兼容旧数据和手动构建知识库的过渡策略，不应作为多剧本正式检索方案。

重建 chunk 时按 `parsed_document_id + character_id` 范围清理；未绑定 chunk 只替换未绑定旧片段，当前角色绑定 chunk 只替换当前角色旧片段，便于暴露并控制历史未绑定数据的串库风险。

## 9. 如何注入 PromptBuilder

PromptBuilder 新增：

- `knowledge_prompt`
- `retrieved_chunk_count`
- `retrieved_chunks_debug`
- `retrieval_scope`

系统提示词同时增加：

- 可参考剧本资料
- 资料不足时不得编造
- hidden / restricted 内容不得直接剧透
- 用户追问真相时应保留悬念

## 10. 后续如何升级

后续可以在不推翻当前结构的前提下继续升级：

- 为 chunk 生成 embedding
- 接入 `pgvector`
- 或切换到 `Qdrant / Milvus`
- 将当前关键词分数与向量相似度融合
- 加入更细粒度的角色视角、时间线和权限控制
