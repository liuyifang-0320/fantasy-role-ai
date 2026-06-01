<template>
  <GradientPage v-if="project">
    <view class="page-head">
      <text class="title">{{ project.title }}</text>
      <text class="subtitle">{{ project.description || '这个项目还没有简介。' }}</text>
      <text class="project-id">project_id: {{ project.project_id }}</text>
    </view>

    <view class="summary-grid" v-if="project.summary">
      <view class="summary-item">
        <text class="summary-value">{{ project.summary.file_count }}</text>
        <text class="summary-label">文件</text>
      </view>
      <view class="summary-item">
        <text class="summary-value">{{ project.summary.parsed_document_count }}</text>
        <text class="summary-label">解析文档</text>
      </view>
      <view class="summary-item">
        <text class="summary-value">{{ project.summary.character_count }}</text>
        <text class="summary-label">角色</text>
      </view>
      <view class="summary-item">
        <text class="summary-value">{{ project.summary.knowledge_chunk_count }}</text>
        <text class="summary-label">知识片段</text>
      </view>
    </view>

    <view class="panel">
      <text class="panel-title">项目资料</text>
      <button class="ghost" :disabled="uploading" @click="chooseFile">
        {{ uploading ? '上传解析中...' : '选择并解析资料包' }}
      </button>
      <view
        v-for="item in uploadParseItems"
        :key="item.local_id"
        class="parsed-card"
      >
        <text class="parsed-name">{{ item.filename }}</text>
        <text class="parsed-meta">
          {{ item.file_type || '-' }} · {{ item.status }} · {{ item.parse_status || '-' }} · {{ item.word_count || 0 }} 字
        </text>
        <text v-if="item.ocr_provider" class="parsed-meta">
          OCR: {{ item.ocr_provider }} · {{ item.parse_status }}
        </text>
        <text v-if="item.safety_warning" class="parsed-meta warning">
          {{ item.safety_warning }}
        </text>
        <text class="parsed-preview">{{ item.text_preview || item.error || '等待处理' }}</text>
      </view>
    </view>

    <view class="panel ai-panel">
      <view class="panel-head">
        <text class="panel-title">AI 理解剧本资料</text>
        <button class="mini-button" :disabled="llmAnalyzing" @click="runLlmAnalyze">
          {{ llmAnalyzing ? '理解中...' : '让 AI 理解剧本资料' }}
        </button>
      </view>
      <text class="privacy-note">
        AI 理解剧本资料会将解析后的部分文本片段发送给当前配置的大模型服务，用于结构化分析。请勿上传无授权商业剧本或敏感隐私资料。未配置 API Key 时会使用规则 fallback，结果仅供测试。
      </text>

      <view v-if="uploadParseItems.length" class="owner-hint-list">
        <view v-for="item in uploadParseItems" :key="item.local_id" class="owner-hint-card">
          <text class="parsed-name">{{ item.filename }}</text>
          <label class="field">
            <text>文件归属角色（可选）</text>
            <input v-model="llmOwnerHints[item.parsed_document_id || item.file_id].owner_character_name" placeholder="例如：阿奇" />
          </label>
          <label class="field">
            <text>文档范围</text>
            <input v-model="llmOwnerHints[item.parsed_document_id || item.file_id].document_scope" placeholder="character_book / public_background / clue / host_guide / unknown" />
          </label>
        </view>
      </view>

      <view v-if="llmAnalysisStatus" class="analysis-status">
        <text class="candidate-copy">状态：{{ llmAnalysisStatus.status }} · Provider：{{ llmAnalysisStatus.provider || '-' }} · 模型：{{ llmAnalysisStatus.model || '-' }}</text>
        <text class="candidate-copy">文档 {{ llmAnalysisStatus.documents_count || 0 }} · Chunks {{ llmAnalysisStatus.chunks_count || 0 }} · 候选 {{ llmAnalysisStatus.characters_count || 0 }} · 关系 {{ llmAnalysisStatus.relationships_count || 0 }}</text>
      </view>

      <view v-if="llmAnalysisResult" class="analysis-result">
        <text class="candidate-copy">{{ llmAnalysisResult.message || 'AI 理解结果已生成，请确认后再批量生成数字人。' }}</text>
        <text v-if="llmWarningsText" class="candidate-copy warning">{{ llmWarningsText }}</text>

        <view class="candidate-group">
          <text class="group-title">AI 候选角色</text>
          <text class="group-copy">高置信 person 可进入生成；中低置信与 unknown 需要先人工确认。</text>
        </view>
        <view
          v-for="candidate in llmResultCharacters"
          :key="candidate.candidate_id || candidate.canonical_name"
          class="candidate-card"
        >
          <view class="candidate-head">
            <text class="candidate-name">{{ candidate.display_name || candidate.canonical_name }}</text>
            <text class="status">{{ candidate.candidate_type }} · {{ candidate.confidence_level }} · {{ candidate.candidate_status }}</text>
          </view>
          <text class="candidate-copy">LLM 理由：{{ candidate.llm_reason || candidate.reviewer_reason || '-' }}</text>
          <text class="candidate-copy">证据：{{ candidate.evidence || candidate.llm_evidence || '-' }}</text>
          <text class="candidate-copy">来源：{{ (candidate.source_documents || []).join(', ') || '-' }}</text>
        </view>

        <view class="candidate-group">
          <text class="group-title">AI 关系结果</text>
          <text class="group-copy">hidden / heavy 关系默认不会进入 non_spoiler 普通聊天。</text>
        </view>
        <view
          v-for="relationship in llmResultRelationships"
          :key="relationship.relationship_id || `${relationship.source_character_name}_${relationship.target_character_name}_${relationship.relation_type}`"
          class="relationship-card"
        >
          <view class="relationship-line">
            <text class="candidate-name">{{ relationship.source_character_name }}</text>
            <text class="graph-link">— {{ relationship.relation_type }} —</text>
            <text class="candidate-name">{{ relationship.target_character_name }}</text>
          </view>
          <text class="candidate-copy">{{ relationship.relation_summary }}</text>
          <text class="candidate-copy">置信：{{ relationship.confidence_level }} · {{ relationship.is_explicit ? '明确' : '推断' }} · {{ relationship.spoiler_level }} · {{ relationship.visibility }}</text>
          <text class="evidence">{{ relationship.evidence_summary || '-' }}</text>
        </view>

        <view class="row-actions">
          <button class="mini-button" @click="confirmLlmAnalysis">确认 AI 理解结果</button>
          <button class="ghost mini-ghost" @click="loadProject">刷新候选/关系</button>
        </view>
      </view>
    </view>

    <view class="panel candidate-panel">
      <view class="panel-head">
        <text class="panel-title">角色候选</text>
        <button class="mini-button" :disabled="extracting" @click="extractCandidates">
          {{ extracting ? '识别中...' : '识别角色候选' }}
        </button>
      </view>

      <view v-if="candidates.length" class="candidate-list">
        <view class="candidate-group">
          <text class="group-title">高置信角色候选</text>
          <text class="group-copy">默认可勾选生成；必须具备当前角色、字段、标题/文件名、复核高置信或足够对白证据，单独关系句不会进入这里。</text>
        </view>
        <view
          v-for="candidate in highConfidenceCandidates"
          :key="candidate.candidate_id"
          class="candidate-card"
          :class="{ selected: selectedCandidateIds.includes(candidate.candidate_id) }"
        >
          <view class="candidate-head">
            <label class="candidate-check">
              <checkbox
                :value="candidate.candidate_id"
                :checked="selectedCandidateIds.includes(candidate.candidate_id)"
                @click.stop="toggleCandidate(candidate.candidate_id)"
              />
              <text class="candidate-name">{{ candidate.display_name || candidate.name }}</text>
            </label>
            <text class="status">{{ candidate.candidate_type }} · {{ candidate.confidence_level }} · {{ candidate.candidate_status }}</text>
          </view>
          <text class="candidate-copy">{{ candidate.identity_hint || '暂无身份提示' }}</text>
          <text class="candidate-copy">{{ relationText(candidate) }}</text>
          <text class="candidate-copy">置信度 {{ formatConfidence(candidate.confidence) }} · 来源 {{ (candidate.source_types || []).join(' / ') || '-' }}</text>
          <text class="candidate-copy">出现 {{ candidate.mention_count || 0 }} 次 · 对白 {{ candidate.dialogue_count || 0 }} 次</text>
          <text class="candidate-copy">Reviewer：{{ candidate.reviewer_status || '-' }} · {{ candidate.reviewer_reason || '-' }}</text>
          <text class="candidate-copy">关系证据：{{ (candidate.relationship_evidence || []).join('；') || '暂无' }}</text>
          <text class="evidence">{{ candidate.evidence || '暂无证据摘要' }}</text>

          <view v-if="editingCandidateId === candidate.candidate_id" class="edit-box">
            <label class="field">
              <text>角色名</text>
              <input v-model="candidateDraft.name" />
            </label>
            <label class="field">
              <text>身份提示</text>
              <input v-model="candidateDraft.identity_hint" />
            </label>
            <label class="field">
              <text>性格提示</text>
              <input v-model="candidateDraft.personality_hint" />
            </label>
            <label class="field">
              <text>关系线索</text>
              <textarea v-model="candidateDraft.relationship_hints_text" />
            </label>
            <view class="row-actions">
              <button class="mini-button" @click="saveCandidate(candidate)">保存</button>
              <button class="ghost mini-ghost" @click="editingCandidateId = ''">取消</button>
            </view>
          </view>

          <view v-else class="row-actions">
            <button class="mini-button" @click="editCandidate(candidate)">编辑</button>
            <button class="ghost mini-ghost" @click="ignoreCandidate(candidate)">忽略</button>
          </view>
        </view>

        <view class="candidate-group">
          <text class="group-title">待确认候选</text>
          <text class="group-copy">低/中置信候选必须先确认为角色，才允许批量生成。</text>
          <button class="ghost mini-ghost" @click="showReviewCandidates = !showReviewCandidates">
            {{ showReviewCandidates ? '收起' : `展开（${reviewCandidates.length}）` }}
          </button>
        </view>
        <view v-if="showReviewCandidates" class="candidate-list">
          <view
            v-for="candidate in reviewCandidates"
            :key="candidate.candidate_id"
            class="candidate-card"
          >
            <view class="candidate-head">
              <text class="candidate-name">{{ candidate.display_name || candidate.name }}</text>
              <text class="status">{{ candidate.candidate_type }} · {{ candidate.confidence_level }}</text>
            </view>
            <text class="candidate-copy">{{ candidate.identity_hint || '暂无身份提示' }}</text>
            <text class="candidate-copy">来源 {{ (candidate.source_types || []).join(' / ') || '-' }} · 需人工确认：{{ candidate.needs_human_review ? '是' : '否' }}</text>
            <text class="candidate-copy">Reviewer：{{ candidate.reviewer_status || '-' }} · {{ candidate.reviewer_reason || '-' }}</text>
            <text class="evidence">{{ candidate.evidence || '暂无证据摘要' }}</text>
            <view class="row-actions">
              <button class="mini-button" @click="confirmCandidate(candidate)">确认为角色</button>
              <button class="ghost mini-ghost" @click="editCandidate(candidate)">编辑</button>
              <button class="ghost mini-ghost" @click="ignoreCandidate(candidate)">忽略</button>
            </view>
          </view>
        </view>

        <view class="candidate-group">
          <text class="group-title">非人物 / 噪声候选</text>
          <text class="group-copy">默认折叠为不可生成；可人工改为人物后再确认。</text>
          <button class="ghost mini-ghost" @click="showNonPersonCandidates = !showNonPersonCandidates">
            {{ showNonPersonCandidates ? '收起' : `展开（${nonPersonCandidates.length}）` }}
          </button>
        </view>
        <view v-if="showNonPersonCandidates" class="candidate-list">
          <view
            v-for="candidate in nonPersonCandidates"
            :key="candidate.candidate_id"
            class="candidate-card muted-card"
          >
            <view class="candidate-head">
              <text class="candidate-name">{{ candidate.display_name || candidate.name }}</text>
              <text class="status">{{ candidate.candidate_type }}</text>
            </view>
            <text class="candidate-copy">{{ candidate.identity_hint || '规则归类为非人物候选' }}</text>
            <text class="evidence">{{ candidate.evidence || '暂无证据摘要' }}</text>
            <view class="row-actions">
              <button class="mini-button" @click="setCandidateType(candidate, 'person')">标记为人物</button>
              <button class="ghost mini-ghost" @click="setCandidateType(candidate, 'organization')">标记组织</button>
              <button class="ghost mini-ghost" @click="setCandidateType(candidate, 'place')">标记地点</button>
              <button class="ghost mini-ghost" @click="setCandidateType(candidate, 'prop')">标记道具</button>
              <button class="ghost mini-ghost" @click="setCandidateType(candidate, 'clue')">标记线索</button>
              <button class="ghost mini-ghost" @click="ignoreCandidate(candidate)">忽略</button>
            </view>
          </view>
        </view>
      </view>
      <view v-else class="empty">
        <text>还没有角色候选。请先上传并解析项目资料，然后点击识别。</text>
      </view>

      <view class="batch-box">
        <text class="panel-title">批量生成数字人</text>
        <label class="field">
          <text>用户扮演身份</text>
          <input v-model="batchForm.user_persona_name" placeholder="例如：戴丽拉" />
        </label>
        <label class="field">
          <text>默认关系提示</text>
          <input v-model="batchForm.default_relationship_hint" placeholder="根据剧本资料生成" />
        </label>
        <button class="primary" :disabled="batchGenerating" @click="batchGenerate">
          {{ batchGenerating ? '批量生成中...' : `生成已选候选（${selectedCandidateIds.length}）` }}
        </button>
        <text v-if="batchResultText" class="batch-result">{{ batchResultText }}</text>
      </view>
    </view>

    <view class="panel relationship-panel">
      <view class="panel-head">
        <text class="panel-title">角色关系图</text>
        <button class="mini-button" :disabled="extractingRelationships" @click="extractRelationships">
          {{ extractingRelationships ? '抽取中...' : '抽取角色关系' }}
        </button>
      </view>

      <view v-if="graph.edges.length" class="graph-list">
        <view v-for="edge in graph.edges" :key="edge.id" class="graph-edge">
          <text class="graph-node">{{ edge.source }}</text>
          <text class="graph-link">— {{ edge.label }} —</text>
          <text class="graph-node">{{ edge.target }}</text>
        </view>
      </view>
      <view v-else class="empty">
        <text>还没有关系图。请先抽取角色关系。</text>
      </view>

      <view v-if="relationships.length" class="relationship-list">
        <view
          v-for="relationship in relationships"
          :key="relationship.relationship_id"
          class="relationship-card"
        >
          <view class="relationship-line">
            <text class="candidate-name">{{ relationship.source_character_name }}</text>
            <text class="graph-link">— {{ relationship.relation_type }} —</text>
            <text class="candidate-name">{{ relationship.target_character_name }}</text>
          </view>
          <text class="status">{{ relationship.relationship_status }}</text>
          <text class="candidate-copy">{{ relationship.relation_summary }}</text>
          <text class="evidence">{{ relationship.evidence || '暂无证据片段' }}</text>

          <view v-if="editingRelationshipId === relationship.relationship_id" class="edit-box">
            <label class="field">
              <text>主体角色</text>
              <input v-model="relationshipDraft.source_character_name" />
            </label>
            <label class="field">
              <text>目标角色</text>
              <input v-model="relationshipDraft.target_character_name" />
            </label>
            <label class="field">
              <text>关系类型</text>
              <input v-model="relationshipDraft.relation_type" />
            </label>
            <label class="field">
              <text>关系摘要</text>
              <textarea v-model="relationshipDraft.relation_summary" />
            </label>
            <view class="row-actions">
              <button class="mini-button" @click="saveRelationship(relationship)">保存</button>
              <button class="ghost mini-ghost" @click="editingRelationshipId = ''">取消</button>
            </view>
          </view>

          <view v-else class="row-actions">
            <button class="mini-button" @click="editRelationship(relationship)">编辑</button>
            <button class="ghost mini-ghost" @click="ignoreRelationship(relationship)">忽略</button>
          </view>
        </view>
      </view>
    </view>

    <view class="panel form-panel">
      <text class="panel-title">从项目资料创建单个角色</text>
      <label class="field">
        <text>目标角色名</text>
        <input v-model="form.target_character_name" placeholder="例如：阿奇" />
      </label>
      <label class="field">
        <text>用户扮演身份</text>
        <input v-model="form.user_persona_name" placeholder="例如：戴丽拉" />
      </label>
      <label class="field">
        <text>关系提示</text>
        <input v-model="form.relationship_hint" placeholder="例如：情侣" />
      </label>
      <button class="primary" :disabled="generating" @click="generateCharacter">
        {{ generating ? '生成中...' : '生成项目角色' }}
      </button>
    </view>

    <view class="section">
      <text class="section-title">已生成数字人</text>
      <view v-if="projectCharacters.length" class="character-list">
        <view
          v-for="character in projectCharacters"
          :key="character.character_id"
          class="character-card"
          @click="goCharacter(character)"
        >
          <text class="character-name">{{ character.character_name }}</text>
          <text class="character-meta">{{ character.relationship_with_user }}</text>
        </view>
      </view>
      <view v-else class="empty">
        <text>这个项目还没有角色。</text>
      </view>
    </view>
  </GradientPage>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import GradientPage from '../../components/GradientPage.vue'
