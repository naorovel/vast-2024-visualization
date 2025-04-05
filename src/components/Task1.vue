<template>
  <div>
    <!-- <pre>{{ JSON.stringify(data, null, 2) }}</pre> -->
    <div v-if="pending">Loading...</div>
    <!-- <div v-if="error">Error: {{ error.message }}</div> -->
    <div v-else-if="data">
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
    target: string,
    type: string,
    _date_added: Date,
    _raw_source: string,
    _algorithm: string,
    _last_edited_by: string,
    _last_edited_date: Date,
    bias_dict: Object
    
}

type GraphData = {
    nodes: Node[],
    links: Link[]
}

const API_URL = 'http://localhost:8000/graph'

const { data, pending, error} = useFetch<GraphData>(API_URL, { 
  headers: { 'Accept': '*/*' },
  transform: (res: any) => {
    console.log('Processed Links:', res.links) // Add this for debugging
    return {
      nodes: res.nodes?.map((node: Node) => ({ id: node.id })),
      links: res.links?.map((link: Link) => {
        // Preserve all bias types regardless of array contents
        const biasTypes = link.bias_dict || {};
        console.log('bias_types: ', link.bias_dict)
        // Convert to object with boolean presence indicators
        const biasPresence = Object.fromEntries(
          Object.entries(biasTypes).map(([key, val]) => 
            [key, val.length > 0]
          )
        );

        return {
          source: link.source, 
          target: link.target,
          type: link.type,
          date_added: new Date(link._date_added),
          raw_source: link._raw_source,
          algorithm: link._algorithm,
          last_edited_by: link._last_edited_by,
          last_edited_date: new Date(link._last_edited_date),
          bias_types: biasTypes,  // Keep original structure
          has_bias: biasPresence  // Add presence map for filtering
        }
      })
    }
  }
})

</script>