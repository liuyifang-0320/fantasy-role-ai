# Q版桌宠资产与形象生成设计

## 目标

第 12 阶段把早期的简单 Q版桌宠 mock 升级为 `PetAsset` 资产系统。角色生成后会自动创建一个默认桌宠资产，资产绑定 `project_id / character_id / pet_id`，聊天页优先使用当前 active 桌宠资产。

当前阶段不是真实 AI 绘图，不做 3D 建模，不做 Live2D 绑定，也不做 Spine 动画引擎。没有图片生成 API 配置时，系统始终使用 mock 图片。

## PetAsset 字段

- `asset_id`：桌宠资产业务 ID。
- `project_id`：所属剧本项目，可为空兼容旧流程。
- `character_id`：所属数字人角色。
- `pet_id`：关联原有 Q版桌宠记录。
- `asset_type`：资产类型，当前主要使用 `static_image`，预留 `multi_pose_pack / live2d_placeholder / spine_placeholder / vrm_placeholder`。
- `style`：形象风格，支持 `q_chibi / anime_chibi / soft_dream / mystery_dark / cute_pet`。
- `prompt`：生成提示词。
- `negative_prompt`：负面提示词。
- `image_url`：前端可访问图片 URL。
- `local_path`：本地资源路径。
- `generation_provider`：生成 Provider，当前为 `mock`，预留 `custom`。
- `generation_status`：生成状态，支持 `pending / success / failed / mock`。
- `is_active`：当前角色正在使用的桌宠资产。

## ImageGenerationProvider

`ImageGenerationProvider` 统一封装图片生成接口：

```python
generate_image(prompt, negative_prompt, style) -> {
  "provider": "mock / image_api / custom",
  "status": "success / mock / failed",
  "image_url": "...",
  "local_path": "...",
  "error": null
}
```

### MockImageProvider

默认启用，不依赖外部服务，返回 `/static/mock/generated-q.png` 或 `/static/mock/aqi-q.png` 这类已有测试图片。Mock 结果只代表流程占位，不代表真实 AI 绘图。

### CustomImageProvider

当前仅保留骨架，读取：

- `IMAGE_PROVIDER`
- `IMAGE_API_KEY`
- `IMAGE_BASE_URL`
- `IMAGE_MODEL`
- `IMAGE_TIMEOUT_SECONDS`

配置不完整时自动回退 mock。后续接具体图片模型服务时，可以在该 Provider 内适配厂商协议。不要把真实 API Key 写进代码、文档或压缩包。

## Prompt 生成策略

`build_pet_prompt` 会参考：

- 角色名
- 角色身份
- 性格
- 说话风格
- 角色调教配置中的性格 / 说话风格覆盖
- 用户选择的桌宠风格

负面提示词默认包含：恐怖、血腥、色情、真实人物肖像、低俗元素等边界。

## 生成流程

1. 生成 `Character`。
2. 生成原有 `Pet`。
3. 自动创建默认 `PetAsset`。
4. 默认资产 `is_active=true`。
5. 角色生成接口返回 `pet_assets / active_pet_asset`。
6. 聊天页优先使用 `active_pet_asset.image_url`，没有时回退到 `pet.pet_avatar`。

## 前端使用

- 生成结果页展示当前 active 桌宠资产。
- 角色详情页展示 active 桌宠信息，并提供“管理桌宠形象”入口。
- 桌宠资产管理页支持查看资产列表、mock 重新生成、切换 active。
- 设置页展示图片生成 Provider 状态。

## 后续升级方向

- 接入真实 AI 绘图服务。
- 生成多表情 / 多姿势包。
- 将 `multi_pose_pack` 与聊天动作 `pet_action` 绑定。
- 增加 Live2D / Spine / VRM / 3D 资产管理。
- 为不同剧本项目建立统一角色视觉规范。
