<template>
  <div>
    <div style="margin-bottom: 20px; display: flex; align-items: center; flex-wrap: wrap;">
      <button @click="activeChart = 'sources'" :class="{ active: activeChart==='sources' }">Distribution of sources per analyst</button>
      <button @click="activeChart = 'algorithm'" :class="{ active: activeChart==='algorithm' }" style="margin-left: 10px;">Algorithm</button>
      <button @click="activeChart = 'eventTypes'" :class="{ active: activeChart==='eventTypes' }" style="margin-left: 10px;">Event types</button>
      <button @click="activeChart = 'timeSeries'" :class="{ active: activeChart==='timeSeries' }" style="margin-left: 10px;">Time series</button>
      <button @click="activeChart = 'eventCount'" :class="{ active: activeChart==='eventCount' }" style="margin-left: 10px;">Number of events</button>
    </div>

    <!-- Distribution of Sources Chart -->
    <div v-show="activeChart==='sources'">
      <div class="chart-header">
        <h2>Distribution of Sources Used by Analysts</h2>
        <button class="download-btn" @click="downloadChart('sources')">download</button>
      </div>
      <div ref="chartSources"></div>
    </div>

    <!-- Algorithm Chart -->
    <div v-show="activeChart==='algorithm'">
      <div class="chart-header">
        <h2>Algorithm Usage by Analysts</h2>
        <button class="download-btn" @click="downloadChart('algorithm')">download</button>
      </div>
      <div ref="chartAlgorithm"></div>
    </div>

    <!-- Event Types Chart -->
    <div v-show="activeChart==='eventTypes'">
      <div class="chart-header">
        <h2>Event types assigned by each analyst</h2>
        <button class="download-btn" @click="downloadChart('eventTypes')">download</button>
      </div>
      <div ref="chartEventTypes"></div>
    </div>

    <!-- Time Series Chart with Analyst Drop-Down -->
    <div v-show="activeChart==='timeSeries'">
      <div class="chart-header">
        <h2>Time series of entries per analyst over time</h2>
        <button class="download-btn" @click="downloadChart('timeSeries')">download</button>
      </div>
      <!-- Drop-down to select an analyst -->
      <select v-model="selectedAnalyst" style="margin-bottom: 10px;">
        <option value="all">All Analysts</option>
        <option v-for="analyst in timeSeriesAnalysts" :key="analyst" :value="analyst">{{ analyst }}</option>
      </select>
      <div ref="chartTimeSeries"></div>
    </div>

    <!-- Event Count Chart -->
    <div v-show="activeChart==='eventCount'">
      <div class="chart-header">
        <h2>Number of events recorded by each analyst</h2>
        <button class="download-btn" @click="downloadChart('eventCount')">download</button>
      </div>
      <div ref="chartEventCount"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const activeChart = ref('sources')
const selectedAnalyst = ref('all')
const timeSeriesAnalysts = ref([])

const chartSources = ref(null)
const chartAlgorithm = ref(null)
const chartEventTypes = ref(null)
const chartTimeSeries = ref(null)
const chartEventCount = ref(null)

let PlotlyRef = null

