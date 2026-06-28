<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">知识图谱</h1>
        <p class="page-sub">按北航智慧课程思路，将课程知识、能力目标、问题链、工程案例和教学资源贯通。</p>
      </div>
      <div class="header-actions">
        <select v-model.number="selectedCourseId" class="course-select" @change="loadGraph">
          <option :value="0">选择课程</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <button class="ghost-btn" @click="seedGraph" :disabled="!selectedCourseId || seeding">
          {{ seeding ? '初始化中...' : '初始化自动测试图谱' }}
        </button>
      </div>
    </div>

    <div class="metric-grid">
      <div class="metric-card"><span>知识节点</span><strong>{{ graph.nodes.length }}</strong></div>
      <div class="metric-card"><span>关联关系</span><strong>{{ graph.edges.length }}</strong></div>
      <div class="metric-card"><span>证据材料</span><strong>{{ evidenceCount }}</strong></div>
      <div class="metric-card"><span>课程</span><strong>{{ graph.course?.name || '--' }}</strong></div>
    </div>

    <div v-if="!selectedCourseId" class="empty">请选择一门课程查看知识图谱。</div>
    <div v-else class="graph-layout">
      <section class="graph-panel">
        <div class="legend">
          <span v-for="item in legend" :key="item.type"><i :class="item.type"></i>{{ item.label }}</span>
          <span class="relation-hint">默认突出选中节点的直接关系，减少无关交叉线。</span>
        </div>
        <div class="graph-scroll">
          <div class="graph-inner">
            <svg class="edges" width="1040" height="780">
              <defs>
                <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
                  <path d="M0,0 L0,6 L9,3 z" fill="#8db7e3" />
                </marker>
              </defs>
              <path
                v-for="edge in visibleEdges"
                :key="edge.id"
                :d="edgePath(edge)"
                class="edge-line"
                marker-end="url(#arrow)"
              />
            </svg>
            <button
              v-for="node in graph.nodes"
              :key="node.id"
              :class="['node', node.node_type, selectedNode?.id === node.id && 'active']"
              :style="{ left: `${node.x || 100}px`, top: `${node.y || 100}px` }"
              @click="selectedNode = node"
            >
              <strong>{{ node.title }}</strong>
              <span>{{ typeLabel(node.node_type) }}</span>
            </button>
          </div>
        </div>
      </section>

      <aside class="detail-panel">
        <template v-if="selectedNode">
          <div class="detail-type">{{ typeLabel(selectedNode.node_type) }}</div>
          <h2>{{ selectedNode.title }}</h2>
          <p>{{ selectedNode.description || '暂无描述' }}</p>
          <div class="evidence-head">
            <strong>教学证据</strong>
            <span>{{ selectedNode.evidence?.length || 0 }} 条</span>
          </div>
          <div v-if="!selectedNode.evidence?.length" class="empty small">暂无直接证据，可继续补充资源或题目映射。</div>
          <div v-for="item in selectedNode.evidence" :key="`${item.type}-${item.id}-${item.label}`" class="evidence-item">
            <span>{{ evidenceType(item.type) }}</span>
            <strong>{{ item.label }}</strong>
            <em>{{ item.description }}</em>
          </div>
        </template>
        <template v-else>
          <div class="empty small">点击图谱节点查看知识点说明和关联资源。</div>
        </template>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

type NodeItem = {
  id: number
  title: string
  node_type: string
  description?: string
  x?: number
  y?: number
  evidence?: any[]
}

const courses = ref<any[]>([])
const selectedCourseId = ref<number>(0)
const selectedNode = ref<NodeItem | null>(null)
const seeding = ref(false)
const graph = ref<any>({ course: null, nodes: [], edges: [], type_labels: {} })

const legend = [
  { type: 'chapter', label: '课程模块' },
  { type: 'knowledge', label: '知识点' },
  { type: 'ability', label: '能力目标' },
  { type: 'problem', label: '问题链' },
  { type: 'case', label: '工程案例' },
]

const evidenceCount = computed(() => graph.value.nodes.reduce((sum: number, n: NodeItem) => sum + (n.evidence?.length || 0), 0))
const nodeById = computed(() => new Map(graph.value.nodes.map((n: NodeItem) => [n.id, n])))
const drawableEdges = computed(() => graph.value.edges
  .map((e: any) => ({ ...e, source: nodeById.value.get(e.source_id), target: nodeById.value.get(e.target_id) }))
  .filter((e: any) => e.source && e.target))
const visibleEdges = computed(() => {
  const edges = drawableEdges.value
  if (!selectedNode.value) return edges.filter((e: any) => e.source?.node_type === 'chapter' || e.target?.node_type === 'chapter')
  const id = selectedNode.value.id
  return edges.filter((e: any) => e.source_id === id || e.target_id === id)
})

function typeLabel(type: string) {
  return graph.value.type_labels?.[type] || type
}

function evidenceType(type: string) {
  return type === 'resource' ? '资源' : type === 'assignment' ? '作业/报告' : type === 'quiz' ? '测验' : type
}

function edgePath(edge: any) {
  const sx = Number(edge.source?.x || 0)
  const sy = Number(edge.source?.y || 0)
  const tx = Number(edge.target?.x || 0)
  const ty = Number(edge.target?.y || 0)
  const dx = tx - sx
  const lift = Math.max(34, Math.min(90, Math.abs(dx) * 0.18))
  const c1x = sx + dx * 0.42
  const c2x = sx + dx * 0.58
  const c1y = sy + (ty >= sy ? lift : -lift)
  const c2y = ty - (ty >= sy ? lift : -lift)
  return `M ${sx} ${sy} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${tx} ${ty}`
}