import { chooseAndUploadFiles } from '../../utils/upload'

const projectId = ref('')
const project = ref(null)
const characters = ref([])
const candidates = ref([])
const relationships = ref([])
const graph = ref({ nodes: [], edges: [] })
const uploading = ref(false)
const extracting = ref(false)
const extractingRelationships = ref(false)
const llmAnalyzing = ref(false)
const generating = ref(false)
const batchGenerating = ref(false)
const uploadedFiles = ref([])
const parsedDocument = ref(null)
const uploadParseItems = ref([])
const projectCharacters = ref([])
const selectedCandidateIds = ref([])
const editingCandidateId = ref('')
const editingRelationshipId = ref('')
const batchResultText = ref('')
const showReviewCandidates = ref(false)
const showNonPersonCandidates = ref(false)
const llmAnalysisStatus = ref(null)
const llmAnalysisResult = ref(null)
const llmOwnerHints = ref({})
const candidateDraft = ref({
  name: '',
  identity_hint: '',
  personality_hint: '',
  relationship_hints_text: '',
})
const relationshipDraft = ref({
  source_character_name: '',
  target_character_name: '',
  relation_type: '',
  relation_summary: '',
})
const form = ref({
  target_character_name: '阿奇',
  user_persona_name: '戴丽拉',
  relationship_hint: '情侣',
})
const batchForm = ref({
  user_persona_name: '戴丽拉',
  default_relationship_hint: '根据剧本资料生成',
})
const highConfidenceCandidates = computed(() =>
  candidates.value.filter((candidate) => isHighConfidencePerson(candidate))
)
const reviewCandidates = computed(() =>
  candidates.value.filter(
    (candidate) =>
      ['person', 'unknown'].includes(candidate.candidate_type) &&
      (candidate.needs_human_review || candidate.confidence_level !== 'high') &&
      ['pending', 'confirmed'].includes(candidate.candidate_status)
  )
)
const nonPersonCandidates = computed(() =>
  candidates.value.filter(
    (candidate) =>
      !['person', 'unknown'].includes(candidate.candidate_type) &&
      !['ignored', 'rejected', 'generated'].includes(candidate.candidate_status)
  )
)
const llmResultCharacters = computed(() => llmAnalysisResult.value?.characters || [])
const llmResultRelationships = computed(() => llmAnalysisResult.value?.relationships || [])
const llmWarningsText = computed(() => (llmAnalysisResult.value?.warnings || []).join('；'))

