import { init, use } from 'echarts/core'
import { BarChart, ScatterChart, HeatmapChart, BoxplotChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent, MarkLineComponent, AriaComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'

use([BarChart, ScatterChart, HeatmapChart, BoxplotChart, GridComponent, TooltipComponent, VisualMapComponent, MarkLineComponent, AriaComponent, SVGRenderer])

export { init }
