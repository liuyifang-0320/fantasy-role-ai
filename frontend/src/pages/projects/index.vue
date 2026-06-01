<template>
  <GradientPage>
    <view class="page-head">
      <text class="title">剧本项目</text>
      <text class="subtitle">把资料、角色和知识库放进同一个项目空间里。</text>
    </view>

    <view class="panel form-panel">
      <text class="panel-title">创建新项目</text>
      <label class="field">
        <text>项目名称</text>
        <input v-model="form.title" placeholder="例如：流浪叙事" />
      </label>
      <label class="field">
        <text>项目简介</text>
        <textarea v-model="form.description" placeholder="简单描述这个剧本资料包" />
      </label>
      <button class="primary" :disabled="creating" @click="createProject">
        {{ creating ? '创建中...' : '创建项目' }}
      </button>
    </view>

    <view class="section">
      <text class="section-title">项目列表</text>
      <view v-if="projects.length" class="project-list">
        <view
          v-for="project in projects"
          :key="project.project_id"
          class="project-card"
          @click="goProject(project.project_id)"
        >
          <view class="project-head">
            <text class="project-title">{{ project.title }}</text>
            <text class="status">{{ project.project_status }}</text>
          </view>
          <text class="project-copy">{{ project.description || '暂无简介' }}</text>
          <view class="summary-grid" v-if="project.summary">
            <text>文件 {{ project.summary.file_count }}</text>
            <text>解析 {{ project.summary.parsed_document_count }}</text>
            <text>角色 {{ project.summary.character_count }}</text>
            <text>知识 {{ project.summary.knowledge_chunk_count }}</text>
          </view>
        </view>
      </view>
      <view v-else class="empty">
        <text>还没有剧本项目，先创建一个资料空间。</text>
      </view>
    </view>
  </GradientPage>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import GradientPage from '../../components/GradientPage.vue'

const projects = ref([])
const creating = ref(false)
const form = ref({
  title: '',
  description: '',
  source_type: 'upload',
})

async function loadProjects() {
  projects.value = await api.listProjects()
}

async function createProject() {
  if (!form.value.title.trim()) {
    uni.showToast({ title: '请填写项目名称', icon: 'none' })
    return
  }
  creating.value = true
  try {
    const project = await api.createProject({
      title: form.value.title,
      description: form.value.description,
      source_type: form.value.source_type,
    })
    form.value.title = ''
    form.value.description = ''
    await loadProjects()
    uni.navigateTo({ url: `/pages/project-detail/index?project_id=${project.project_id}` })
  } catch (error) {
    uni.showToast({ title: error.message || '创建失败', icon: 'none' })
  } finally {
    creating.value = false
  }
}

function goProject(projectId) {
  uni.navigateTo({ url: `/pages/project-detail/index?project_id=${projectId}` })
}

onShow(loadProjects)
</script>

<style scoped lang="scss">
.page-head text {
  display: block;
}

.title {
  font-size: 42rpx;
  font-weight: 700;
}

.subtitle {
  margin-top: 10rpx;
  color: rgba(248, 247, 255, 0.72);
  font-size: 24rpx;
}

.panel,
.project-card,
.empty {
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.panel {
  margin-top: 26rpx;
}

.panel-title,
.section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}

.form-panel {
  display: grid;
  gap: 18rpx;
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
  min-height: 140rpx;
  padding-top: 18rpx;
}

.primary {
  border-radius: 8px;
  color: #1b1036;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #ff8db4, #7ee7f6);
}

.section {
  margin-top: 30rpx;
}

.project-list {
  display: grid;
  gap: 16rpx;
  margin-top: 16rpx;
}

.project-head {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.project-title {
  font-size: 30rpx;
  font-weight: 700;
}

.status {
  color: #7ee7f6;
  font-size: 22rpx;
}

.project-copy,
.empty {
  color: rgba(248, 247, 255, 0.74);
  font-size: 24rpx;
  line-height: 1.7;
}

.project-copy {
  display: block;
  margin-top: 10rpx;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10rpx;
  margin-top: 16rpx;
  color: rgba(248, 247, 255, 0.8);
  font-size: 22rpx;
}
</style>