async function loadProject() {
  if (!projectId.value) {
    return
  }
  project.value = await api.getProject(projectId.value)
  characters.value = await api.getCharacters()
  projectCharacters.value = characters.value.filter(
    (character) => character.project_id === projectId.value
  )
  candidates.value = await api.listProjectCandidates(projectId.value)
  relationships.value = await api.listProjectRelationships(projectId.value)
  graph.value = await api.getProjectRelationshipGraph(projectId.value)
}

async function chooseFile() {
  try {
    uploading.value = true
    const uploadedList = await chooseAndUploadFiles({ projectId: projectId.value })
    for (const uploaded of uploadedList) {
      const item = {
        local_id: `${Date.now()}_${uploaded.file_id}`,
        file_id: uploaded.file_id,
        filename: uploaded.filename,
        file_type: uploaded.file_type,
        upload_status: uploaded.upload_status,
        status: 'uploaded',
        parse_status: 'waiting',
        word_count: 0,
        text_preview: '',
        ocr_provider: '',
        safety_warning: '',
        error: '',
      }
      ensureOwnerHint(item)
      uploadParseItems.value.push(item)
      uploadedFiles.value.push(uploaded)
      try {
        item.status = 'parsing'
        const parsed = await api.parseFile(uploaded.file_id)
        parsedDocument.value = parsed
        item.status = 'parsed'
        item.parse_status = parsed.parse_status
        item.parsed_document_id = parsed.parsed_id
        item.word_count = parsed.word_count
        item.text_preview = parsed.text_preview
        item.ocr_provider = parsed.ocr_provider || ''
        item.safety_warning = parsed.safety_warning || ''
        ensureOwnerHint(item)
      } catch (parseError) {
        item.status = 'failed'
        item.error = parseError.message || '解析失败'
      }
    }
    await loadProject()
  } catch (error) {
    if (!error?.errMsg?.includes('cancel')) {
      uni.showToast({ title: error.message || '上传失败', icon: 'none' })
    }
  } finally {
    uploading.value = false
  }
}

