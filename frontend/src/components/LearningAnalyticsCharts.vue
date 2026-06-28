<template>
  <div class="visual-grid">
    <section class="visual-card">
      <div class="visual-head">
        <div>
          <strong>{{ radarTitle }}</strong>
          <span>{{ radarSubtitle }}</span>
        </div>
      </div>
      <svg class="radar-svg" viewBox="0 0 320 260" role="img" aria-label="能力雷达图">
        <polygon
          v-for="grid in radarGrid"
          :key="grid.level"
          :points="grid.points"
          class="radar-grid"
        />
        <line
          v-for="axis in radarAxes"
          :key="axis.label"
          x1="160"
          y1="126"
          :x2="axis.x"
          :y2="axis.y"
          class="radar-axis-line"
        />
        <g v-for="axis in radarAxes" :key="`label-${axis.label}`">
          <text :x="axis.labelX" :y="axis.labelY" text-anchor="middle" class="radar-label">{{ axis.label }}</text>
        </g>
        <g v-for="series in normalizedSeries" :key="series.name">
          <polygon :points="radarPoints(series.values)" :fill="series.color" fill-opacity="0.14" :stroke="series.color" stroke-width="2" />
          <circle
            v-for="point in radarPointObjects(series.values)"
            :key="`${series.name}-${point.x}-${point.y}`"
            :cx="point.x"
            :cy="point.y"
            r="3"
            :fill="series.color"
          />
        </g>
      </svg>
      <div class="chart-legend">
        <span v-for="series in normalizedSeries" :key="series.name">
          <i :style="{ background: series.color }"></i>{{ series.name }}
        </span>
      </div>
      <div class="radar-insights">
        <div>
          <span>班级均值</span>
          <strong>{{ Math.round(metricAverage) }}%</strong>
        </div>
        <div>
          <span>优势维度</span>
          <strong>{{ strongestMetric.short }} {{ Math.round(strongestMetric.value) }}%</strong>
        </div>
        <div>
          <span>补强维度</span>
          <strong>{{ weakestMetric.short }} {{ Math.round(weakestMetric.value) }}%</strong>
        </div>
      </div>
    </section>

    <section class="visual-card">
      <div class="visual-head">
        <div>
          <strong>{{ wheelTitle }}</strong>
          <span>{{ wheelSubtitle }}</span>
        </div>
      </div>
      <svg class="wheel-svg" viewBox="0 0 320 300" role="img" aria-label="能力目标饼状图">
        <circle cx="160" cy="150" r="118" class="wheel-ring" />
        <circle cx="160" cy="150" r="88" class="wheel-ring muted" />
        <circle cx="160" cy="150" r="58" class="wheel-ring muted" />
        <g v-for="sector in wheelSectors" :key="sector.label">
          <path :d="sector.backgroundPath" class="wheel-sector-bg" />
          <path :d="sector.path" :fill="sector.color" fill-opacity="0.74" />
          <text :x="sector.labelX" :y="sector.labelY" text-anchor="middle" class="wheel-label">
            {{ sector.short }}
          </text>
          <text :x="sector.labelX" :y="sector.labelY + 16" text-anchor="middle" class="wheel-value">
            {{ Math.round(sector.value) }}%
          </text>
        </g>
        <circle cx="160" cy="150" r="45" class="wheel-center" />
        <text x="160" y="145" text-anchor="middle" class="wheel-center-title">能力目标</text>
        <text x="160" y="164" text-anchor="middle" class="wheel-center-sub">过程画像</text>
      </svg>
      <div class="wheel-summary">
        <div
          v-for="metric in normalizedMetrics"
          :key="`wheel-${metric.label}`"
          class="wheel-chip"
        >
          <span><i :style="{ background: metric.color }"></i>{{ metric.short }}</span>
          <strong>{{ Math.round(metric.value) }}%</strong>
        </div>
      </div>
    </section>

    <section class="visual-card">
      <div class="visual-head">
        <div>
          <strong>{{ distributionTitle }}</strong>
          <span>{{ distributionSubtitle }}</span>
        </div>
      </div>
      <div class="process-board">
        <div class="process-score">
          <svg class="score-gauge" viewBox="0 0 160 160" role="img" aria-label="过程健康度仪表盘">
            <circle cx="80" cy="80" r="58" class="gauge-bg" />
            <circle
              cx="80"
              cy="80"
              r="58"
              class="gauge-ring"
              :stroke-dasharray="gaugeDash"
              transform="rotate(-90 80 80)"
            />
            <text x="80" y="77" text-anchor="middle" class="gauge-value">{{ Math.round(processScore) }}</text>
            <text x="80" y="99" text-anchor="middle" class="gauge-label">{{ distributionCenterTitle }}</text>
          </svg>
          <div class="process-score-meta">
            <strong>{{ processStatus.title }}</strong>
            <span>{{ processStatus.detail }}</span>
          </div>
        </div>
        <div class="process-lanes">
          <div
            v-for="segment in segmentValues"
            :key="segment.label"
            class="process-lane"
            :class="segment.level"
          >
            <div class="lane-head">
              <span><i :style="{ background: segment.color }"></i>{{ segment.label }}</span>
              <strong>{{ Math.round(segment.value) }}%</strong>
            </div>
            <div class="lane-track"><b :style="{ width: `${segment.value}%`, background: segment.color }"></b></div>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Metric = {
  label: string
  short?: string
  text?: string | number
  width?: string
  value?: number
  color?: string
}