const paletteSources = [
  '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]
const paletteAlgorithm = [
  '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
  '#ffff33', '#a65628', '#f781bf', '#999999'
]
const paletteEventTypes = [
  '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99',
  '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a'
]

// Save layout and original traces for time series to update later
let originalTimeSeriesTraces = []
let layoutTimeSeries = {}

const downloadChart = (chartType) => {
  if (!PlotlyRef) return
  if (chartType === 'sources' && chartSources.value) {
    PlotlyRef.downloadImage(chartSources.value, { format: 'png', width: 800, height: 600, filename: 'sources_chart' })
  } else if (chartType === 'algorithm' && chartAlgorithm.value) {
    PlotlyRef.downloadImage(chartAlgorithm.value, { format: 'png', width: 800, height: 600, filename: 'algorithm_chart' })
  } else if (chartType === 'eventTypes' && chartEventTypes.value) {
    PlotlyRef.downloadImage(chartEventTypes.value, { format: 'png', width: 800, height: 600, filename: 'event_types_chart' })
  } else if (chartType === 'timeSeries' && chartTimeSeries.value) {
    PlotlyRef.downloadImage(chartTimeSeries.value, { format: 'png', width: 800, height: 600, filename: 'time_series_chart' })
  } else if (chartType === 'eventCount' && chartEventCount.value) {
    PlotlyRef.downloadImage(chartEventCount.value, { format: 'png', width: 800, height: 600, filename: 'event_count_chart' })
  }
}

onMounted(async () => {
  const Plotly = (await import('plotly.js-dist-min')).default
  PlotlyRef = Plotly

  const response = await fetch('/mc1.json')
  const jsonData = await response.json()
  const events = jsonData.links || []

  const dataMapSources = {}
  events.forEach(event => {
    const analyst = event._last_edited_by
    const source = event._raw_source
    if (!dataMapSources[analyst]) {
      dataMapSources[analyst] = {}
    }
    dataMapSources[analyst][source] = (dataMapSources[analyst][source] || 0) + 1
  })
  const sourcesSet = new Set()
  for (const analyst in dataMapSources) {
    for (const source in dataMapSources[analyst]) {
      sourcesSet.add(source)
    }
  }
  
  const uniqueSources = Array.from(sourcesSet)
  const analystsSources = Object.keys(dataMapSources)
  const tracesSources = uniqueSources.map((source, index) => {
    const counts = analystsSources.map(analyst => dataMapSources[analyst][source] || 0)
    return {
      x: counts,
      y: analystsSources,
      name: source,
      type: 'bar',
      orientation: 'h',
      marker: { color: paletteSources[index % paletteSources.length] }
    }
  })
  const baseWidth = 1694;
  const baseHeight = 600;
  const layoutSources = {
    title: 'Distribution of Sources Used by Analysts',
    barmode: 'stack',
    xaxis: { title: 'Count' },
    yaxis: { title: 'Analyst' },
    legend: { title: { text: 'Source' }, x: 1.05, y: 1 },
    margin: { l: 100, r: 100, t: 50, b: 50 },
    width: baseWidth,
    height: baseHeight
  }
  Plotly.newPlot(chartSources.value, tracesSources, layoutSources)
  

  const dataMapAlgorithm = {}
  events.forEach(event => {
    const analyst = event._last_edited_by
    const algorithm = event._algorithm
    if (!dataMapAlgorithm[analyst]) {
      dataMapAlgorithm[analyst] = {}
    }
    dataMapAlgorithm[analyst][algorithm] = (dataMapAlgorithm[analyst][algorithm] || 0) + 1
  })
  const algorithmsSet = new Set()
  for (const analyst in dataMapAlgorithm) {
    for (const algorithm in dataMapAlgorithm[analyst]) {
      algorithmsSet.add(algorithm)
    }
  }
  const uniqueAlgorithms = Array.from(algorithmsSet)
  const analystsAlgorithm = Object.keys(dataMapAlgorithm)
  const tracesAlgorithm = uniqueAlgorithms.map((algorithm, index) => {
    const counts = analystsAlgorithm.map(analyst => dataMapAlgorithm[analyst][algorithm] || 0)
    return {
      x: analystsAlgorithm,
      y: counts,
      name: algorithm,
      type: 'bar',
      marker: { color: paletteAlgorithm[index % paletteAlgorithm.length] }
    }
  })
  const layoutAlgorithm = {
    title: 'Algorithm Usage by Analysts',
    barmode: 'group',
    xaxis: { title: 'Analyst' },
    yaxis: { title: 'Count' },
    legend: { title: { text: 'Algorithm' }, x: 1.05, y: 1 },
    margin: { l: 100, r: 100, t: 50, b: 150 },
    width: baseWidth,
    height: baseHeight
  }
  Plotly.newPlot(chartAlgorithm.value, tracesAlgorithm, layoutAlgorithm)

  const dataMapEventTypes = {}
  events.forEach(event => {
    const analyst = event._last_edited_by
    const eventType = event.type
    if (!dataMapEventTypes[analyst]) {
      dataMapEventTypes[analyst] = {}
    }
    dataMapEventTypes[analyst][eventType] = (dataMapEventTypes[analyst][eventType] || 0) + 1
  })
  const typesSet = new Set()
  for (const analyst in dataMapEventTypes) {
    for (const type in dataMapEventTypes[analyst]) {
      typesSet.add(type)
    }
  }
  const uniqueEventTypes = Array.from(typesSet)
  const analystsEvent = Object.keys(dataMapEventTypes)
  const eventMatrix = analystsEvent.map(analyst => {
    return uniqueEventTypes.map(eventType => dataMapEventTypes[analyst][eventType] || 0)
  })
  const traceEventTypes = {
    x: uniqueEventTypes,
    y: analystsEvent,
    z: eventMatrix,
    type: 'heatmap',
    colorscale: 'YlGnBu',
    colorbar: {
      title: 'Event Count',
      titleside: 'right'
    }
  }
  const layoutEventTypes = {
    title: 'Event Types Heatmap by Analyst',
    xaxis: {
      title: 'Event Type',
      tickangle: -45,
      automargin: true
    },
    yaxis: { title: 'Analyst' },
    margin: { l: 120, r: 120, t: 60, b: 80 },
    width: baseWidth,
    height: baseHeight
  }
  Plotly.newPlot(chartEventTypes.value, [traceEventTypes], layoutEventTypes)
  
  const dataMapTime = {}
  events.forEach(event => {
    const analyst = event._last_edited_by
    const dateObj = new Date(event._date_added)
    const dateStr = dateObj.toISOString().split('T')[0]
    if (!dataMapTime[dateStr]) {
      dataMapTime[dateStr] = {}
    }
    dataMapTime[dateStr][analyst] = (dataMapTime[dateStr][analyst] || 0) + 1
  })
  const uniqueDates = Object.keys(dataMapTime).sort()
  const analystsTime = Array.from(new Set(events.map(e => e._last_edited_by)))
  // Save the list of analysts for the drop-down
  timeSeriesAnalysts.value = analystsTime
  originalTimeSeriesTraces = analystsTime.map(analyst => {
    const counts = uniqueDates.map(date => dataMapTime[date][analyst] || 0)
    return {
      x: uniqueDates,
      y: counts,
      name: analyst,
      type: 'scatter',
      mode: 'lines+markers'
    }
  })
  layoutTimeSeries = {
    title: 'Entries Over Time per Analyst',
    xaxis: { title: 'Date' },
    yaxis: { title: 'Number of Entries' },
    legend: { title: { text: 'Analyst' }, x: 1.05, y: 1 },
    margin: { l: 100, r: 100, t: 50, b: 50 },
    width: baseWidth,
    height: baseHeight
  }
  // Initially plot all analysts
  Plotly.newPlot(chartTimeSeries.value, originalTimeSeriesTraces, layoutTimeSeries)

  const counts = {}
  events.forEach(event => {
    const analyst = event._last_edited_by
    counts[analyst] = (counts[analyst] || 0) + 1
  })
  // Sort analysts by count (least -> most)
  const sortedEntries = Object.entries(counts).sort((a, b) => a[1] - b[1])
  const sortedAnalysts = sortedEntries.map(entry => entry[0])
  const sortedEventCounts = sortedEntries.map(entry => entry[1])
  const traceEventCount = {
    x: sortedAnalysts,
    y: sortedEventCounts,
    type: 'bar',
    marker: { color: '#4a90e2' }
  }
  const layoutEventCount = {
    title: 'Number of Events Recorded by Each Analyst',
    xaxis: {
      title: 'Analyst',
      tickangle: -45
    },
    yaxis: {
      title: 'Number of Events'
    },
    margin: { t: 50, b: 100, l: 70, r: 20 },
    width: baseWidth,
    height: baseHeight
  }
  Plotly.newPlot(chartEventCount.value, [traceEventCount], layoutEventCount)
})

// Watch for changes in selectedAnalyst to update the time series chart
watch(selectedAnalyst, (newVal) => {
  let updatedTraces;
  if (newVal === 'all') {
    updatedTraces = originalTimeSeriesTraces;
  } else {
    updatedTraces = originalTimeSeriesTraces.filter(trace => trace.name === newVal);
  }
  PlotlyRef.react(chartTimeSeries.value, updatedTraces, layoutTimeSeries);
})
</script>

<style scoped>
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

button {
  padding: 8px 16px;
  border: none;
  background-color: #eee;
  color: #333;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s, color 0.3s;
  margin-top: 5px;
}

button.active {
  background-color: #4a90e2;
  color: #fff;
}

button:hover {
  background-color: #ddd;
}

.download-btn {
  padding: 6px 12px;
  font-size: 14px;
  background-color: #28a745;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.download-btn:hover {
  background-color: #218838;
}

select {
  padding: 6px;
  margin-bottom: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
}
</style>