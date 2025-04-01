<template>
  <div>
    <div v-if="pending">Loading graph data...</div>
    <div v-else-if="error">Error loading data: {{ error }}</div>
    <div v-else-if="data">
      <div class="graph-info">
        Loaded {{ data.nodes.length }} nodes and {{ data.links.length }} links
      </div>
      <ForceGraph
        :nodes="data.nodes"
        :links="data.links"
      />
    </div>
    <div v-else>No data available</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ForceGraph from './ForceGraph.vue'

type Node = { id: string }
type Link = { source: string; target: string }
type GraphData = { nodes: Node[]; links: Link[] }

const GRAPH_API_URL = 'http://localhost:8000/graph'

const data = ref<GraphData | null>(null)
const pending = ref(true)
const error = ref<Error | null>(null)

onMounted(async () => {
  try {
    const response = await $fetch(GRAPH_API_URL, {
      headers: { Accept: '*/*' },
      timeout: 90000 // 30 seconds timeout
    })

    // Process data in smaller chunks to avoid blocking UI
    const processData = async (res: any): Promise<GraphData> => {
      const nodes = []
      const links = []
      
      // Process nodes in batches
      for (let i = 0; i < res.nodes.length; i++) {
        nodes.push({ id: res.nodes[i].id })
        if (i % 1000 === 0) await new Promise(resolve => setTimeout(resolve, 0))
      }

      // Process links in batches
      for (let i = 0; i < res.links.length; i++) {
        links.push({
          source: res.links[i].source,
          target: res.links[i].target
        })
        if (i % 1000 === 0) await new Promise(resolve => setTimeout(resolve, 0))
      }

      return { nodes, links }
    }

    data.value = await processData(response)
  } catch (err) {
    error.value = err
    console.error('Fetch error:', err)
  } finally {
    pending.value = false
  }
})
</script>