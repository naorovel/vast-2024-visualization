<template>
  <div class="container">
    <h1>ShadGPT vs. BassLine: Bias Visualization</h1>
    <p>
      Welcome to the Bias Visualization Dashboard. Please select a visualization
      to view:
    </p>
    <ul>
      <li><NuxtLink to="/heatmap">View Heatmaps</NuxtLink></li>
      <li><NuxtLink to="/barchart">View Bar Charts</NuxtLink></li>
      <li><NuxtLink to="/scatterplot">View Scatter Plot</NuxtLink></li>
      <li><NuxtLink to="/sankey">View Sankey Diagram</NuxtLink></li>
    </ul>
  </div>
</template>

<script setup>
// No data fetching or rendering logic needed since there are no visualizations on this page
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
h1 {
  text-align: center;
  margin-bottom: 40px;
}
p {
  text-align: center;
  font-size: 1.2em;
  margin-bottom: 20px;
}
ul {
  list-style-type: none;
  padding: 0;
  text-align: center;
}
li {
  margin: 10px 0;
}
a {
  color: #1f77b4;
  text-decoration: none;
  font-size: 1.1em;
}
a:hover {
  text-decoration: underline;
}
</style>
