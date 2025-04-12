<template>
  <div class="container">
    <h1>ShadGPT vs. BassLine: Sankey Diagram Visualization</h1>

    <!-- Chart Display Area -->
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="chart-container">
      <ClientOnly>
        <div id="sankey" class="plot"></div>
      </ClientOnly>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from "vue";

// State for loading, error, and data
const loading = ref(true);
const error = ref(null);
const sankeyData = ref(null);
let Plotly = null;

// Dynamically import Plotly.js on the client side
if (process.client) {
  Plotly = await import("plotly.js-dist-min");
}

// Fetch data from the FastAPI endpoints
const fetchData = async () => {
  try {
    // Fetch Sankey data
    const sankeyResponse = await fetch("/api/sankey");
    if (!sankeyResponse.ok) {
      throw new Error(`HTTP error! Status: ${sankeyResponse.status}`);
    }
    const sankey = await sankeyResponse.json();
    sankeyData.value = sankey;
  } catch (err) {
    error.value = "Failed to fetch data: " + err.message;
    console.error("Fetch Error:", err.message);
  } finally {
    loading.value = false;
  }
};

// Function to render visualizations
const renderVisualizations = () => {
  // Check if DOM elements exist
  const requiredElements = ["sankey"];
  for (const id of requiredElements) {
    if (!document.getElementById(id)) {
      console.error(`DOM element with id '${id}' not found.`);
      return;
    }
  }

  if (!process.client || !Plotly || !sankeyData.value) {
    return;
  }

  // Extract data
  const sankey = sankeyData.value;

  // Render Sankey diagram
  renderSankey(sankey);
};

// Sankey Diagram: Sentiment Influence on Over-Extraction Bias
const renderSankey = (sankey) => {
  const sentiments = [...new Set(sankey.map((d) => d.sentiment))];
  const edgeTypes = [...new Set(sankey.map((d) => d.edge_type))];
  const algorithms = [...new Set(sankey.map((d) => d.algorithm))];
  const nodes = [...sentiments, ...edgeTypes, ...algorithms];
  const nodeDict = Object.fromEntries(nodes.map((node, i) => [node, i]));

  const groupedData = {};
  sankey.forEach((d) => {
    const key = `${d.sentiment}|${d.edge_type}|${d.algorithm}`;
    if (!groupedData[key]) {
      groupedData[key] = {
        sentiment: d.sentiment,
        edge_type: d.edge_type,
        algorithm: d.algorithm,
        total_count: 0,
        tp_count: 0,
        fp_count: 0,
      };
    }
    groupedData[key].total_count += d.total_count;
    groupedData[key].tp_count += d.tp_count;
    groupedData[key].fp_count += d.fp_count;
  });

  const sankeyLinks = Object.values(groupedData);

  const hoverData = [];
  sankeyLinks.forEach((link) => {
    const sentiment = link.sentiment;
    const event = link.edge_type;
    const algo = link.algorithm;
    const total = link.total_count;
    const tp = link.tp_count;
    const fp = link.fp_count;
    const fpRate = total > 0 ? fp / total : 0;

    const otherAlgo = algo === "ShadGPT" ? "BassLine" : "ShadGPT";
    const otherLink = sankeyLinks.find(
      (l) =>
        l.sentiment === sentiment &&
        l.edge_type === event &&
        l.algorithm === otherAlgo
    );
    const biasDiff = otherLink ? fp - otherLink.fp_count : 0;
    const biasText =
      biasDiff > 0
        ? `${algo} over-extracts by ${Math.round(biasDiff)} more`
        : biasDiff < 0
        ? `${otherAlgo} over-extracts by ${Math.round(-biasDiff)} more`
        : "No over-extraction bias between algorithms";

    const hoverText =
      `Sentiment: ${sentiment}<br>` +
      `Event: ${event}<br>` +
      `Algorithm: ${algo}<br>` +
      `Total Detected: ${Math.round(total)}<br>` +
      `True Positives: ${Math.round(tp)}<br>` +
      `False Positives: ${Math.round(fp)}<br>` +
      `FP Rate: ${fpRate.toFixed(2)}<br>` +
      `Bias: ${biasText}`;
    hoverData.push(hoverText);
  });

  const sources = [];
  const targets = [];
  const values = [];
  const colors = [];
  const customData = [];

  sankeyLinks.forEach((link, index) => {
    const sentiment = link.sentiment;
    const event = link.edge_type;
    const algo = link.algorithm;
    const fp = link.fp_count;

    const linkColor =
      sentiment === "Negative"
        ? "#FFB6C1"
        : sentiment === "Positive"
        ? "#ADD8E6"
        : "#D3D3D3";

    sources.push(nodeDict[sentiment]);
    targets.push(nodeDict[event]);
    values.push(fp * 2);
    colors.push(linkColor);
    customData.push(hoverData[index]);

    sources.push(nodeDict[event]);
    targets.push(nodeDict[algo]);
    values.push(fp * 2);
    colors.push(linkColor);
    customData.push(hoverData[index]);
  });

  const data = [
    {
      type: "sankey",
      node: {
        label: nodes,
        hoverinfo: "none",
      },
      link: {
        source: sources,
        target: targets,
        value: values,
        color: colors,
        customdata: customData,
        hovertemplate: "%{customdata}<extra></extra>",
        hoverinfo: "all",
      },
    },
  ];

  const layout = {
    title:
      "Top 5 Events by False Positives: Sentiment Influence on Over-Extraction Bias",
    font: { size: 10 },
    margin: { t: 100, b: 100, l: 100, r: 100 },
  };

  Plotly.newPlot("sankey", data, layout);
};

// Watch the loading state to render visualizations after DOM is ready
watch(loading, async (newValue) => {
  if (newValue === false && !error.value) {
    await nextTick();
    setTimeout(() => {
      renderVisualizations();
    }, 100); // Small delay to ensure DOM is ready
  }
});

// Fetch data when the component is mounted
onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.container {
  max-width: 100%;
  margin: 0;
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
  font-size: 1.8em;
  color: #333;
}

/* Chart Container Styling */
.chart-container {
  flex: 1;
  width: 100%;
  overflow: hidden;
}

.plot {
  width: 100%;
  height: 100%;
  border: 1px solid #ddd;
  border-radius: 5px;
}

/* Loading and Error States */
.loading,
.error {
  text-align: center;
  font-size: 1.2em;
  color: #666;
  margin-top: 20px;
}

.error {
  color: #d9534f;
}
</style>
