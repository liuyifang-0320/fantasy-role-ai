# API 接口文档

## 目录索引

### 全局规则

- Base URL：`http://127.0.0.1:8000`
- 接口风格：REST API
- 所有业务接口都支持请求头 `X-User-Id`。
- 当前用户体系为 `dev_mock`，未传 `X-User-Id` 时默认使用 `dev_user`。
- `prompt_debug`、`provider_debug`、`memory_debug`、`safety_debug` 等调试输出受 `ENABLE_DEBUG_OUTPUT` 控制。
- 生产环境建议设置 `ENABLE_DEBUG_OUTPUT=false`。
- 未配置真实 API Key 时不会调用真实 LLM，默认使用 MockLLMProvider。
- v0.18.2 的 Script Intelligence Pipeline 是解析后的内部后处理链路，当前由候选抽取、角色生成和知识库构建流程触发，不单独暴露公共 API。

### 模块分组

#### Auth

- `GET /api/auth/me`
- `POST /api/auth/dev-login`
- `POST /api/auth/switch-dev-user`
- `POST /api/auth/wechat-login`

#### Projects

- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/{project_id}`
- `PATCH /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`

#### Files

- `POST /api/files/upload`
- `POST /api/files/{file_id}/parse`
- `GET /api/files/{file_id}/parsed`

#### Parsed Documents

- `GET /api/parsed-documents/{parsed_id}`

#### Profiles

- `POST /api/profiles/extract`
- `GET /api/profiles`
- `GET /api/profiles/{profile_id}`

#### Characters

- `POST /api/characters/generate`
- `GET /api/characters`
- `GET /api/characters/{character_id}`

#### Candidates

- `POST /api/projects/{project_id}/candidates/extract`
- `GET /api/projects/{project_id}/candidates`
- `GET /api/character-candidates/{candidate_id}`
- `PATCH /api/character-candidates/{candidate_id}`
- `DELETE /api/character-candidates/{candidate_id}`
- `POST /api/projects/{project_id}/characters/batch-generate`

#### Relationships

- `POST /api/projects/{project_id}/relationships/extract`
- `GET /api/projects/{project_id}/relationships`
- `GET /api/projects/{project_id}/relationships/graph`
- `GET /api/character-relationships/{relationship_id}`
- `PATCH /api/character-relationships/{relationship_id}`
- `DELETE /api/character-relationships/{relationship_id}`

#### Knowledge

- `POST /api/knowledge/build`
- `GET /api/knowledge/chunks`
- `GET /api/knowledge/chunks/{chunk_id}`
- `POST /api/knowledge/search`

#### Chat

- `POST /api/chat`
- `GET /api/chat/sessions/{session_id}/messages`
- `GET /api/chat/characters/{character_id}/sessions`

#### Memory

- `GET /api/memory/{character_id}`
- `POST /api/memory/update`
- `PATCH /api/memory/{memory_id}`
- `DELETE /api/memory/{memory_id}`
- `GET /api/memory/{character_id}/debug`

#### Settings

- `GET /api/characters/{character_id}/settings`
- `PATCH /api/characters/{character_id}/settings`
- `POST /api/characters/{character_id}/settings/reset`
- `GET /api/characters/{character_id}/settings/prompt-preview`

#### Pets / PetAssets

- `GET /api/pets/{pet_id}`
- `GET /api/characters/{character_id}/pet-assets`
- `POST /api/characters/{character_id}/pet-assets/generate`
- `PATCH /api/characters/{character_id}/pet-assets/{asset_id}/active`
- `GET /api/pet-assets/{asset_id}`

#### LLM / OCR / Image / Storage / Safety / System

- `GET /api/llm/status`
- `GET /api/ocr/status`
- `GET /api/image-generation/status`
- `GET /api/storage/status`
- `GET /api/safety/status`
- `GET /api/system/health`
- `GET /health`

#### User Data

- `GET /api/user-data/export`
- `DELETE /api/user-data/delete`

---

## 基础信息

- Base URL：`http://127.0.0.1:8000`
- 接口风格：REST API

## 推荐调用顺序

1. `POST /api/files/upload` 上传文件
2. `POST /api/files/{file_id}/parse` 解析文件
3. `GET /api/files/{file_id}/parsed` 查看解析结果
4. `POST /api/profiles/extract` 抽取角色设定档案
5. `POST /api/characters/generate` 生成数字人
6. `POST /api/knowledge/build` 构建剧本知识库
7. `POST /api/knowledge/search` 检索知识片段
8. `GET /api/characters/{character_id}/settings` 查看角色调教配置
9. `PATCH /api/characters/{character_id}/settings` 按需更新角色调教配置
10. `GET /api/characters` 查看聊天列表
11. `GET /api/llm/status` 查看当前模型接入状态
12. `GET /api/ocr/status` 查看当前 OCR Provider 状态
13. `POST /api/chat` 开始聊天

注意：

- `uploaded_file_ids` 必须来自 `/api/files/upload` 的真实返回结果。
- 在空数据库里直接使用示例值 `file_001`，如果该文件记录并不存在，会返回 `400`。
- 如果生成角色前文件还没有被显式解析，`POST /api/characters/generate` 会自动补做解析。
- 当前人物关系来自用户手填信息、上传文本规则抽取或开发自测 sample TXT；未上传正式剧本时，不代表系统已真实知道人物关系。
- 未配置 `LLM_API_KEY` 时不会调用真实模型，会使用 `MockLLMProvider` 规则测试回复。

## 1. 健康检查

### `GET /health`

