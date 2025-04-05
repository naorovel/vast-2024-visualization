<template>
  <div class="container">
    <h1>ShadGPT vs. BassLine: Bar Chart Visualizations</h1>

    <!-- Tab Navigation -->
    <div class="tabs">
      <button
        :class="{ active: activeTab === 'barchart1' }"
        @click="activeTab = 'barchart1'"
      >
        Total Detected Events
      </button>
      <button
        :class="{ active: activeTab === 'barchart2' }"
        @click="activeTab = 'barchart2'"
      >
        False Positive Counts
      </button>
    </div>

    <!-- Chart Display Area -->
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="chart-container">
      <ClientOnly>
        <!-- Show Bar Chart 1 if activeTab is 'barchart1' -->
        <div v-if="activeTab === 'barchart1'" id="barchart1" class="plot"></div>
        <!-- Show Bar Chart 2 if activeTab is 'barchart2' -->
        <div v-if="activeTab === 'barchart2'" id="barchart2" class="plot"></div>
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

// State for active tab
const activeTab = ref("barchart1"); // Default to Bar Chart 1

// Dynamically import Plotly.js on the client side
if (process.client) {
  Plotly = await import("plotly.js-dist-min");
}

// Fetch data from the FastAPI endpoints
const fetchData = async () => {
  try {
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

// Function to render visualizations based on the active tab
const renderVisualizations = () => {
  // Check if the DOM element for the active tab exists
  const currentChartId = activeTab.value;
  if (!document.getElementById(currentChartId)) {
    console.error(`DOM element with id '${currentChartId}' not found.`);
    return;
  }

  if (!process.client || !Plotly || !confusionData.value) {
    return;
  }

  const shadgptConf = confusionData.value.shadgpt_confusion;
  const basslineConf = confusionData.value.bassline_confusion;

  // Render only the active chart
  if (activeTab.value === "barchart1") {
    renderBarChart1(shadgptConf, basslineConf);
  } else if (activeTab.value === "barchart2") {
    renderBarChart2(shadgptConf, basslineConf);
  }
};

// Bar Chart 1: Total Detected Events by Algorithm
const renderBarChart1 = (shadgptConf, basslineConf) => {
  const eventTypes = [
    ...new Set([
      ...Object.keys(shadgptConf.FP || {}),
      ...Object.keys(basslineConf.FP || {}),
    ]),
  ];

  if (eventTypes.length === 0) {
    console.error("No event types found for Bar Chart 1.");
    return;
  }

  const totalData = eventTypes.map((event) => ({
    event,
    ShadGPT: (shadgptConf.TP[event] || 0) + (shadgptConf.FP[event] || 0),
    BassLine: (basslineConf.TP[event] || 0) + (basslineConf.FP[event] || 0),
    shadgptTP: shadgptConf.TP[event] || 0,
    shadgptFP: shadgptConf.FP[event] || 0,
    basslineTP: basslineConf.TP[event] || 0,
    basslineFP: basslineConf.FP[event] || 0,
  }));

  const shadgptTotalTrace = {
    x: eventTypes,
    y: totalData.map((d) => d.ShadGPT),
    name: "ShadGPT",
    type: "bar",
    marker: { color: "#1f77b4" },
    customdata: totalData.map((d) => {
      const total = d.ShadGPT;
      const tp = d.shadgptTP;
      const fp = d.shadgptFP;
      const fpRate = total > 0 ? fp / total : 0;
      return (
        `Total Events: ${Math.round(total)}<br>` +
        `True Positives: ${Math.round(tp)}<br>` +
        `False Positives: ${Math.round(fp)}<br>` +
        `FP Rate: ${fpRate.toFixed(2)}`
      );
    }),
    hovertemplate: "%{customdata}<extra></extra>",
  };

  const basslineTotalTrace = {
    x: eventTypes,
    y: totalData.map((d) => d.BassLine),
    name: "BassLine",
    type: "bar",
    marker: { color: "#ff7f0e" },
    customdata: totalData.map((d) => {
      const total = d.BassLine;
      const tp = d.basslineTP;
      const fp = d.basslineFP;
      const fpRate = total > 0 ? fp / total : 0;
      return (
        `Total Events: ${Math.round(total)}<br>` +
        `True Positives: ${Math.round(tp)}<br>` +
        `False Positives: ${Math.round(fp)}<br>` +
        `FP Rate: ${fpRate.toFixed(2)}`
      );
    }),
    hovertemplate: "%{customdata}<extra></extra>",
  };

  const totalLayout = {
    title: "Total Detected Events by Algorithm (Higher = More Extraction)",
    xaxis: {
      title: "Event Type",
      tickangle: 45,
      automargin: true,
    },
    yaxis: {
      title: "Number of Events",
    },
    barmode: "group",
    margin: { t: 100, b: 150, l: 100, r: 100 },
    plot_bgcolor: "#E5ECF6",
  };

  Plotly.newPlot(
    "barchart1",
    [shadgptTotalTrace, basslineTotalTrace],
    totalLayout
  );
};

// Bar Chart 2: False Positive Counts by Algorithm
const renderBarChart2 = (shadgptConf, basslineConf) => {
  const eventTypes = [
    ...new Set([
      ...Object.keys(shadgptConf.FP || {}),
      ...Object.keys(basslineConf.FP || {}),
    ]),
  ];

  if (eventTypes.length === 0) {
    console.error("No event types found for Bar Chart 2.");
    return;
  }

  const fpData = eventTypes.map((event) => ({
    event,
    ShadGPT: shadgptConf.FP[event] || 0,
    BassLine: basslineConf.FP[event] || 0,
  }));

  const shadgptFPTrace = {
    x: eventTypes,
    y: fpData.map((d) => d.ShadGPT),
    name: "ShadGPT",
    type: "bar",
    marker: { color: "#1f77b4" },
    customdata: fpData.map((d) => {
      const fp = d.ShadGPT;
      const diff = d.BassLine - fp;
      const biasText =
        diff > 0
          ? `BassLine over-extracts by ${Math.round(diff)} more events`
          : diff < 0
          ? `ShadGPT over-extracts by ${Math.round(-diff)} more events`
          : "No over-extraction bias";
      return (
        `False Positives: ${Math.round(fp)}<br>` +
        `Difference: ${Math.round(diff)}<br>` +
        `Bias: ${biasText}`
      );
    }),
    hovertemplate: "%{customdata}<extra></extra>",
  };

  const basslineFPTrace = {
    x: eventTypes,
    y: fpData.map((d) => d.BassLine),
    name: "BassLine",
    type: "bar",
    marker: { color: "#ff7f0e" },
    customdata: fpData.map((d) => {
      const fp = d.BassLine;
      const diff = fp - d.ShadGPT;
      const biasText =
        diff > 0
          ? `BassLine over-extracts by ${Math.round(diff)} more events`
          : diff < 0
          ? `ShadGPT over-extracts by ${Math.round(-diff)} more events`
          : "No over-extraction bias";
      return (
        `False Positives: ${Math.round(fp)}<br>` +
        `Difference: ${Math.round(diff)}<br>` +
        `Bias: ${biasText}`
      );
    }),
    hovertemplate: "%{customdata}<extra></extra>",
  };

  const fpLayout = {
    title:
      "False Positive Counts by Algorithm (Higher = More Over-Extraction Bias)",
    xaxis: {
      title: "Event Type",
      tickangle: 45,
      automargin: true,
    },
    yaxis: {
      title: "Number of False Positives",
    },
    barmode: "group",
    margin: { t: 100, b: 150, l: 100, r: 100 },
    plot_bgcolor: "#E5ECF6",
  };

  Plotly.newPlot("barchart2", [shadgptFPTrace, basslineFPTrace], fpLayout);
};

// Watch the loading state and activeTab to render visualizations
watch([loading, activeTab], async ([newLoading, newTab]) => {
  if (newLoading === false && !error.value) {
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

/* Tabs Styling */
.tabs {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.tabs button {
  padding: 12px 24px;
  margin: 0 5px;
  font-size: 1em;
  font-weight: 500;
  color: #555;
  background-color: #f0f0f0;
  border: none;
  border-radius: 5px 5px 0 0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tabs button.active {
  background-color: #1f77b4;
  color: white;
  font-weight: 600;
}

.tabs button:hover:not(.active) {
  background-color: #e0e0e0;
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