type Series = {
  name: string
  color: string
  values: number[]
}

type Segment = {
  label: string
  value: number
  color?: string
  reverse?: boolean
}

const props = defineProps<{
  metrics: Metric[]
  series?: Series[]
  segments?: Segment[]
  radarTitle?: string
  radarSubtitle?: string
  wheelTitle?: string
  wheelSubtitle?: string
  distributionTitle?: string
  distributionSubtitle?: string
  distributionCenterTitle?: string
  distributionCenterSub?: string
}>()

const palette = ['#0b63b6', '#14a46f', '#d8890b', '#7768e8', '#45b9c7', '#df6ea5']
const radarTitle = computed(() => props.radarTitle || '多维能力雷达')
const radarSubtitle = computed(() => props.radarSubtitle || '对比当前水平、目标线和薄弱群体')
const wheelTitle = computed(() => props.wheelTitle || '能力目标达成')
const wheelSubtitle = computed(() => props.wheelSubtitle || '按能力维度映射过程数据')
const distributionTitle = computed(() => props.distributionTitle || '学习结构分布')
const distributionSubtitle = computed(() => props.distributionSubtitle || '任务、测验、考勤、课堂和 AI 活动占比')
const distributionCenterTitle = computed(() => props.distributionCenterTitle || '结构')

const clamp = (value: number) => Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0))
const displayValue = (value: number, index = 0) => Math.max(12 + (index % 3) * 2, clamp(value))

function metricValue(metric: Metric, index: number) {
  if (typeof metric.value === 'number') return displayValue(metric.value, index)
  const widthValue = Number.parseFloat(String(metric.width || '').replace('%', ''))
  if (Number.isFinite(widthValue)) return displayValue(widthValue, index)
  const textValue = Number.parseFloat(String(metric.text || '').replace('%', ''))
  return displayValue(Number.isFinite(textValue) ? textValue : 60, index)
}

const normalizedMetrics = computed(() => {
  const base = props.metrics?.length ? props.metrics : [
    { label: '任务完成', short: '任务', value: 78 },
    { label: '知识掌握', short: '测验', value: 82 },
    { label: '学习投入', short: '考勤', value: 88 },
    { label: '课堂表现', short: '课堂', value: 84 },
    { label: 'AI 助学', short: 'AI', value: 72 },
  ]
  return base.map((item, index) => ({
    ...item,
    short: item.short || item.label.slice(0, 2),
    value: metricValue(item, index),
    color: item.color || palette[index % palette.length],
  }))
})

const metricAverage = computed(() => {
  if (!normalizedMetrics.value.length) return 0
  return normalizedMetrics.value.reduce((sum, item) => sum + item.value, 0) / normalizedMetrics.value.length
})

const fallbackMetric = { label: '暂无数据', short: '暂无', value: 0, color: palette[0] }
const strongestMetric = computed(() => [...normalizedMetrics.value].sort((a, b) => b.value - a.value)[0] || fallbackMetric)
const weakestMetric = computed(() => [...normalizedMetrics.value].sort((a, b) => a.value - b.value)[0] || fallbackMetric)

const normalizedSeries = computed(() => {
  const metricValues = normalizedMetrics.value.map(item => item.value)
  const given = props.series?.length ? props.series : [
    { name: '当前画像', color: '#0b63b6', values: metricValues },
    { name: '目标线', color: '#14a46f', values: metricValues.map(() => 88) },
    { name: '参照线', color: '#d8890b', values: metricValues.map((value, index) => displayValue(value * 0.82 + 10, index)) },
  ]
  return given.map(series => ({
    ...series,
    values: normalizedMetrics.value.map((_item, index) => displayValue(series.values[index] ?? metricValues[index] ?? 60, index)),
  }))
})

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  const rad = (Math.PI / 180) * angle
  return {
    x: cx + Math.cos(rad) * radius,
    y: cy + Math.sin(rad) * radius,
  }
}