返回：

```json
{
  "status": "ok",
  "message": "Fantasy Role AI backend is running"
}
```

## 2. 文件上传

### `POST /api/files/upload`

- 表单字段：`file`
- 支持：PDF / DOCX / TXT / PNG / JPG / JPEG

返回字段：

- `file_id`
- `filename`
- `file_type`
- `file_path`
- `upload_status`

## 3. 文件解析

### `POST /api/files/{file_id}/parse`

根据 `file_id` 解析已上传文件并保存解析结果。

返回：

```json
{
  "parsed_id": "parsed_001",
  "file_id": "file_001",
  "filename": "script.pdf",
  "file_type": "pdf",
  "parse_status": "success",
  "text_preview": "……",
  "word_count": 1234,
  "ocr_provider": "",
  "ocr_confidence": 0.0,
  "ocr_error": null
}
```

图片 PNG / JPG / JPEG 会通过 OCR Provider 解析：

- `ocr_provider=mock` 且 `parse_status=mock_ocr`：当前为 mock OCR，未真实识别图片文字。
- `ocr_provider=paddleocr` 且 `parse_status=success`：PaddleOCR 真实 OCR 成功。
- `ocr_error`：OCR fallback 或失败原因，不包含敏感信息。

### `GET /api/files/{file_id}/parsed`

返回该文件最近一次解析结果摘要。

### `GET /api/parsed-documents/{parsed_id}`

返回完整解析结果，包含：

- `raw_text`
- `text_preview`
- `word_count`
- `parse_status`
- `ocr_provider`
- `ocr_confidence`
- `ocr_error`

## 3.1 OCR 状态

### `GET /api/ocr/status`

返回当前 OCR Provider 配置与可用状态：

```json
{
  "ocr_provider": "mock",
  "active_provider": "mock",
  "paddleocr_available": false,
  "ocr_lang": "ch",
  "pdf_image_fallback_enabled": false
}
```

说明：

- 未配置真实 OCR 时，`active_provider=mock`。
- 配置 `OCR_PROVIDER=paddleocr` 但未安装 PaddleOCR 时，仍会自动回退 mock，不影响后端启动。
- 前端只展示 OCR 状态，不展示任何敏感信息。

## 4. 角色设定档案

### `POST /api/profiles/extract`

请求：

```json
{
  "parsed_document_ids": ["parsed_001"],
  "target_character_name": "阿奇",
  "user_persona_name": "戴丽拉",
  "relationship_hint": "情侣"
}
```

当前行为：

- 合并 `parsed_document_ids` 对应的 `raw_text`
- 使用规则抽取加 mock 补全生成 `CharacterProfile`
- 保存到 `character_profiles`
- 返回结构化角色设定档案

### `GET /api/profiles/{profile_id}`

返回单个角色设定档案。

### `GET /api/profiles`

返回所有角色设定档案列表。

## 5. 角色生成

### `POST /api/characters/generate`

请求：

```json
{
  "uploaded_file_ids": ["来自上传接口返回的 file_id"],
  "target_character_name": "阿奇",
  "user_persona_name": "戴丽拉",
  "relationship_hint": "情侣"
}
```

当前行为：

- 如果文件未解析，会先自动解析
- 自动先生成 `CharacterProfile`
- 角色生成仍是 mock，但优先参考 `CharacterProfile`
- 返回 `parsed_document_ids`
- 同时返回 `parsed_documents` 摘要列表，便于前端展示
- 返回 `profile_id`
- 返回完整 `profile`
- 返回 `knowledge_chunk_count`
- 返回 `knowledge_chunks_preview`

## 6. 角色列表

### `GET /api/characters`

返回数字人聊天列表，每项包含：

- 角色基础信息
- 用户扮演身份
- 关系字段
- 最近消息
- 更新时间
- Q版桌宠

## 7. 角色详情

### `GET /api/characters/{character_id}`

返回单个角色详情及桌宠信息。

## 8. 角色调教配置

当前角色调教配置是 Prompt-level customization，不是真正模型微调。

### `GET /api/characters/{character_id}/settings`

返回单个角色的调教配置。如果该角色还没有配置，后端会自动创建默认配置。

返回字段包括：

- `settings_id`
- `character_id`
- `display_name`
- `user_persona_name`
- `nickname_for_user`
- `relationship_with_user`
- `relationship_stage`
- `tone_style`
- `reply_length`
- `intimacy_mode`
- `spoiler_protection`
- `pet_enabled`
- `pet_position`
- `personality_override`
- `speaking_style_override`
- `custom_prompt_notes`
- `forbidden_topics`

### `PATCH /api/characters/{character_id}/settings`

支持局部更新角色调教配置。

请求示例：

```json
{
  "tone_style": "mature",
  "reply_length": "short",
  "nickname_for_user": "戴丽拉",
  "relationship_stage": "暧昧期",
  "spoiler_protection": true,
  "pet_enabled": false
}
```

可选值：

- `tone_style`：`gentle / cold / playful / mature / yandere_light / poetic / original`
- `reply_length`：`short / medium / long`
- `intimacy_mode`：`low / normal / high`
- `pet_position`：`bottom_right / bottom_left / floating`

### `POST /api/characters/{character_id}/settings/reset`

重置为默认配置。默认配置来自当前 Character 的角色名、用户身份、关系和关系阶段。

### `GET /api/characters/{character_id}/settings/prompt-preview`

返回当前配置将注入 Prompt 的预览文本：

