<template>
  <div class="container">
    <h1>ShadGPT vs. BassLine: Heatmap Visualizations</h1>

    <!-- Tab Navigation -->
    <div class="tabs">
      <button
        :class="{ active: activeTab === 'heatmap1' }"
        @click="activeTab = 'heatmap1'"
      >
        Over-Extraction Rate
      </button>
      <button
        :class="{ active: activeTab === 'heatmap2' }"
        @click="activeTab = 'heatmap2'"
      >
        Bias Difference
      </button>
    </div>

    <!-- Chart Display Area -->
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="chart-container">
      <ClientOnly>
        <!-- Show Heatmap 1 if activeTab is 'heatmap1' -->
        <div v-if="activeTab === 'heatmap1'" id="heatmap1" class="plot"></div>
        <!-- Show Heatmap 2 if activeTab is 'heatmap2' -->
        <div v-if="activeTab === 'heatmap2'" id="heatmap2" class="plot"></div>
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
const fpRatesData = ref(null);
let Plotly = null;

// State for active tab
const activeTab = ref("heatmap1"); // Default to Heatmap 1

// Dynamically import Plotly.js on the client side
if (process.client) {
  Plotly = await import("plotly.js-dist-min");
}

// Fetch data from the FastAPI endpoints
const fetchData = async () => {
  try {
    // Fetch confusion data
    const confusionResponse = await fetch("/api/confusion");
    if (!confusionResponse.ok) {
      throw new Error(`HTTP error! Status: ${confusionResponse.status}`);
    }
    const confusion = await confusionResponse.json();
    confusionData.value = confusion;

    // Fetch FP rates data
    const fpRatesResponse = await fetch("/api/fp_rates");
    if (!fpRatesResponse.ok) {
      throw new Error(`HTTP error! Status: ${fpRatesResponse.status}`);
    }
    const fpRates = await fpRatesResponse.json();
    fpRatesData.value = fpRates;
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

  if (
    !process.client ||
    !Plotly ||
    !confusionData.value ||
    !fpRatesData.value
  ) {
    return;
  }

  const shadgptConf = confusionData.value.shadgpt_confusion;
  const basslineConf = confusionData.value.bassline_confusion;
  const shadgptFpRate = fpRatesData.value.shadgpt_fp_rate;
  const basslineFpRate = fpRatesData.value.bassline_fp_rate;

  // Render only the active heatmap
  if (activeTab.value === "heatmap1") {
    renderHeatmap1(shadgptFpRate, basslineFpRate);
  } else if (activeTab.value === "heatmap2") {
    renderHeatmap2(shadgptFpRate, basslineFpRate, shadgptConf, basslineConf);
  }
};

// Heatmap 1: Over-Extraction Rate by Algorithm
const renderHeatmap1 = (shadgptFpRate, basslineFpRate) => {
  const eventTypes = Object.keys(shadgptFpRate).filter(
    (event) => event in basslineFpRate
  );

  const shadgptValues = eventTypes.map((event) => shadgptFpRate[event]);
  const basslineValues = eventTypes.map((event) => basslineFpRate[event]);
  const zData = [shadgptValues, basslineValues];

  const textData = [
    shadgptValues.map((v) => v.toFixed(4)),
    basslineValues.map((v) => v.toFixed(4)),
  ];

  const hoverText = eventTypes.map((event, i) => {
    const shadgptFP = shadgptValues[i];
    const basslineFP = basslineValues[i];
    const diff = basslineFP - shadgptFP;
    return `Event: ${event}<br>ShadGPT FP Rate: ${shadgptFP.toFixed(
      4
    )}<br>BassLine FP Rate: ${basslineFP.toFixed(
      4
    )}<br>Difference: ${diff.toFixed(4)}`;
  });

  const data = [
    {
      z: zData,
      x: eventTypes,
      y: ["ShadGPT", "BassLine"],
      type: "heatmap",
      colorscale: "Reds",
      zmin: 0,
      zmax: 1,
      showscale: true,
      colorbar: { title: "FP Rate (0-1)" },
      text: textData,
      texttemplate: "%{text}",
      textfont: {
        size: 12,
        color: "black",
      },
      hovertext: [hoverText, hoverText],
      hoverinfo: "text",
    },
  ];

  const layout = {
    title:
      "Over-Extraction Rate by Algorithm (Higher = More Over-Extraction Bias)",
    xaxis: {
      title: "Event Type",
      tickangle: 45,
      automargin: true,
    },
    yaxis: {
      title: "Algorithm",
      tickmode: "array",
      tickvals: ["ShadGPT", "BassLine"],
      ticktext: ["ShadGPT", "BassLine"],
    },
    margin: { t: 100, b: 150, l: 100, r: 100 },
    plot_bgcolor: "#E5ECF6",
    grid: {
      xgap: 0.1,
      ygap: 0.1,
    },
    shapes: eventTypes
      .map((_, i) => ({
        type: "line",
        x0: i - 0.5,
        x1: i - 0.5,
        y0: -0.5,
        y1: 1.5,
        xref: "x",
        yref: "y",
        line: { color: "white", width: 1 },
      }))
      .concat([
        {
          type: "line",
          x0: -0.5,
          x1: eventTypes.length - 0.5,
          y0: 0.5,
          y1: 0.5,
          xref: "x",
          yref: "y",
          line: { color: "white", width: 1 },
        },
      ]),
  };

  Plotly.newPlot("heatmap1", data, layout);
};

// Heatmap 2: Bias Difference (BassLine - ShadGPT)
const renderHeatmap2 = (
  shadgptFpRate,
  basslineFpRate,
  shadgptConf,
  basslineConf
) => {
  const descriptiveEventTypes = Object.keys(shadgptFpRate).filter(
    (event) => event in basslineFpRate
  );

  const eventTypes = descriptiveEventTypes;

  if (eventTypes.length === 0) {
    console.error(
      "No event types found for Heatmap 2. Check shadgptFpRate and basslineFpRate data."
    );
    return;
  }

  const diffValues = eventTypes.map(
    (event) => basslineFpRate[event] - shadgptFpRate[event]
  );
  const zData = [diffValues];

  const textData = [diffValues.map((v) => v.toFixed(4))];

  const hoverText = eventTypes.map((event, i) => {
    const diff = diffValues[i];
    const shadgptFP =
      shadgptConf.FP && event in shadgptConf.FP
        ? Number(shadgptConf.FP[event])
        : 0;
    const basslineFP =
      basslineConf.FP && event in basslineConf.FP
        ? Number(basslineConf.FP[event])
        : 0;
    const fpDiff = basslineFP - shadgptFP;
    return (
      `Difference: ${diff.toFixed(4)}<br>` +
      `ShadGPT FP: ${Math.round(shadgptFP)}<br>` +
      `BassLine FP: ${Math.round(basslineFP)}<br>` +
      `Bias: BassLine over-extracts by ${Math.round(fpDiff)} more events`
    );
  });

  const data = [
    {
      z: zData,
      x: eventTypes,
      y: ["BassLine - ShadGPT"],
      type: "heatmap",
      colorscale: "RdBu",
      zmid: 0,
      showscale: true,
      colorbar: { title: "FP Rate Difference" },
      text: textData,
      texttemplate: "%{text}",
      textfont: {
        size: 12,
        color: "black",
      },
      hovertext: [hoverText],
      hoverinfo: "text",
    },
  ];

  const layout = {
    title: "Bias Difference (BassLine - ShadGPT): Over-Extraction Tendency",
    xaxis: {
      title: "Event Type",
      tickangle: 45,
      automargin: true,
    },
    yaxis: {
      title: "Comparison",
      tickmode: "array",
      tickvals: ["BassLine - ShadGPT"],
      ticktext: ["BassLine - ShadGPT"],
    },
    margin: { t: 100, b: 150, l: 100, r: 100 },
    plot_bgcolor: "#E5ECF6",
    grid: {
      xgap: 0.1,
      ygap: 0.1,
    },
    annotations: [
      {
        text: "Red = BassLine over-extracts more, Blue = ShadGPT over-extracts more",
        xref: "paper",
        yref: "paper",
        x: 0.5,
        y: 1.05,
        showarrow: false,
      },
    ],
    shapes: eventTypes
      .map((_, i) => ({
        type: "line",
        x0: i - 0.5,
        x1: i - 0.5,
        y0: -0.5,
        y1: 0.5,
        xref: "x",
        yref: "y",
        line: { color: "white", width: 1 },
      }))
      .concat([
        {
          type: "line",
          x0: -0.5,
          x1: eventTypes.length - 0.5,
          y0: -0.5,
          y1: -0.5,
          xref: "x",
          yref: "y",
          line: { color: "white", width: 1 },
        },
        {
          type: "line",
          x0: -0.5,
          x1: eventTypes.length - 0.5,
          y0: 0.5,
          y1: 0.5,
          xref: "x",
          yref: "y",
          line: { color: "white", width: 1 },
        },
      ]),
  };

  Plotly.newPlot("heatmap2", data, layout);
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