async function extractCandidates() {
  extracting.value = true
  try {
    candidates.value = await api.extractProjectCandidates(projectId.value)
    selectedCandidateIds.value = candidates.value
      .filter((candidate) => isHighConfidencePerson(candidate))
      .map((candidate) => candidate.candidate_id)
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '识别失败', icon: 'none' })
  } finally {
    extracting.value = false
  }
}

async function extractRelationships() {
  extractingRelationships.value = true
  try {
    relationships.value = await api.extractProjectRelationships(projectId.value)
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '抽取失败', icon: 'none' })
  } finally {
    extractingRelationships.value = false
  }
}

function ensureOwnerHint(item) {
  const key = item?.parsed_document_id || item?.file_id
  if (!key) return
  if (!llmOwnerHints.value[key]) {
    llmOwnerHints.value[key] = {
      parsed_document_id: item.parsed_document_id || '',
      owner_character_name: '',
      document_scope: 'unknown',
    }
  }
}

function buildOwnerHints() {
  uploadParseItems.value.forEach(ensureOwnerHint)
  return Object.values(llmOwnerHints.value)
    .filter((hint) => hint.parsed_document_id)
    .map((hint) => ({
      parsed_document_id: hint.parsed_document_id,
      owner_character_name: hint.owner_character_name || '',
      document_scope: hint.document_scope || 'unknown',
    }))
}