```json
{
  "character_id": "char_001",
  "settings_id": "settings_001",
  "prompt_preview": "角色调教配置（Prompt-level customization，不是真正模型训练）：……"
}
```

## 9. 剧本知识库

### `POST /api/knowledge/build`

请求：

```json
{
  "parsed_document_ids": ["parsed_001"],
  "target_character_name": "阿奇",
  "user_persona_name": "戴丽拉",
  "character_id": "char_001"
}
```

功能：

- 对指定解析文档生成 `knowledge_chunks`
- 返回 `knowledge_chunk_count`
- 返回 `knowledge_chunks_preview`

### `GET /api/knowledge/chunks`

支持查询参数：

- `character_id`
- `parsed_document_id`
- `visibility`

### `GET /api/knowledge/chunks/{chunk_id}`

返回单个知识片段详情。

### `POST /api/knowledge/search`

请求：

```json
{
  "character_id": "char_001",
  "query": "阿奇和戴丽拉是什么关系？",
  "limit": 5
}
```

返回按得分排序的知识片段列表。

检索范围遵循当前角色优先策略：如果当前 `character_id` 已有绑定 chunk，只检索当前角色知识库；只有没有绑定 chunk 时，才按角色名兜底检索未绑定片段。返回项中的 `retrieval_scope` 可为 `character_bound / fallback_by_character_name / none`。

返回项示例：

```json
{
  "chunk_id": "chunk_001",
  "content_preview": "……",
  "content": "……",
  "score": 8,
  "visibility": "self_only",
  "restricted": false,
  "retrieval_scope": "character_bound"
}
```

## 10. 聊天

### `POST /api/chat`

请求：

```json
{
  "character_id": "char_001",
  "session_id": "session_001",
  "message": "阿奇，你还记得我吗？"
}
```

返回：

```json
{
  "reply": "戴丽拉，阿奇当然记得你。我们之间的情侣，不是一句话就会散掉的。",
  "pet_action": "shy",
  "memory_hint": "角色主动确认了与你的关系记忆。",
  "session_id": "session_001",
  "message_id": "msg_002",
  "prompt_debug": {
    "system_prompt_preview": "你正在扮演一个剧本角色……",
    "context_message_count": 0,
    "uses_character_profile": true,
    "uses_character_settings": true,
    "settings_prompt_preview": "角色调教配置（Prompt-level customization，不是真正模型训练）：……",
    "retrieval_scope": "character_bound",
    "retrieved_chunk_count": 1,
    "retrieved_chunks_preview": [
      {
        "chunk_id": "chunk_001",
        "visibility": "self_only",
        "content_preview": "……",
        "restricted": false
      }
    ],
    "active_memory_count": 1,
    "active_memories_preview": [
      {
        "memory_id": "mem_001",
        "memory_type": "user_preference",
        "content": "用户喜欢雨夜散步。",
        "importance": 3
      }
    ]
  },
  "memory_debug": {
    "created_count": 1,
    "candidates": [
      {
        "memory_type": "user_preference",
        "content": "用户喜欢雨夜散步。",
        "importance": 3,
        "saved": true,
        "reason": "用户明确表达偏好"
      }
    ]
  },
  "provider_debug": {
    "configured_provider": "mock",
    "provider": "mock",
    "model": "mock-model",
    "base_url_configured": false,
    "api_key_configured": false,
    "fallback": false,
    "fallback_reason": null
  }
}
```

说明：

- 当 `ENABLE_PROMPT_DEBUG=false` 时，`prompt_debug` 会返回 `null`
- `provider_debug` 只返回是否已配置，不返回真实 API Key
- `memory_debug` 来自当前规则版记忆抽取；只有用户明确陈述偏好时才会保存，偏好疑问句不会被当作事实记忆

### `GET /api/chat/sessions/{session_id}/messages`

返回某个会话的消息列表，按时间正序，包含 user 与 assistant 消息。

### `GET /api/chat/characters/{character_id}/sessions`

返回某个角色的会话列表，按最近更新时间倒序。

## 11. LLM 状态

### `GET /api/llm/status`

返回：

```json
{
  "configured_provider": "mock",
  "active_provider": "mock",
  "api_key_configured": false,
  "base_url_configured": false,
  "model": "mock-model",
  "api_style": "chat_completions",
  "prompt_debug_enabled": true
}
```

## 12. 查询记忆

### `GET /api/memory/{character_id}`

返回 active 记忆，按类型分区：

- `user_preference_memory`
- `relationship_memory`
- `story_interaction_memory`
- `emotional_state_memory`
- `custom_memory`

每条记忆包含：

- `memory_id`
- `memory_content`
- `memory_type`
- `importance`
- `source`
- `is_active`
- `created_at`
- `updated_at`

## 13. 更新记忆

### `POST /api/memory/update`

请求：

```json
{
  "character_id": "char_001",
  "memory_content": "戴丽拉喜欢雨夜散步。",
  "memory_type": "user_preference",
  "importance": 3
}
```

支持的 `memory_type`：

- `user_preference`
- `relationship`
- `story_interaction`
- `emotional_state`
- `custom`

### `PATCH /api/memory/{memory_id}`

编辑记忆内容、类型、重要度。

推荐请求：

```json
{
  "memory_content": "用户喜欢下雨天散步。",
  "memory_type": "user_preference",
  "importance": 4
}
```

兼容说明：

- 推荐使用 `memory_content` 更新记忆正文
- `content` 也可作为兼容字段传入，后端会统一写入 `Memory.content`
- 如果同时传入 `memory_content` 和 `content`，以后端优先使用 `memory_content`
- PATCH 成功后，返回结果中的 `memory.memory_content` 是更新后的内容

