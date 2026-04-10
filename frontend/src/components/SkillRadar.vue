<template>
  <div class="skill-radar">
    <!-- 雷达图区域 -->
    <div class="radar-container">
      <v-chart 
        :option="chartOption" 
        :autoresize="true"
        style="width: 100%; height: 400px;"
      />
    </div>
    
    <!-- 图例说明 -->
    <div class="legend">
      <div class="legend-item">
        <span class="legend-color" style="background: #409eff;"></span>
        <span>我的能力</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background: #67c23a;"></span>
        <span>行业平均</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent
])

const props = defineProps({
  radarData: {
    type: Object,
    required: true
  }
})

const chartOption = computed(() => {
  if (!props.radarData) return {}
  
  return {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      data: ['我的能力', '行业平均'],
      bottom: 10
    },
    radar: {
      indicator: props.radarData.indicators,
      center: ['50%', '50%'],
      radius: '60%',
      splitNumber: 5,
      axisName: {
        color: '#333',
        fontSize: 12,
        formatter: '{value}'
      },
      splitLine: {
        lineStyle: {
          color: '#e0e6ed'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(250,250,250,0.3)', 'rgba(240,240,240,0.3)']
        }
      }
    },
    series: [
      {
        name: '能力对比',
        type: 'radar',
        data: [
          {
            value: props.radarData.user_data,
            name: '我的能力',
            itemStyle: {
              color: '#409eff'
            },
            lineStyle: {
              width: 2,
              color: '#409eff'
            },
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.3)'
            }
          },
          {
            value: props.radarData.industry_data,
            name: '行业平均',
            itemStyle: {
              color: '#67c23a'
            },
            lineStyle: {
              width: 2,
              color: '#67c23a'
            },
            areaStyle: {
              color: 'rgba(103, 194, 58, 0.2)'
            }
          }
        ]
      }
    ]
  }
})
</script>

<style scoped>
.skill-radar {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.radar-container {
  margin-bottom: 20px;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}
</style>