async function loadScriptIntelligenceStatus() {
  if (!projectId.value) return
  try {
    llmAnalysisStatus.value = await api.getScriptIntelligenceStatus(projectId.value)
    const result = await api.getScriptIntelligenceResult(projectId.value)
    llmAnalysisResult.value = result?.result || null
  } catch (error) {
    llmAnalysisStatus.value = null
  }
}

async function runLlmAnalyze() {
  llmAnalyzing.value = true
  try {
    const parsedIds = uploadParseItems.value
      .map((item) => item.parsed_document_id)
      .filter(Boolean)
    const result = await api.runLlmScriptAnalyze(projectId.value, {
      parsed_document_ids: parsedIds,
      force_rebuild: false,
      use_llm: true,
      spoiler_mode: 'non_spoiler',
      owner_hints: buildOwnerHints(),
    })
    llmAnalysisResult.value = result.summary
    llmAnalysisStatus.value = {
      analysis_id: result.analysis_id,
      status: result.status,
      provider: result.summary.provider,
      model: result.summary.model,
      documents_count: result.summary.documents_count || result.summary?.corpus_analysis?.corpus_summary?.documents_count || 0,
      chunks_count: result.summary.chunks_count || 0,
      characters_count: result.summary.characters?.length || 0,
      relationships_count: result.summary.relationships?.length || 0,
      warnings: result.summary.warnings || [],
    }
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || 'AI 理解失败', icon: 'none' })
  } finally {
    llmAnalyzing.value = false
  }
}

