<template>
  <div class="container">
    <h1>ShadGPT vs. BassLine: Scatter Plot Visualization</h1>

    <!-- Chart Display Area -->
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="chart-container">
      <ClientOnly>
        <div id="scatter" class="plot"></div>
      </ClientOnly>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from "vue";

// State for loading, error, and data
const loading = ref(true);
const error = ref(null);
const confusionData = ref(null);
let Plotly = null;

// Dynamically import Plotly.js on the client side
if (process.client) {
  Plotly = await import("plotly.js-dist-min");
}

// Fetch data from the FastAPI endpoints
const fetchData = async () => {
  try {
    // Fetch confusion data (needed for scatter plot)
    const confusionResponse = await fetch("/api/confusion");
    if (!confusionResponse.ok) {
      throw new Error(`HTTP error! Status: ${confusionResponse.status}`);
    }
    const confusion = await confusionResponse.json();
    confusionData.value = confusion;
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
  const requiredElements = ["scatter"];
  for (const id of requiredElements) {
    if (!document.getElementById(id)) {
      console.error(`DOM element with id '${id}' not found.`);
      return;
    }
  }

  if (!process.client || !Plotly || !confusionData.value) {
    return;
  }

  // Extract data
  const shadgptConf = confusionData.value.shadgpt_confusion;
  const basslineConf = confusionData.value.bassline_confusion;

  // Render scatter plot
  renderScatter(shadgptConf, basslineConf);
};

// Scatter Plot: Detection Volume vs. Reliability
const renderScatter = (shadgptConf, basslineConf) => {
  const eventTypes = [
    ...new Set([
      ...Object.keys(shadgptConf.TP || {}),
      ...Object.keys(basslineConf.TP || {}),
    ]),
  ];

  if (eventTypes.length === 0) {
    console.error("No event types found for scatter plot.");
    return;
  }

  const scatterData = eventTypes.map((event) => {
    const shadgptTotal =
      (shadgptConf.TP[event] || 0) + (shadgptConf.FP[event] || 0);
    const shadgptTP = shadgptConf.TP[event] || 0;
    const shadgptFP = shadgptConf.FP[event] || 0;
    const shadgptTPRate = shadgptTotal > 0 ? shadgptTP / shadgptTotal : 0;

    const basslineTotal =
      (basslineConf.TP[event] || 0) + (basslineConf.FP[event] || 0);
    const basslineTP = basslineConf.TP[event] || 0;
    const basslineFP = basslineConf.FP[event] || 0;
    const basslineTPRate = basslineTotal > 0 ? basslineTP / basslineTotal : 0;

    const tpRateDiffShadGPT = shadgptTPRate - basslineTPRate;
    const shadgptBiasText =
      tpRateDiffShadGPT > 0
        ? `ShadGPT more reliable by ${tpRateDiffShadGPT.toFixed(4)}`
        : `BassLine more reliable by ${Math.abs(tpRateDiffShadGPT).toFixed(4)}`;

    const tpRateDiffBassLine = basslineTPRate - shadgptTPRate;
    const basslineBiasText =
      tpRateDiffBassLine > 0
        ? `BassLine more reliable by ${tpRateDiffBassLine.toFixed(4)}`
        : `ShadGPT more reliable by ${Math.abs(tpRateDiffBassLine).toFixed(4)}`;

    return {
      event,
      shadgpt: {
        total: shadgptTotal,
        tp: shadgptTP,
        fp: shadgptFP,
        tpRate: shadgptTPRate,
        biasText: shadgptBiasText,
      },
      bassline: {
        total: basslineTotal,
        tp: basslineTP,
        fp: basslineFP,
        tpRate: basslineTPRate,
        biasText: basslineBiasText,
      },
    };
  });

  const shadgptTrace = {
    x: scatterData.map((d) => d.shadgpt.total),
    y: scatterData.map((d) => d.shadgpt.tpRate),
    mode: "markers",
    name: "ShadGPT",
    marker: {
      size: scatterData.map((d) => d.shadgpt.fp / 1000),
      sizemode: "area",
      sizeref: 0.05,
      sizemin: 4,
      color: "#1f77b4",
    },
    customdata: scatterData.map((d) => {
      return (
        `Event: ${d.event}<br>` +
        `Total Detected: ${Math.round(d.shadgpt.total)}<br>` +
        `True Positives: ${Math.round(d.shadgpt.tp)}<br>` +
        `False Positives: ${Math.round(d.shadgpt.fp)}<br>` +
        `TP Rate: ${d.shadgpt.tpRate.toFixed(4)}<br>` +
        `Bias: ${d.shadgpt.biasText}`
      );
    }),
    hovertemplate: "%{customdata}<extra></extra>",
  };

  const basslineTrace = {
    x: scatterData.map((d) => d.bassline.total),
    y: scatterData.map((d) => d.bassline.tpRate),
    mode: "markers",
    name: "BassLine",
    marker: {
      size: scatterData.map((d) => d.bassline.fp / 1000),
      sizemode: "area",
      sizeref: 0.05,
      sizemin: 4,
      color: "#ff7f0e",
    },
    customdata: scatterData.map((d) => {
      return (
        `Event: ${d.event}<br>` +
        `Total Detected: ${Math.round(d.bassline.total)}<br>` +
        `True Positives: ${Math.round(d.bassline.tp)}<br>` +
        `False Positives: ${Math.round(d.bassline.fp)}<br>` +
        `TP Rate: ${d.bassline.tpRate.toFixed(4)}<br>` +
        `Bias: ${d.bassline.biasText}`
      );
    }),
    hovertemplate: "%{customdata}<extra></extra>",
  };

  const layout = {
    title: "Detection Volume vs. Reliability (Size = False Positives)",
    xaxis: {
      title: "Total Detected Events (TP + FP)",
    },
    yaxis: {
      title: "True Positive Rate (TP / (TP + FP))",
      range: [0, 1],
    },
    legend: { title: "Algorithm" },
    margin: { t: 100, b: 100, l: 100, r: 100 },
    plot_bgcolor: "#E5ECF6",
  };

  Plotly.newPlot("scatter", [shadgptTrace, basslineTrace], layout);
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