async function loadGraph() {
  selectedNode.value = null
  if (!selectedCourseId.value) {
    graph.value = { course: null, nodes: [], edges: [], type_labels: {} }
    return
  }
  const r = await axios.get(`/api/v1/knowledge/courses/${selectedCourseId.value}/graph`)
  graph.value = r.data
  selectedNode.value = r.data.nodes[0] || null
}

async function seedGraph() {
  if (!selectedCourseId.value) return
  seeding.value = true
  try {
    const r = await axios.post(`/api/v1/knowledge/courses/${selectedCourseId.value}/seed-auto-test-system`)
    ElMessage.success(`图谱已初始化：${r.data.nodes} 个节点，${r.data.edges} 条关系`)
    await loadGraph()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '图谱初始化失败')
  } finally {
    seeding.value = false
  }
}

onMounted(async () => {
  const r = await axios.get('/api/v1/courses/my')
  courses.value = r.data
  const auto = courses.value.find(c => String(c.name || '').includes('自动测试系统'))
  if (auto) {
    selectedCourseId.value = auto.id
    await loadGraph()
  }
})
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; }
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.course-select { min-width: 240px; background: #ffffff; border: 1px solid #c8ddf4; border-radius: 8px; color: #0f2f64; padding: 9px 12px; outline: none; }
.ghost-btn { background: #ffffff; color: #0b63b6; border: 1px solid #c8ddf4; border-radius: 8px; padding: 9px 14px; font-weight: 800; cursor: pointer; }
.ghost-btn:disabled { opacity: .55; cursor: not-allowed; }
.metric-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 2fr; gap: 12px; margin-bottom: 16px; }
.metric-card { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 9px; padding: 14px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.metric-card span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 8px; }
.metric-card strong { color: #0f2f64; font-size: 23px; line-height: 1.2; }
.graph-layout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: stretch; }
.graph-panel, .detail-panel { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.graph-panel { min-height: 680px; padding: 14px; overflow: hidden; }
.legend { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; color: #5b6f92; font-size: 12px; background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 999px; padding: 5px 9px; }
.legend i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.legend .relation-hint { margin-left: auto; color: #0b63b6; background: #eaf3ff; border-color: #c8ddf4; }
.graph-scroll { overflow: auto; border-radius: 8px; border: 1px solid #edf3fb; background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); }
.graph-inner { width: 1040px; height: 780px; position: relative; }
.edges { position: absolute; left: 0; top: 0; pointer-events: none; }
.edge-line { fill: none; stroke: #8db7e3; stroke-width: 2.2; opacity: .86; stroke-linecap: round; }
.node { position: absolute; transform: translate(-50%, -50%); width: 146px; min-height: 66px; border-radius: 10px; padding: 9px 10px; border: 1px solid #c8ddf4; background: #ffffff; cursor: pointer; text-align: center; box-shadow: 0 10px 22px rgba(15,47,100,.08); transition: all .16s; }
.node strong { display: block; color: #0f2f64; font-size: 13px; line-height: 1.25; }
.node span { display: block; color: #5b6f92; font-size: 11px; margin-top: 5px; }
.node:hover, .node.active { transform: translate(-50%, -50%) translateY(-2px); box-shadow: 0 16px 30px rgba(11,99,182,.18); border-color: #80b8ee; }
.node.chapter { background: #0b63b6; border-color: #0b63b6; }
.node.chapter strong, .node.chapter span { color: #ffffff; }
.node.knowledge { background: #ffffff; }
.node.ability { background: #e8f7f0; border-color: #b6e6ce; }
.node.problem { background: #fff2d9; border-color: #f3d598; }
.node.case { background: #eef2ff; border-color: #c9d4ff; }
.legend .chapter { background: #0b63b6; }
.legend .knowledge { background: #ffffff; border: 1px solid #8db7e3; }
.legend .ability { background: #22a06b; }
.legend .problem { background: #d8890b; }
.legend .case { background: #6366f1; }
.detail-panel { padding: 18px; min-height: 680px; }
.detail-type { display: inline-flex; border-radius: 999px; background: #eaf3ff; color: #0b63b6; padding: 4px 9px; font-size: 12px; font-weight: 900; }
.detail-panel h2 { color: #0f2f64; margin: 14px 0 8px; font-size: 20px; }
.detail-panel p { color: #5b6f92; line-height: 1.7; font-size: 13px; }
.evidence-head { display: flex; justify-content: space-between; align-items: center; margin: 18px 0 10px; color: #0f2f64; }
.evidence-head span { color: #5b6f92; font-size: 12px; }
.evidence-item { border: 1px solid #e1ecf8; border-radius: 8px; padding: 10px; margin-bottom: 8px; background: #f8fbff; }
.evidence-item span { color: #0b63b6; font-size: 12px; font-weight: 900; }
.evidence-item strong { display: block; color: #0f2f64; font-size: 13px; line-height: 1.45; margin-top: 4px; }
.evidence-item em { color: #5b6f92; font-size: 12px; font-style: normal; display: block; margin-top: 4px; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 8px; padding: 24px; text-align: center; background: #f8fbff; }
.empty.small { padding: 18px; font-size: 13px; }
@media (max-width: 1180px) {
  .graph-layout { grid-template-columns: 1fr; }
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