### `DELETE /api/memory/{memory_id}`

软删除记忆，将 `is_active` 设置为 `false`。软删除后的记忆不参与后续 Prompt 注入。

### `GET /api/memory/{character_id}/debug`

返回该角色全部记忆，包括 inactive，用于开发调试。

## 14. 查询桌宠

### `GET /api/pets/{character_id}`

返回：

- `character_id`
- `pet_name`
- `pet_avatar`
- `pet_status`
- `available_actions`
- `intimacy_level`

## 15. 更新桌宠动作

### `POST /api/pets/action`

请求：

```json
{
  "character_id": "char_001",
  "action": "happy"
}
```

支持动作：

- `idle`
- `happy`
- `shy`
- `thinking`
- `talking`
- `comfort`
- `surprised`

## 16. 剧本项目空间

第 9 阶段新增 `ScriptProject`，用于隔离不同剧本资料包。旧流程不传 `project_id` 仍然兼容。

### `POST /api/projects`

请求：

```json
{
  "title": "流浪叙事",
  "description": "一个关于阿奇和戴丽拉的剧本项目",
  "source_type": "upload"
}
```

返回项目详情和 summary。

### `GET /api/projects`

返回项目列表。每个项目包含 `project_id / title / description / source_type / cover_image / project_status / summary`。

### `GET /api/projects/{project_id}`

返回单个项目详情和 summary。summary 包括文件数量、解析文档数量、角色数量、知识片段数量和最近更新时间。

### `PATCH /api/projects/{project_id}`

支持更新 `title / description / source_type / cover_image / project_status`。

### `DELETE /api/projects/{project_id}`

软归档项目，设置 `project_status=archived`，不会物理删除资料。

## 17. project_id 相关接口变化

### 文件上传

`POST /api/files/upload` 新增可选表单字段：

- `project_id`

如果传入 `project_id`，文件会绑定该项目；项目不存在时返回错误。返回新增 `project_id`。

### 文件解析

`POST /api/files/{file_id}/parse`、`GET /api/files/{file_id}/parsed`、`GET /api/parsed-documents/{parsed_id}` 返回新增 `project_id`。

`ParsedDocument.project_id` 自动继承 `UploadedFile.project_id`。

### 角色生成

`POST /api/characters/generate` 请求新增可选：

```json
{
  "project_id": "project_001",
  "uploaded_file_ids": ["file_001"],
  "target_character_name": "阿奇",
  "user_persona_name": "戴丽拉",
  "relationship_hint": "情侣"
}
```

如果请求带 `project_id`：

- 生成的 `Character` 绑定该项目。
- 生成的 `CharacterProfile` 绑定该项目。
- 自动生成的 `KnowledgeChunk` 绑定该项目。
- 如果上传文件不属于该项目，会拒绝请求，避免跨项目混用资料。

返回新增 `project_id`。

### 知识库构建与查询

`POST /api/knowledge/build` 请求新增可选 `project_id`。如果请求带 `project_id`，会校验 `parsed_documents` 是否属于该项目。

`GET /api/knowledge/chunks` 查询参数新增 `project_id`。

`POST /api/knowledge/search` 请求新增可选 `project_id`。如果角色本身已绑定 `project_id`，检索以角色所属项目为准。

### 聊天 prompt_debug

`POST /api/chat` 的 `prompt_debug` 新增：

```json
{
  "project_id": "project_001",
  "retrieval_project_scope": "project_bound"
}
```

`retrieval_project_scope` 可选：

- `project_bound`：检索严格限制在角色所属项目内。
- `legacy_no_project`：旧角色没有项目，使用旧兼容逻辑。
- `none`：未命中可用项目范围。

注意：有 `project_id` 的角色不会跨项目检索同名角色知识片段。
## 第 10 阶段：项目内角色候选与批量生成

### POST /api/projects/{project_id}/candidates/extract

扫描指定项目下的 `parsed_documents`。v0.18.2 起优先调用 Script Intelligence Pipeline，完成文本清洗、文档分层、script chunk、证据驱动候选抽取、候选 reviewer 复核和关系短句抽取后写入 `character_candidates`。

响应示例：

```json
[
  {
    "candidate_id": "candidate_001",
    "project_id": "project_001",
    "name": "阿奇",
    "aliases": [],
    "identity_hint": "阿奇是项目资料中与关系线索相关的关键角色",
    "personality_hint": "带有情感牵连和故事感",
    "relationship_hints": ["阿奇和戴丽拉是情侣。"],
    "evidence": "阿奇：戴丽拉，你还记得我吗？ ...",
    "source_document_ids": ["parsed_001"],
    "confidence": 1.0,
    "candidate_type": "person",
    "source_types": ["dialogue_label", "relationship_sentence"],
    "evidence_spans": ["阿奇：戴丽拉，你还记得我吗？"],
    "dialogue_count": 1,
    "mention_count": 2,
    "relationship_evidence": ["阿奇和戴丽拉是情侣"],
    "confidence_level": "high",
    "needs_human_review": false,
    "reviewer_provider": "rule",
    "reviewer_status": "rule_fallback",
    "reviewer_reason": "对白标签和关系句提供强证据",
    "candidate_status": "pending",
    "created_at": "2026-05-22T00:00:00",
    "updated_at": "2026-05-22T00:00:00"
  }
]
```

重复抽取时，同一项目同名候选不会重复创建；`generated` 状态候选默认不覆盖。