async function confirmLlmAnalysis() {
  try {
    const confirmedCandidateIds = llmResultCharacters.value
      .filter((candidate) => candidate.candidate_type === 'person' && candidate.confidence_level === 'high')
      .map((candidate) => candidate.candidate_id)
      .filter(Boolean)
    const confirmedRelationshipIds = llmResultRelationships.value
      .filter((relationship) => relationship.confidence_level === 'high')
      .map((relationship) => relationship.relationship_id)
      .filter(Boolean)
    await api.confirmScriptIntelligence(projectId.value, {
      confirmed_candidate_ids: confirmedCandidateIds,
      confirmed_relationship_ids: confirmedRelationshipIds,
      spoiler_mode: 'non_spoiler',
      document_ownership: buildOwnerHints(),
    })
    uni.showToast({ title: 'AI 理解结果已确认', icon: 'none' })
    await loadProject()
    await loadScriptIntelligenceStatus()
  } catch (error) {
    uni.showToast({ title: error.message || '确认失败', icon: 'none' })
  }
}

function toggleCandidate(candidateId) {
  const candidate = candidates.value.find((item) => item.candidate_id === candidateId)
  if (!isCandidateSelectable(candidate)) {
    uni.showToast({ title: '该候选需要先确认为角色，或不是人物候选。', icon: 'none' })
    return
  }
  if (selectedCandidateIds.value.includes(candidateId)) {
    selectedCandidateIds.value = selectedCandidateIds.value.filter((id) => id !== candidateId)
  } else {
    selectedCandidateIds.value = [...selectedCandidateIds.value, candidateId]
  }
}

function editCandidate(candidate) {
  editingCandidateId.value = candidate.candidate_id
  candidateDraft.value = {
    name: candidate.display_name || candidate.name,
    identity_hint: candidate.identity_hint,
    personality_hint: candidate.personality_hint,
    relationship_hints_text: (candidate.relationship_hints || []).join('\n'),
  }
}

async function saveCandidate(candidate) {
  try {
    await api.updateCharacterCandidate(candidate.candidate_id, {
      name: candidateDraft.value.name,
      display_name: candidateDraft.value.name,
      identity_hint: candidateDraft.value.identity_hint,
      personality_hint: candidateDraft.value.personality_hint,
      relationship_hints: splitLines(candidateDraft.value.relationship_hints_text),
      candidate_type: 'person',
      confidence_level: 'high',
      needs_human_review: false,
      candidate_status: 'confirmed',
    })
    editingCandidateId.value = ''
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  }
}

async function confirmCandidate(candidate) {
  try {
    await api.updateCharacterCandidate(candidate.candidate_id, {
      candidate_type: 'person',
      confidence_level: 'high',
      needs_human_review: false,
      candidate_status: 'confirmed',
    })
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '确认失败', icon: 'none' })
  }
}

