<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="900px"
    :destroy-on-close="true"
    class="terminal-dialog"
    :close-on-click-modal="false"
  >
    <div class="terminal-window">
      <div class="terminal-header">
        <div class="terminal-dots">
          <span class="dot close"></span>
          <span class="dot minimize"></span>
          <span class="dot maximize"></span>
        </div>
        <span class="terminal-title">{{ terminalTitle }}</span>
      </div>
      <div class="terminal-content" ref="contentRef">
        <pre v-if="content" class="terminal-text"
             :class="{ 'green-text': isGreenTheme, 'white-text': !isGreenTheme }">{{ content }}</pre>
        <el-empty v-else description="正在加载..." :image-size="80" />
      </div>
      <div class="terminal-footer">
        <el-button size="small" @click="copyContent">复制</el-button>
        <span class="terminal-status">
          <el-icon><OfficeBuilding /></el-icon>
          {{ formatField }}
        </span>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button size="small" @click="closeDialog">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { OfficeBuilding } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: boolean
  title: string
  content: string
  formatField: string
  isGreenTheme?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const dialogVisible = ref(false)
const contentRef = ref<HTMLElement | null>(null)

watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
})

watch(() => dialogVisible.value, (val) => {
  emit('update:modelValue', val)
})

const closeDialog = () => {
  dialogVisible.value = false
}

const copyContent = () => {
  if (!props.content) return
  navigator.clipboard.writeText(props.content).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const dialogTitle = computed(() => {
  return props.title
})

const terminalTitle = computed(() => {
  return props.title
})

onMounted(() => {
  // 初始化时滚动到底部
  nextTick(() => {
    if (contentRef.value) {
      contentRef.value.scrollTop = contentRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.terminal-dialog ::v-deep .el-dialog {
  background-color: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.terminal-dialog ::v-deep .el-dialog__header {
  background-color: #3c3c3c;
  padding: 10px 20px;
  border-bottom: 1px solid #2c2c2c;
}

.terminal-dialog ::v-deep .el-dialog__title {
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
}

.terminal-dialog ::v-deep .el-dialog__close {
  color: #ffffff;
  font-size: 16px;
}

.terminal-dialog ::v-deep .el-dialog__close:hover {
  color: #4caf50;
}

.terminal-window {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.terminal-header {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background-color: #3c3c3c;
  border-bottom: 1px solid #2c2c2c;
}

.terminal-dots {
  display: flex;
  gap: 6px;
  margin-right: 16px;
}

.terminal-dots .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.terminal-dots .dot.close {
  background-color: #ff5f56;
}

.terminal-dots .dot.minimize {
  background-color: #ffbd2e;
}

.terminal-dots .dot.maximize {
  background-color: #27c93f;
}

.terminal-title {
  color: #cccccc;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.terminal-content {
  flex: 1;
  overflow: auto;
  background-color: #000000;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.terminal-content .terminal-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #00ff00;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.terminal-content .green-text {
  color: #00ff00 !important;
  text-shadow: 0 0 2px rgba(0, 255, 0, 0.3);
}

.terminal-content .white-text {
  color: #ffffff !important;
}

.terminal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background-color: #3c3c3c;
  border-top: 1px solid #2c2c2c;
}

.terminal-footer .dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.terminal-footer .terminal-status {
  color: #cccccc;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.terminal-footer .terminal-status .el-icon {
  margin-right: 4px;
}
</style>