候选不是简单分词结果，必须由证据驱动。`X的声音 / X的照片 / X的日记` 等结构不会创建独立人物候选；如果 `X` 已是高置信角色，会归属到 `X` 的 `evidence_spans`。LLM reviewer 只接收候选摘要和有限证据片段，没有 API Key 或调用失败时回退规则 reviewer。

### GET /api/projects/{project_id}/candidates

获取项目候选角色列表。

查询参数：

- `status`：可选，筛选 `pending / confirmed / ignored / generated / rejected`

### GET /api/character-candidates/{candidate_id}

获取单个候选角色详情。

### PATCH /api/character-candidates/{candidate_id}

编辑候选信息。

请求示例：

```json
{
  "name": "阿奇",
  "identity_hint": "旧街区叙事中的关键角色",
  "personality_hint": "带有情感牵连和故事感",
  "relationship_hints": ["阿奇和戴丽拉是情侣。"],
  "candidate_status": "confirmed"
}
```

可编辑字段：

- `name`
- `aliases`
- `identity_hint`
- `personality_hint`
- `relationship_hints`
- `display_name`
- `candidate_type`
- `confidence_level`
- `needs_human_review`
- `candidate_status`

### DELETE /api/character-candidates/{candidate_id}

将候选标记为 `ignored`，不物理删除。

### POST /api/projects/{project_id}/characters/batch-generate

根据项目内候选角色批量生成数字人。

请求示例：

```json
{
  "candidate_ids": ["candidate_001", "candidate_002"],
  "user_persona_name": "戴丽拉",
  "default_relationship_hint": "根据剧本资料生成",
  "relationship_overrides": {
    "candidate_001": "情侣"
  }
}
```

处理规则：

- 候选必须属于当前 `project_id`
- 只使用当前项目的上传资料和解析文档
- 每个角色复用现有单角色生成流程，自动生成 `CharacterProfile`、`KnowledgeChunk`、桌宠和默认角色调教配置
- `relationship_hint` 优先使用 `relationship_overrides`，其次使用候选 `relationship_hints`，最后使用 `default_relationship_hint`
- 已 `generated` 的候选会返回 `skipped`
- `ignored` 的候选会返回 `skipped`
- `candidate_type != person` 的候选会返回 `skipped`
- `confidence_level=medium/low` 且未被用户 `confirmed` 的候选会返回 `skipped`

响应示例：

```json
{
  "generated": [
    {
      "character_id": "char_001",
      "project_id": "project_001",
      "character_name": "阿奇",
      "profile_id": "profile_001",
      "knowledge_chunk_count": 3
    }
  ],
  "skipped": [
    {
      "candidate_id": "candidate_003",
      "name": "戴丽拉",
      "reason": "Candidate already generated"
    }
  ],
  "failed": []
}
```

批量生成不会破坏原有 `POST /api/characters/generate` 单角色生成接口。

## 第 11 阶段：项目内角色关系图

### POST /api/projects/{project_id}/relationships/extract

扫描指定项目下的 `parsed_documents`，使用规则抽取角色关系并写入 `character_relationships`。

响应示例：

```json
[
  {
    "relationship_id": "rel_001",
    "project_id": "project_001",
    "source_character_name": "阿奇",
    "target_character_name": "戴丽拉",
    "relation_type": "情侣",
    "relation_summary": "阿奇和戴丽拉是情侣",
    "evidence": "阿奇和戴丽拉是情侣。小雪和阿奇是宿敌。",
    "source_document_ids": ["parsed_001"],
    "confidence": 0.92,
    "relationship_status": "pending",
    "created_at": "2026-05-25T00:00:00",
    "updated_at": "2026-05-25T00:00:00"
  }
]
```

同项目内同一组关系不会重复创建；情侣、朋友、宿敌等对称关系会合并正反向。

### GET /api/projects/{project_id}/relationships

获取项目角色关系列表。

查询参数：

- `status`：可选，筛选 `pending / confirmed / ignored`

### GET /api/character-relationships/{relationship_id}

获取单条角色关系详情。

### PATCH /api/character-relationships/{relationship_id}

编辑关系。

请求示例：

```json
{
  "source_character_name": "阿奇",
  "target_character_name": "戴丽拉",
  "relation_type": "情侣",
  "relation_summary": "阿奇和戴丽拉是情侣。",
  "relationship_status": "confirmed"
}
```

可编辑字段：

- `source_character_name`
- `target_character_name`
- `relation_type`
- `relation_summary`
- `relationship_status`

### DELETE /api/character-relationships/{relationship_id}

将关系标记为 `ignored`，不物理删除。

### GET /api/projects/{project_id}/relationships/graph

返回适合前端绘图的数据。

响应示例：

```json
{
  "nodes": [
    {"id": "阿奇", "label": "阿奇"},
    {"id": "戴丽拉", "label": "戴丽拉"}
  ],
  "edges": [
    {
      "id": "rel_001",
      "source": "阿奇",
      "target": "戴丽拉",
      "label": "情侣",
      "summary": "阿奇和戴丽拉是情侣。"
    }
  ]
}
```

### POST /api/chat 调试字段补充

`prompt_debug` 增加：

```json
{
  "active_relationship_count": 2,
  "relationships_preview": [
    {
      "relationship_id": "rel_001",
      "source_character_name": "阿奇",
      "target_character_name": "戴丽拉",
      "relation_type": "情侣",
      "relation_summary": "阿奇和戴丽拉是情侣。"
    }
  ]
}
```