async function setCandidateType(candidate, candidateType) {
  try {
    await api.updateCharacterCandidate(candidate.candidate_id, {
      candidate_type: candidateType,
      candidate_status: candidateType === 'person' ? 'confirmed' : 'pending',
      confidence_level: candidateType === 'person' ? 'high' : 'low',
      needs_human_review: candidateType !== 'person',
    })
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '更新失败', icon: 'none' })
  }
}

async function ignoreCandidate(candidate) {
  try {
    await api.ignoreCharacterCandidate(candidate.candidate_id)
    selectedCandidateIds.value = selectedCandidateIds.value.filter(
      (id) => id !== candidate.candidate_id
    )
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '忽略失败', icon: 'none' })
  }
}

function editRelationship(relationship) {
  editingRelationshipId.value = relationship.relationship_id
  relationshipDraft.value = {
    source_character_name: relationship.source_character_name,
    target_character_name: relationship.target_character_name,
    relation_type: relationship.relation_type,
    relation_summary: relationship.relation_summary,
  }
}

async function saveRelationship(relationship) {
  try {
    await api.updateCharacterRelationship(relationship.relationship_id, {
      ...relationshipDraft.value,
      relationship_status: 'confirmed',
    })
    editingRelationshipId.value = ''
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  }
}

async function ignoreRelationship(relationship) {
  try {
    await api.ignoreCharacterRelationship(relationship.relationship_id)
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '忽略失败', icon: 'none' })
  }
}

async function batchGenerate() {
  if (!selectedCandidateIds.value.length) {
    uni.showToast({ title: '请先选择候选角色', icon: 'none' })
    return
  }
  const invalid = selectedCandidateIds.value
    .map((id) => candidates.value.find((candidate) => candidate.candidate_id === id))
    .find((candidate) => !isCandidateSelectable(candidate))
  if (invalid) {
    uni.showToast({ title: '低置信或非人物候选不能直接生成。', icon: 'none' })
    return
  }
  batchGenerating.value = true
  try {
    const result = await api.batchGenerateProjectCharacters(projectId.value, {
      candidate_ids: selectedCandidateIds.value,
      user_persona_name: batchForm.value.user_persona_name,
      default_relationship_hint: batchForm.value.default_relationship_hint,
      relationship_overrides: {},
    })
    batchResultText.value = `生成 ${result.generated.length} 个，跳过 ${result.skipped.length} 个，失败 ${result.failed.length} 个。`
    selectedCandidateIds.value = []
    await loadProject()
  } catch (error) {
    uni.showToast({ title: error.message || '批量生成失败', icon: 'none' })
  } finally {
    batchGenerating.value = false
  }
}

async function generateCharacter() {
  if (!uploadedFiles.value.length) {
    uni.showToast({ title: '请先上传项目资料', icon: 'none' })
    return
  }
  generating.value = true
  try {
    const character = await api.generateCharacter({
      project_id: projectId.value,
      uploaded_file_ids: uploadedFiles.value.map((file) => file.file_id),
      ...form.value,
    })
    uni.setStorageSync('latestGeneratedCharacter', character)
    uni.setStorageSync('latestParsedDocuments', character.parsed_documents || [])
    uni.setStorageSync('latestCharacterProfile', character.profile || null)
    await loadProject()
    uni.navigateTo({
      url: `/pages/generate-result/index?character_id=${character.character_id}`,
    })
  } catch (error) {
    uni.showToast({ title: error.message || '生成失败', icon: 'none' })
  } finally {
    generating.value = false
  }
}