const radarAngles = computed(() => normalizedMetrics.value.map((_item, index) => -90 + index * 360 / normalizedMetrics.value.length))

function radarPointObjects(values: number[]) {
  return values.map((value, index) => polarPoint(160, 126, 92 * displayValue(value, index) / 100, radarAngles.value[index] ?? -90))
}

function radarPoints(values: number[]) {
  return radarPointObjects(values).map(point => `${point.x},${point.y}`).join(' ')
}

const radarGrid = computed(() => [20, 40, 60, 80, 100].map(level => ({
  level,
  points: radarAngles.value.map(angle => {
    const point = polarPoint(160, 126, 92 * level / 100, angle)
    return `${point.x},${point.y}`
  }).join(' '),
})))

const radarAxes = computed(() => normalizedMetrics.value.map((metric, index) => {
  const angle = radarAngles.value[index] ?? -90
  const end = polarPoint(160, 126, 98, angle)
  const label = polarPoint(160, 126, 118, angle)
  return {
    label: metric.short,
    x: end.x,
    y: end.y,
    labelX: label.x,
    labelY: label.y + 4,
  }
}))

function sectorPath(index: number, total: number, inner: number, outer: number) {
  const startAngle = -90 + index * 360 / total + 2
  const endAngle = -90 + (index + 1) * 360 / total - 2
  const outerStart = polarPoint(160, 150, outer, startAngle)
  const outerEnd = polarPoint(160, 150, outer, endAngle)
  const innerEnd = polarPoint(160, 150, inner, endAngle)
  const innerStart = polarPoint(160, 150, inner, startAngle)
  const large = endAngle - startAngle > 180 ? 1 : 0
  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${outer} ${outer} 0 ${large} 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${inner} ${inner} 0 ${large} 0 ${innerStart.x} ${innerStart.y}`,
    'Z',
  ].join(' ')
}

const wheelSectors = computed(() => {
  const total = normalizedMetrics.value.length
  return normalizedMetrics.value.map((metric, index) => {
    const outer = 54 + (118 - 54) * metric.value / 100
    const labelAngle = -90 + (index + 0.5) * 360 / total
    const labelPoint = polarPoint(160, 150, 86, labelAngle)
    return {
      label: metric.label,
      short: metric.short,
      value: metric.value,
      color: metric.color,
      backgroundPath: sectorPath(index, total, 54, 118),
      path: sectorPath(index, total, 54, outer),
      labelX: labelPoint.x,
      labelY: labelPoint.y,
    }
  })
})

const segmentValues = computed(() => {
  const source: Segment[] = props.segments?.length
    ? props.segments
    : normalizedMetrics.value.map(item => ({ label: item.short, value: item.value, color: item.color, reverse: false }))
  return source.map((item, index) => {
    const healthValue = item.reverse ? 100 - clamp(item.value) : clamp(item.value)
    return {
      ...item,
      value: displayValue(item.value, index),
      color: item.color || palette[index % palette.length],
      healthValue,
      level: healthValue >= 85 ? 'good' : healthValue >= 70 ? 'stable' : 'warn',
    }
  })
})

const processScore = computed(() => {
  if (!segmentValues.value.length) return 0
  const total = segmentValues.value.reduce((sum, item) => sum + item.healthValue, 0)
  return clamp(total / segmentValues.value.length)
})

const gaugeCircumference = 2 * Math.PI * 58
const gaugeDash = computed(() => `${processScore.value / 100 * gaugeCircumference} ${gaugeCircumference}`)

const processStatus = computed(() => {
  const weakest = [...segmentValues.value].sort((a, b) => a.healthValue - b.healthValue)[0]
  if (processScore.value >= 90) {
    return { title: '运行良好', detail: `${weakest?.label || '各环节'}仍是主要观察点` }
  }
  if (processScore.value >= 75) {
    return { title: '整体可控', detail: `建议优先跟进${weakest?.label || '薄弱环节'}` }
  }
  return { title: '需要干预', detail: `${weakest?.label || '过程指标'}偏低，建议集中处理` }
})

</script>

<style scoped>
.visual-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.visual-card { min-width: 0; display: flex; flex-direction: column; background: #ffffff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 16px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.visual-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
.visual-head strong { display: block; color: #0f2f64; font-size: 15px; }
.visual-head span { display: block; color: #5b6f92; font-size: 11px; line-height: 1.5; margin-top: 4px; }
.radar-svg, .wheel-svg { width: 100%; height: 286px; display: block; flex: none; }
.radar-grid { fill: none; stroke: #d9e7f7; stroke-width: 1; }
.radar-axis-line { stroke: #e1ecf8; stroke-width: 1; }
.radar-label, .wheel-label { fill: #0f2f64; font-size: 10px; font-weight: 800; }
.wheel-value { fill: #5b6f92; font-size: 9px; font-weight: 800; }
.chart-legend { display: flex; flex-wrap: wrap; gap: 6px 10px; justify-content: center; margin-top: -2px; }
.chart-legend span { display: inline-flex; align-items: center; gap: 5px; color: #5b6f92; font-size: 11px; font-weight: 700; }
.chart-legend i { width: 8px; height: 8px; border-radius: 2px; }
.radar-insights { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #edf3fb; }
.radar-insights div { min-width: 0; border: 1px solid #e1ecf8; background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); border-radius: 8px; padding: 9px 10px; }
.radar-insights span { display: block; color: #5b6f92; font-size: 10px; font-weight: 700; margin-bottom: 4px; }
.radar-insights strong { display: block; color: #0f2f64; font-size: 13px; font-weight: 900; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wheel-ring { fill: none; stroke: #e1ecf8; stroke-width: 1; }
.wheel-ring.muted { stroke: #edf3fb; }
.wheel-sector-bg { fill: #f4f8fd; stroke: #ffffff; stroke-width: 1; }
.wheel-center { fill: #ffffff; stroke: #e1ecf8; stroke-width: 1; }
.wheel-center-title { fill: #0f2f64; font-size: 14px; font-weight: 900; }
.wheel-center-sub { fill: #5b6f92; font-size: 10px; font-weight: 700; }
.wheel-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 10px; }
.wheel-chip { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-width: 0; border: 1px solid #d9e7f7; background: #f8fbff; border-radius: 8px; padding: 8px 9px; }
.wheel-chip span { display: inline-flex; align-items: center; min-width: 0; gap: 6px; color: #5b6f92; font-size: 11px; font-weight: 800; }
.wheel-chip i { width: 8px; height: 8px; border-radius: 2px; flex: none; }
.wheel-chip strong { color: #0f2f64; font-size: 13px; font-weight: 900; flex: none; }
.wheel-chip:last-child:nth-child(odd) { grid-column: 1 / -1; }
.process-board { min-height: 238px; display: grid; grid-template-columns: 1fr; gap: 8px; align-items: center; }
.process-score { display: grid; justify-items: center; gap: 6px; }
.score-gauge { width: 118px; height: 118px; display: block; }
.gauge-bg, .gauge-ring { fill: none; stroke-width: 16; }
.gauge-bg { stroke: #edf3fb; }
.gauge-ring { stroke: #0b63b6; stroke-linecap: round; }
.gauge-value { fill: #0f2f64; font-size: 31px; font-weight: 900; }
.gauge-label { fill: #5b6f92; font-size: 11px; font-weight: 800; }
.process-score-meta { text-align: center; }
.process-score-meta strong { display: block; color: #0f2f64; font-size: 15px; }
.process-score-meta span { display: block; color: #5b6f92; font-size: 11px; line-height: 1.5; margin-top: 3px; }
.process-lanes { display: grid; gap: 7px; }
.process-lane { border: 1px solid #e1ecf8; background: #f8fbff; border-radius: 8px; padding: 8px 10px; }
.process-lane.warn { background: #fff7f6; border-color: #f4ceca; }
.process-lane.stable { background: #fffaf0; border-color: #f1dfb7; }
.process-lane.good { background: #f4fbf8; border-color: #cbead9; }
.lane-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: #5b6f92; font-size: 11px; font-weight: 800; margin-bottom: 6px; }
.lane-head span { display: inline-flex; align-items: center; min-width: 0; gap: 6px; }
.lane-head i { width: 8px; height: 8px; border-radius: 2px; flex: none; }
.lane-head strong { color: #0f2f64; }
.lane-track { height: 7px; background: #edf3fb; border-radius: 999px; overflow: hidden; }
.lane-track b { display: block; height: 100%; border-radius: inherit; }
@media (max-width: 1500px) {
  .visual-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 1120px) {
  .visual-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .visual-grid { grid-template-columns: 1fr; }
  .radar-insights, .wheel-summary { grid-template-columns: 1fr; }
  .process-board { grid-template-columns: 1fr; }
}
</style>