当 `ENABLE_PROMPT_DEBUG=false` 时，`prompt_debug` 仍可能为 `null`。

## 第 12 阶段：Q版桌宠资产系统

### GET /api/characters/{character_id}/pet-assets

返回某个角色的全部桌宠资产，按 active 优先、创建时间倒序排列。

响应字段包括：

- `asset_id`
- `project_id`
- `character_id`
- `pet_id`
- `asset_type`
- `style`
- `prompt`
- `negative_prompt`
- `image_url`
- `local_path`
- `generation_provider`
- `generation_status`
- `is_active`

### POST /api/characters/{character_id}/pet-assets/generate

mock 生成新的桌宠资产，并默认设为 active。

请求示例：

```json
{
  "style": "q_chibi",
  "prompt_override": "更像神社少女，蓝紫色调"
}
```

当前默认使用 `MockImageProvider`，不会调用真实图片生成 API。

### PATCH /api/characters/{character_id}/pet-assets/{asset_id}/active

将某个桌宠资产设置为当前 active。接口会把同角色其他资产的 `is_active` 置为 `false`。

### GET /api/pet-assets/{asset_id}

获取单个桌宠资产详情。

### GET /api/image-generation/status

查看图片生成 Provider 状态。

响应示例：

```json
{
  "image_provider": "mock",
  "active_provider": "mock",
  "api_key_configured": false,
  "base_url_configured": false,
  "model": "mock-image-model",
  "timeout_seconds": 60
}
```

注意：接口不会返回任何 API Key。

### 角色生成接口补充

`POST /api/characters/generate` 与 `POST /api/projects/{project_id}/characters/batch-generate` 返回中增加：

```json
{
  "pet_assets": [
    {
      "asset_id": "pet_asset_001",
      "style": "q_chibi",
      "image_url": "/static/mock/generated-q.png",
      "generation_provider": "mock",
      "generation_status": "mock",
      "is_active": true
    }
  ],
  "active_pet_asset": {
    "asset_id": "pet_asset_001",
    "style": "q_chibi",
    "image_url": "/static/mock/generated-q.png",
    "generation_provider": "mock",
    "generation_status": "mock",
    "is_active": true
  }
}
```
## 第 13 阶段：用户体系与数据隔离

### 全局请求头

所有业务接口都支持开发环境用户请求头：

```http
X-User-Id: user_001
```

当前阶段这是 `dev_mock` 用户机制，不是正式微信登录或手机号登录。未传 `X-User-Id` 时后端默认使用 `dev_user`。后端不会返回或保存真实敏感登录凭证。

数据访问规则：

- 新建项目、文件、解析文档、角色、知识库、聊天、记忆、调教配置、候选、关系和桌宠资产都会写入当前 `user_id`。
- 查询接口默认只返回当前用户数据。
- 如果资源属于其他 `user_id`，返回 `403 Forbidden`。
- 旧数据 `user_id=null` 在开发阶段兼容访问，上线前应迁移或关闭该兼容策略。

### `GET /api/auth/me`

获取当前用户。

返回示例：

```json
{
  "user_id": "dev_user",
  "nickname": "开发测试用户",
  "avatar": "",
  "auth_provider": "dev_mock",
  "user_status": "active",
  "created_at": "2026-05-25T00:00:00",
  "updated_at": "2026-05-25T00:00:00"
}
```

### `POST /api/auth/dev-login`

开发环境创建或返回 mock 用户。

请求：

```json
{
  "nickname": "测试用户A"
}
```

返回：同 `GET /api/auth/me`。

说明：该接口只用于开发测试，不代表正式登录。

### `POST /api/auth/switch-dev-user`

开发环境切换当前 mock 用户。

请求：

```json
{
  "user_id": "user_001"
}
```

返回：同 `GET /api/auth/me`。

### 既有接口的 user_id 行为

- `POST /api/projects`：创建项目时写入当前 `user_id`。
- `GET /api/projects`：只返回当前用户项目和开发兼容的旧数据。
- `POST /api/files/upload`：上传文件写入当前 `user_id`，并校验 `project_id` 归属。
- `POST /api/characters/generate`：生成角色、Profile、KnowledgeChunk、Pet、PetAsset 时写入当前 `user_id`。
- `GET /api/characters`、`GET /api/characters/{character_id}`：按当前用户隔离。
- `POST /api/chat`：聊天会话与消息写入当前角色所属 `user_id`，跨用户访问会被拒绝。
- `GET /api/chat/sessions/{session_id}/messages`：只能读取当前用户会话。
- `GET /api/memory/{character_id}`、`PATCH /api/memory/{memory_id}`、`DELETE /api/memory/{memory_id}`：只能操作当前用户记忆。
- `GET /api/characters/{character_id}/pet-assets`、`GET /api/pet-assets/{asset_id}`：只能读取当前用户桌宠资产。
- 候选角色、角色关系、知识库构建和检索均同时遵守 `user_id` 与 `project_id` 隔离。
## 第 14 阶段：存储与部署生产化骨架

### `GET /api/storage/status`

查看当前存储 Provider 配置状态。

返回示例：

```json
{
  "storage_provider": "local",
  "active_provider": "local",
  "bucket_configured": false,
  "endpoint_configured": false,
  "public_base_url_configured": false,
  "max_upload_size_mb": 50,
  "allowed_upload_types": ["pdf", "docx", "txt", "png", "jpg", "jpeg"]
}
```

说明：

