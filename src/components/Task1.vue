<template>
  <div>
    <pre>{{ JSON.stringify(data, null, 2) }}</pre>
    <div v-if="pending">Loading...</div>
    <div v-if="error">Error: {{ error.message }}</div>
    <div v-else-if="data">
      <!-- <pre>{{ data }}</pre> -->
      <!-- <div v-for="node in data.nodes" :key="node.id">
        Node: {{ node.id }}
      </div> -->
      <ForceGraph
      :nodes="data.nodes"
      :links="data.links"/>
    </div>
    <div v-else>No data available</div>
  </div>
</template>


<script setup lang="ts">

type Node = {
    id: string
}

type Link = {
    source: string,
    target: string
}

type GraphData = {
    nodes: Node[],
    links: Link[]
}

const API_URL = 'http://localhost:8000/graph'

const { data, pending, error} = useFetch<GraphData>(API_URL, { 
  headers: { 'Accept': '*/*' },
  transform: (res: any) => {
    console.log('API Response:', res) // Inspect this in browser
    return {
      nodes: res.nodes?.map((node: Node) => ({ id: node.id })),
      links: res.links?.map((link: Link) => ({ 
        source: link.source, 
        target: link.target 
      }))
    }
  }
})

</script>