function splitLines(text) {
  return text
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function relationText(candidate) {
  return (candidate.relationship_hints || []).join('；') || '暂无关系线索'
}

function isCandidateSelectable(candidate) {
  if (!candidate) return false
  if (candidate.candidate_type !== 'person') return false
  if (candidate.candidate_status === 'confirmed') return true
  return isHighConfidencePerson(candidate)
}

function isHighConfidencePerson(candidate) {
  if (!candidate) return false
  if (candidate.candidate_type !== 'person') return false
  if (candidate.confidence_level !== 'high') return false
  if (candidate.needs_human_review) return false
  if (!['pending', 'confirmed'].includes(candidate.candidate_status)) return false
  if (!['success', 'rule_fallback', 'manual'].includes(candidate.reviewer_status || '')) return false
  return hasStrongCandidateSource(candidate)
}

function hasStrongCandidateSource(candidate) {
  const sources = new Set(candidate.source_types || [])
  if (['current_character', 'identity_field', 'filename', 'title', 'llm_review'].some((source) => sources.has(source))) {
    return true
  }
  if (sources.has('dialogue_label')) {
    return (
      Number(candidate.dialogue_count || 0) >= 2 ||
      [...sources].some((source) => !['dialogue_label', 'relationship_sentence'].includes(source)) ||
      sources.has('relationship_sentence')
    )
  }
  return false
}

function formatConfidence(value) {
  return Number(value || 0).toFixed(2)
}

function getCharacterId(item) {
  if (typeof item === 'string') return item
  if (item && item.character_id) return item.character_id
  if (item && item.id) return item.id
  return ''
}

function showMissingCharacterIdToast() {
  uni.showToast({ title: '角色 ID 缺失，无法进入详情页。', icon: 'none' })
}

function goCharacter(item) {
  const characterId = getCharacterId(item)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  uni.navigateTo({
    url: `/pages/character-detail/index?character_id=${encodeURIComponent(characterId)}`,
  })
}

onLoad(({ project_id }) => {
  projectId.value = project_id || ''
})

onShow(async () => {
  await loadProject()
  await loadScriptIntelligenceStatus()
})
</script>

<style scoped lang="scss">
.page-head text {
  display: block;
}

.title {
  font-size: 42rpx;
  font-weight: 700;
}

.subtitle,
.project-id {
  margin-top: 10rpx;
  color: rgba(248, 247, 255, 0.72);
  font-size: 24rpx;
  line-height: 1.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
  margin-top: 24rpx;
}

.summary-item,
.panel,
.parsed-card,
.candidate-card,
.relationship-card,
.character-card,
.empty {
  padding: 20rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.summary-item text,
.panel-title,
.parsed-card text,
.candidate-card text,
.relationship-card text,
.character-card text {
  display: block;
}

.summary-value {
  font-size: 34rpx;
  font-weight: 700;
}

.summary-label {
  margin-top: 6rpx;
  color: rgba(248, 247, 255, 0.66);
  font-size: 22rpx;
}

.panel {
  display: grid;
  gap: 16rpx;
  margin-top: 24rpx;
}

.panel-head,
.candidate-head,
.row-actions,
.relationship-line,
.graph-edge {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.panel-title,
.section-title {
  font-size: 28rpx;
  font-weight: 700;
}

.field text {
  display: block;
  margin-bottom: 10rpx;
  color: rgba(248, 247, 255, 0.74);
  font-size: 24rpx;
}

.field input,
.field textarea {
  width: 100%;
  padding: 0 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(19, 12, 47, 0.46);
  color: #f8f7ff;
}

.field input {
  height: 76rpx;
}

.field textarea {
  min-height: 120rpx;
  padding-top: 18rpx;
}

.primary,
.ghost,
.mini-button,
.mini-ghost {
  border-radius: 8px;
}

.primary {
  color: #1b1036;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #ff8db4, #7ee7f6);
}

.ghost {
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.12);
}

.mini-button,
.mini-ghost {
  min-width: 120rpx;
  height: 56rpx;
  margin: 0;
  padding: 0 16rpx;
  font-size: 22rpx;
  line-height: 56rpx;
}

.mini-button {
  color: #1b1036;
  background: #7ee7f6;
}

.mini-ghost {
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.12);
}

.parsed-name,
.candidate-name,
.character-name,
.graph-node {
  font-size: 28rpx;
  font-weight: 700;
}

.parsed-meta,
.character-meta,
.status,
.graph-link {
  margin-top: 8rpx;
  color: #7ee7f6;
  font-size: 22rpx;
}

.warning {
  color: #ffd166;
}

.parsed-preview,
.candidate-copy,
.evidence,
.empty,
.batch-result {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.76);
  font-size: 24rpx;
  line-height: 1.7;
}

.candidate-list,
.relationship-list,
.graph-list,
.character-list,
.edit-box,
.batch-box {
  display: grid;
  gap: 16rpx;
}

.candidate-group {
  padding: 16rpx 18rpx;
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.1);
}

.group-title,
.group-copy {
  display: block;
}

.group-title {
  color: #7ee7f6;
  font-size: 26rpx;
  font-weight: 700;
}

.group-copy {
  margin-top: 6rpx;
  color: rgba(248, 247, 255, 0.72);
  font-size: 22rpx;
  line-height: 1.5;
}

.candidate-card.selected {
  border-color: rgba(126, 231, 246, 0.46);
  background: rgba(126, 231, 246, 0.12);
}

.muted-card {
  opacity: 0.82;
}

.candidate-check {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.graph-edge {
  justify-content: flex-start;
  padding: 16rpx 18rpx;
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.12);
}

.relationship-line {
  justify-content: flex-start;
}

.edit-box,
.batch-box {
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.12);
}

.section {
  margin-top: 28rpx;
}

.character-list {
  margin-top: 16rpx;
}
</style>