- 不返回 `STORAGE_ACCESS_KEY_ID` 或 `STORAGE_SECRET_ACCESS_KEY`。
- `STORAGE_PROVIDER=s3_compatible` 但配置不完整时会 fallback 到 local。
- 当前 S3-compatible / custom 是生产化骨架，不要求真实云上传。

### `GET /api/system/health`

查看系统健康状态。

返回示例：

```json
{
  "status": "ok",
  "database": "ok",
  "storage": "local",
  "llm_provider": "mock",
  "ocr_provider": "mock",
  "image_provider": "mock",
  "timestamp": "2026-05-26T00:00:00"
}
```

说明：

- 该接口不会调用真实 LLM。
- 仅检查数据库连通性和 Provider 配置状态。

### `POST /api/files/upload` 存储字段

上传接口在原有字段基础上新增：

```json
{
  "storage_provider": "local",
  "storage_key": "file_001_script.txt",
  "public_url": "/uploads/file_001_script.txt",
  "content_type": "text/plain",
  "file_size": 128
}
```

字段说明：

- `storage_provider`：实际保存文件的 Provider。
- `storage_key`：存储系统内的 key。
- `public_url`：前端可访问路径或 URL。
- `content_type`：上传文件 MIME 类型。
- `file_size`：文件大小，单位 byte。

上传限制：

- 文件类型由 `ALLOWED_UPLOAD_TYPES` 控制，默认 `pdf,docx,txt,png,jpg,jpeg`。
- 文件大小由 `MAX_UPLOAD_SIZE_MB` 控制，默认 50 MB。

## 第 15 阶段：微信小程序适配预留接口

### 全局请求说明

前端 H5 与微信小程序端均通过 `frontend/src/api/index.js` 统一发起请求，baseURL 来自 `frontend/src/config/env.js`。所有业务请求继续自动携带：

```http
X-User-Id: dev_user
```

当前仍为开发环境 `dev_mock` 用户体系，不是正式微信登录。小程序端开发时需要将 baseURL 占位地址替换为开发机局域网 IP 或正式 HTTPS 域名。

### `POST /api/auth/wechat-login`

微信登录预留接口。当前阶段不调用微信真实接口、不请求 `appid / secret`、不伪造 `openid`。

请求示例：

```json
{
  "code": "wx_login_code"
}
```

当前返回：

```json
{
  "status": "not_implemented",
  "message": "微信登录接口已预留，正式上线阶段接入 code2session。"
}
```

说明：

- 该接口只是为正式小程序登录链路预留。
- 后续正式上线阶段才会接入微信 `code2session`。
- `.env.example` 只保留 `WECHAT_APPID` 和 `WECHAT_SECRET` 空占位，不允许提交真实密钥。
- 当前用户中心的“微信登录（预留）”按钮只显示提示，不会创建真实微信用户。

## 第 16 阶段：内容安全与隐私合规

### 全局说明

第 16 阶段新增的是规则版内容安全与隐私合规骨架，不是真实第三方内容审核服务。当前会对用户聊天输入、模型/Mock 输出、角色调教配置和上传文本预览做基础规则检查，并把命中情况写入 `safety_logs`。

生产环境建议设置：

```env
ENABLE_DEBUG_OUTPUT=false
```

当 `ENABLE_DEBUG_OUTPUT=false` 时，`prompt_debug`、`memory_debug`、`safety_debug` 会返回 `null` 或不返回，`provider_debug` 只保留简化信息，避免把调试细节暴露给前端用户。

### `GET /api/safety/status`

查看当前内容安全配置状态。

响应示例：

```json
{
  "safety_mode": "rule",
  "strict_level": "normal",
  "debug_output_enabled": true,
  "user_data_export_enabled": true,
  "user_data_delete_enabled": true,
  "privacy_contact_email": ""
}
```

说明：

- `safety_mode=rule` 表示使用本地规则审核。
- `mock_provider` 是后续接入真实审核 Provider 前的预留模式。
- 接口不返回任何 API Key 或第三方服务密钥。

### `POST /api/chat` 内容安全返回字段

聊天接口保持原有请求结构不变。响应中新增 `safety_debug`，并且 `prompt_debug` 新增 `uses_safety_prompt`。

响应片段示例：

```json
{
  "reply": "戴丽拉，先别一个人撑着。如果你现在真的有伤害自己的念头，请马上联系身边可信任的人，或拨打当地紧急求助电话。我会陪你把这一刻先稳住。",
  "pet_action": "comfort",
  "prompt_debug": {
    "uses_safety_prompt": true
  },
  "safety_debug": {
    "user_input_action": "block",
    "assistant_output_action": "allow",
    "matched_categories": ["self_harm"]
  }
}
```

安全行为说明：

- `allow`：允许继续正常聊天。
- `warn`：允许继续聊天，但会在 Prompt 中加入安全提醒。
- `block`：不调用 LLM Provider，直接返回安全回复。
- `replace`：模型或 Mock 输出命中风险后，用安全回复替换。

当前规则覆盖：

- `self_harm`：自伤、自杀风险。
- `sexual_explicit`：色情露骨内容。
- `violence`：暴力危险内容。
- `illegal`：违法危险指导。
- `privacy`：身份证、银行卡、验证码、密码、手机号、家庭住址等敏感信息。
- `dependency_risk`：过度依赖风险。
- `spoiler_sensitive`：凶手、真相、结局等剧透敏感追问。
- `prompt_injection`：索要系统提示词、要求忽略指令等 Prompt 注入。

### 角色调教配置安全错误

`PATCH /api/characters/{character_id}/settings` 会检查：

