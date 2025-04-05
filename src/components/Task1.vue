<template>
  <div>
    <!-- <pre>{{ JSON.stringify(data, null, 2) }}</pre> -->
    <div v-if="pending">Loading...</div>
    <!-- <div v-if="error">Error: {{ error.message }}</div> -->
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

type Bias = {
    positive_bias: [],
    lack_of_objectivity: [],
    authority_bias: [],
    halo_effect: [],
    social_desirability_bias: [],
    confirmation_bias: [],
    anchoring_bias: [],
    availability_bias: [],
    hindsight_bias: [],
    framing_bias: [],
    actor_observer_bias: [],
    fundamental_attribution_error_bias: [],
    self_serving_bias: [],
    bandwagon_effect: [],
    status_quo_bias: [],
    loss_aversion_bias: [],
    overconfidence_bias: [],
    illusion_of_control_bias: [],
    gambler_fallacy_bias: [],
    negative_bias: [],
    emotional_bias: [],
    recency_bias: [],
    sunk_cost_fallacy: [],
    stereotyping: [],
    selection_bias: [],
    presentation_bias: [],
    information_bias: [],
    experiential_bias: [],
    linguistic_bias: [],
    cultural_bias: []    
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
    bias_types: Bias
    
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
        target: link.target, 
        type: link.type,
        date_added: new Date(link._date_added),
        raw_source: link._raw_source,
        algorithm: link._algorithm,
        last_edited_by: link._last_edited_by,
        last_edited_date: new Date(link._last_edited_date),
        bias_types: link.bias_types
      }))
    }
  }
})

</script>