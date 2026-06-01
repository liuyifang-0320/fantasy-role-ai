# OCR 与多模态解析设计

## 1. 模块目标

第 8 阶段把图片解析从硬编码 mock 升级为可配置 OCR Provider 骨架。系统在上传 JPG / PNG / JPEG 后，会通过统一 OCR Provider 产出 `ParsedDocument`，后续可以继续参与 `CharacterProfile` 抽取、`KnowledgeChunk` 分块和聊天检索注入。

当前仍不是完整多模态理解系统：默认走 `MockOCRProvider`，真实 OCR 只作为可选能力预留。

## 2. 支持的图片类型

当前图片解析支持：

- PNG
- JPG
- JPEG

TXT / DOCX / PDF 的文本解析链路保持不变。PDF 图片页 OCR fallback 通过 `OCR_ENABLE_PDF_IMAGE_FALLBACK` 预留，默认关闭。

## 3. OCR Provider 抽象层

`backend/app/services/ocr_provider.py` 定义统一接口：

```python
extract_text(image_path: str) -> dict
```

统一返回：

```json
{
  "text": "...",
  "provider": "mock",
  "status": "mock_ocr",
  "confidence": 0.0,
  "error": null
}
```

解析服务只依赖这个统一结构，不直接绑定某个 OCR 厂商或库。

## 4. MockOCRProvider

默认启用，不依赖外部库。

当未配置真实 OCR，或真实 OCR 不可用时，返回固定测试文本：

“当前图片 OCR 使用 mock provider。请配置真实 OCR 后重新解析。”

这段文本会进入 `ParsedDocument.raw_text`，因此也可以继续走角色生成和知识库构建流程。但它只代表测试占位，不代表系统已经真实识别了图片文字。

## 5. PaddleOCRProvider

`PaddleOCRProvider` 是可选真实 OCR provider：

- 只有 `OCR_PROVIDER=paddleocr` 时才尝试加载。
- 不把 `paddleocr` 放进必装依赖。
- 未安装 `paddleocr` 时，后端仍能正常启动。
- PaddleOCR 调用失败或返回空文本时，会自动 fallback 到 `MockOCRProvider`。

这样可以让开发环境保持轻量，部署环境按需安装真实 OCR 依赖。

## 6. ParsedDocument OCR 字段

`parsed_documents` 增加：

- `ocr_provider`：实际产出本次 OCR 文本的 provider。
- `ocr_confidence`：OCR 平均置信度，mock 时为 `0.0`。
- `ocr_error`：OCR fallback 或失败原因，不包含敏感信息。

图片解析结果会使用：

- `parse_status=mock_ocr`：当前是 mock OCR。
- `parse_status=success`：真实 OCR 成功。
- `parse_status=failed`：解析异常。

## 7. 进入后续链路

图片 OCR 文本保存到 `ParsedDocument.raw_text` 后，会和 TXT / DOCX / PDF 一样进入后续流程：

1. `CharacterProfile` 规则抽取读取 `raw_text`。
2. `KnowledgeChunk` 分块服务读取 `raw_text`，图片 mock OCR 对应 `source_type=mock_ocr`。
3. 聊天时知识检索可以命中由图片解析生成的 chunk。
4. `PromptBuilder` 会把命中的知识片段注入 prompt。

如果当前是 mock OCR，后续生成结果只是测试/占位内容，不代表系统真实理解图片资料。

## 8. 配置项

`.env.example` 提供：

```env
OCR_PROVIDER=mock
OCR_LANG=ch
OCR_ENABLE_PDF_IMAGE_FALLBACK=false
```

`OCR_PROVIDER` 可选：

- `mock`
- `paddleocr`

`OCR_LANG` 默认 `ch`，具体语言能力由 provider 决定。

## 9. 状态接口

`GET /api/ocr/status` 返回：

```json
{
  "ocr_provider": "mock",
  "active_provider": "mock",
  "paddleocr_available": false,
  "ocr_lang": "ch",
  "pdf_image_fallback_enabled": false
}
```

前端设置页只展示配置状态，不展示任何敏感信息。

## 10. 后续升级方向

后续可以扩展：

- PaddleOCR 完整部署方案。
- 云 OCR Provider，如自定义 HTTP OCR 服务。
- PDF 扫描页自动图片 OCR。
- 表格、手写体、票据等更细分的多模态解析。
- 图片内容理解与 OCR 文本结合的多模态模型调用。