- `custom_prompt_notes`
- `forbidden_topics`
- `personality_override`
- `speaking_style_override`

如果配置明显要求色情、违法、自伤鼓励、泄露系统 Prompt 等内容，接口返回 `400`。

错误示例：

```json
{
  "detail": "角色调教配置包含不适合保存的安全风险内容"
}
```

说明：

- 角色调教仍然是 Prompt-level customization，不是真正模型训练。
- 角色调教不能用于色情、违法、自伤鼓励或诱导用户病态依赖。

### 文件解析安全字段

文件解析相关接口会在 `ParsedDocument` 返回中增加：

```json
{
  "safety_warning": "上传文本命中隐私或剧透敏感规则，请注意资料使用边界。",
  "safety_categories": ["spoiler_sensitive", "privacy"]
}
```

涉及接口：

- `POST /api/files/{file_id}/parse`
- `GET /api/files/{file_id}/parsed`
- `GET /api/parsed-documents/{parsed_id}`

说明：

- 当前只扫描 `raw_text` 前部内容作为规则提醒。
- 剧本杀文本中出现“凶手 / 真相”等词不会阻止解析，但会标记为 `spoiler_sensitive`。
- 该能力不是正式内容审核服务。

### `GET /api/user-data/export`

导出当前 `X-User-Id` 用户的数据摘要 JSON。

响应示例：

```json
{
  "exported_at": "2026-05-28T00:00:00",
  "user": {
    "user_id": "dev_user",
    "nickname": "开发测试用户",
    "auth_provider": "dev_mock",
    "user_status": "active"
  },
  "projects": [],
  "characters": [],
  "memories": [],
  "summary": {
    "project_count": 0,
    "character_count": 0,
    "memory_count": 0,
    "active_memory_count": 0,
    "chat_session_count": 0,
    "chat_message_count": 0,
    "pet_asset_count": 0
  }
}
```

说明：

- 只导出当前用户的数据摘要。
- 当前不导出上传文件二进制。
- 聊天消息当前导出数量摘要，不导出完整长聊天记录。
- 如果 `ENABLE_USER_DATA_EXPORT=false`，返回 `403`。

### `DELETE /api/user-data/delete`

对当前 `X-User-Id` 用户执行开发版软删除 / 归档。

响应示例：

```json
{
  "success": true,
  "message": "当前用户数据已执行开发版软删除/归档。",
  "user_id": "dev_user",
  "archived_project_count": 1,
  "deactivated_memory_count": 2
}
```

当前行为：

- 将当前用户的项目设置为 `archived`。
- 将当前用户的记忆设置为 `is_active=false`。
- 将当前用户状态设置为 `disabled`。
- 不物理删除上传文件。

隔离规则：

- 只操作当前 `X-User-Id` 用户的数据。
- `user_A` 删除数据不会影响 `user_B`。
- 如果 `ENABLE_USER_DATA_DELETE=false`，返回 `403`。
## v0.18.2-fixed Candidate Reviewer 说明

角色候选相关接口的返回中，`reviewer_status` 不应长期停留在 `pending`：

- 真实 `openai_compatible` reviewer 成功时：`reviewer_provider=openai_compatible`，`reviewer_status=success`。
- 没有 API Key、模型未配置或调用失败时：同步回退规则复核，`reviewer_provider=rule`，`reviewer_status=rule_fallback`。
- 用户在前端手动确认候选时，后端会把复核状态标记为 `manual`。

批量生成接口默认只放行：

- `candidate_type=person`
- `confidence_level=high`
- `needs_human_review=false`
- `reviewer_status` 为 `success / rule_fallback / manual`

或用户已手动 `confirmed` 的人物候选。单独来自 `relationship_sentence` 的候选会保持中低置信并需要人工确认，不能直接生成。
# v0.18.3 Script Intelligence / LLM-first 接口

所有接口继续支持 `X-User-Id`，并遵守 user_id / project_id 隔离。未配置真实 `LLM_API_KEY` 时不会调用真实模型，返回 `provider=rule_fallback` 和明确 fallback 提示。

## POST /api/projects/{project_id}/script-intelligence/llm-analyze

请求：

```json
{
  "parsed_document_ids": ["parsed_001"],
  "force_rebuild": false,
  "use_llm": true,
  "spoiler_mode": "non_spoiler",
  "owner_hints": [
    {
      "parsed_document_id": "parsed_001",
      "owner_character_name": "阿奇",
      "document_scope": "character_book"
    }
  ]
}
```

返回：

```json
{
  "analysis_id": "analysis_001",
  "status": "success/fallback/failed",
  "summary": {
    "provider": "openai_compatible/rule_fallback",
    "message": "当前未配置真实 LLM API，已使用规则 fallback，结果仅供测试。",
    "characters": [],
    "relationships": [],
    "spoiler_summary": {}
  }
}
```

## GET /api/projects/{project_id}/script-intelligence/status

返回最近一次分析任务状态、provider、model、文档数、chunk 数、候选数、关系数和 warnings。

## GET /api/projects/{project_id}/script-intelligence/result

返回最近一次分析结果，包括 corpus analysis、候选、关系、profile 草案、剧透摘要和 warnings。

## POST /api/projects/{project_id}/script-intelligence/confirm

用于用户确认 LLM-first 分析结果。

```json
{
  "confirmed_candidate_ids": ["candidate_001"],
  "rejected_candidate_ids": [],
  "confirmed_relationship_ids": ["rel_001"],
  "rejected_relationship_ids": [],
  "spoiler_mode": "non_spoiler"
}
```
