<template>
  <client-only>
    <div class="graph-wrapper">

      <div class="filter-panel">
        <h4>Filters</h4>
        
        <!-- Existing bias filter -->
        <div class="filter-group">
          <label>Bias Types:</label>
          <select v-model="selectedBiases" multiple class="filter-select">
             <option 
                v-for="bias in allBiasTypes" 
                :key="bias" 
                :value="bias"
                :style="{ color: biasColorScale(bias) }"
              >
                █ {{ formatBiasName(bias) }}
              </option>
          </select>
        </div>

        <!-- New filters -->
        <div class="filter-group">
          <label>Algorithms:</label>
          <select v-model="selectedAlgorithms" multiple class="filter-select">
            <option v-for="alg in allAlgorithms" :key="alg" :value="alg">
              {{ alg }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Sources:</label>
          <select v-model="selectedSources" multiple class="filter-select">
            <option v-for="src in allSources" :key="src" :value="src">
              {{ src }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Last Edited By:</label>
          <select v-model="selectedEditors" multiple class="filter-select">
            <option v-for="editor in allEditors" :key="editor" :value="editor">
              {{ editor }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Connection Types:</label>
          <select v-model="selectedTypes" multiple class="filter-select">
            <option v-for="type in allTypes" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>
      </div>

      <div v-if="selectedNode || selectedConnection" class="side-menu">
        <div class="menu-header">
          <h3>
            {{ selectedNode ? 'Node Details' : 'Connection Details' }}
          </h3>
          <button @click="clearSelection">×</button>
        </div>
        <div class="menu-content">
          <!-- Node Details -->
          <div v-if="selectedNode">
            <p>ID: {{ selectedNode.id }}</p>
            <p>Connections: {{ selectedNode.connections?.length || 0 }}</p>
            <pre>{{ selectedNode }}</pre>
          </div>
          
          <!-- Connection Details -->
          <div v-if="selectedConnection">
            <p>Between:</p>
            <ul>
              <li>{{ selectedConnection.nodes[0].id }}</li>
              <li>{{ selectedConnection.nodes[1].id }}</li>
            </ul>
            
            <h4>All Links ({{ selectedConnection.links.length }}):</h4>
            <div 
              v-for="(link, index) in selectedConnection.links" 
              :key="index"
              class="link-item"
            >
              <div class="link-properties">
                <div v-if="link.type">
                  Type: <strong>{{ link.type }}</strong>
                </div>
                <div v-if="link.date_added">
                  Date Added: <strong>{{ link.date_added }}</strong>
                </div>
                <div v-if="link.raw_source">
                  Raw Source: <strong>{{ link.raw_source }}</strong>
                </div>
                <div v-if="link.algorithm">
                  Algorithm: <strong>{{ link.algorithm }}</strong>
                </div>
                <div v-if="link.last_edited_by">
                  Last Edited By: <strong>{{ link.last_edited_by }}</strong>
                </div>
                <div v-if="link.last_edited_date">
                  Last Edited Date: <strong>{{ link.last_edited_date }}</strong>
                </div>
                <div v-if="link.bias_types">
                  <div v-for="(biasValues, biasType) in link.bias_types" 
                      :key="biasType"
                      class="bias-item">
                    <strong>{{ formatBiasName(biasType) }}:</strong>
                    <div v-if="biasValues.length > 0">
                      <div v-for="(value, index) in biasValues" 
                          :key="index"
                          class="bias-value">
                        {{ value }}
                      </div>
                    </div>
                    <div v-else class="bias-value">
                      No specific values recorded
                    </div>
                  </div>
                </div>
              </div>
              <!-- Optional: Keep raw data view -->
              <pre v-if="showRawLinkData">{{ link }}</pre>
            </div>
            <!-- <div 
              v-for="(link, index) in selectedConnection.links" 
              :key="index"
              class="link-item"
            >
              <pre>{{ link }}</pre>
            </div> -->
          </div>
        </div>
      </div>



      <div ref="graphContainer" class="graph-container" @click="handleBackgroundClick">
        <div 
          v-if="hoveredElement" 
          class="tooltip"
          :style="{
            left: mousePosition.x + 10 + 'px',
            top: mousePosition.y + 10 + 'px'
          }"
        >
          <div v-if="hoveredElement.type === 'node'">
            Node: {{ hoveredElement.data.id }}
          </div>
          <div v-else>
            Link: {{ hoveredElement.data.source.id }} → {{ hoveredElement.data.target.id }}
          </div>
        </div>
      </div>
    </div>
    
  </client-only>
</template>


<script>

import * as d3 from 'd3';
export default {
  props: {
    nodes: { type: Array, required: true },
    links: { type: Array, required: true }
  },
  data() {
    return {
      d3: null,
      simulation: null,
      processedLinks: [],
      zoom: null,
      zoomGroup: null,
      hoveredElement: null,
      mousePosition: { x: 0, y: 0 },
      selectedNode: null,
      selectedConnection: null,
      selectedBiases: [],
      selectedAlgorithms: [],
      selectedSources: [],
      selectedEditors: [],
      selectedTypes: [],
      biasColorScale: d3.scaleOrdinal()
        .domain([]) // Will be set dynamically
        .range(d3.schemeCategory10),
      biasDescriptions: {
        confirmation_bias: "Tendency to search for information confirming existing beliefs",
        authority_bias: "Over-reliance on authority figures' opinions",
      },
      showRawLinkData: false,

    }
  },
  computed: {
    filteredLinks() {
      return this.links.filter(link => {
        // Bias filter
        const hasBias = this.selectedBiases.length === 0 || 
                      (link.bias_types && 
                        Object.keys(link.bias_types).some(b => 
                          this.selectedBiases.includes(b)));

        // Algorithm filter
        const hasAlgorithm = this.selectedAlgorithms.length === 0 ||
                            (!this.selectedAlgorithms.length && !link.algorithm) || 
                            (link.algorithm && 
                            this.selectedAlgorithms.some(a => 
                              link.algorithm.includes(a)));

        // Source filter
        const hasSource = this.selectedSources.length === 0 ||
                        (!this.selectedSources.length && !link.raw_source) ||
                        (link.raw_source && 
                          this.selectedSources.includes(link.raw_source));

        // Editor filter
        const hasEditor = this.selectedEditors.length === 0 ||
                        (!this.selectedEditors.length && !link.last_edited_by) ||
                        (link.last_edited_by && 
                          this.selectedEditors.includes(link.last_edited_by));

        // Type filter
        const hasType = this.selectedTypes.length === 0 ||
                      (!this.selectedTypes.length && !link.type) ||
                      (link.type && 
                        this.selectedTypes.includes(link.type));

        return hasBias && hasAlgorithm && hasSource && hasEditor && hasType;
      });
    },
    allBiasTypes() {
      const biasSet = new Set();
      this.links?.forEach(link => {
        if (link.bias_types) {
          Object.keys(link.bias_types).forEach(bias => {
            biasSet.add(bias);
          });
        }
      });
      return Array.from(biasSet).sort();
    },
      allAlgorithms() {
      return [...new Set(this.links.flatMap(l => l.algorithm || []))];
      },
      allSources() {
        return [...new Set(this.links.flatMap(l => l.raw_source || []))];
      },
      allEditors() {
        return [...new Set(this.links.flatMap(l => l.last_edited_by || []))];
      },
      allTypes() {
        return [...new Set(this.links.flatMap(l => l.type || []))];
      },
  },
  watch: {
    selectedAlgorithms: 'refreshGraph',
    selectedSources: 'refreshGraph',
    selectedEditors: 'refreshGraph',
    selectedTypes: 'refreshGraph',
    filteredLinks: {
      handler(newLinks) {
        if (this.d3) {
          this.processLinks();
          this.resetSimulation();
          this.updateGraphData(newLinks);
        }
      },
      immediate: true,
      deep: true
    },
    allBiasTypes: {
      immediate: true,
      handler(newVal) {
        // Initialize with all biases selected
        if (newVal.length && this.selectedBiases.length === 0) {
          this.selectedBiases = [...newVal];
        }
        this.biasColorScale.domain(newVal);
      }
    },
    selectedBiases: {
      handler() {
        // Force color update on all links
        this.zoomGroup.selectAll('line')
          .transition()
          .duration(300)
          .attr('stroke', d => this.getLinkColor(d));
      },
      deep: true
    }
  },
  mounted() {
    if (process.client) {
      import('d3').then(module => {
        this.d3 = module
        this.processLinks()
        this.initGraph()
        this.initZoom()
        // Add debug logs
        console.log('All Links:', this.links)
        console.log('All Bias Types:', this.allBiasTypes)
        console.log('First Link Bias:', this.links[0]?.bias_types)
      })
    }
  },
  methods: {
    // Zoom methods
    refreshGraph() {
      this.processLinks();
      this.updateGraphData(this.filteredLinks);
    },

    resetSimulation() {
        if (!this.d3 || !this.simulation) return;

        // Stop existing simulation
        this.simulation.stop();
        
        // Get current dimensions
        const { width, height } = this.getDimensions();

        // Reinitialize forces
        this.simulation
          .force('charge', this.d3.forceManyBody().strength(-10000))
          .force('center', this.d3.forceCenter(width / 2, height / 2))
          .force('link', this.d3.forceLink(this.processedLinks).id(d => d.id).distance(100))
          .force('collision', this.d3.forceCollide().radius(5));

        // Restart with fresh alpha
        this.simulation.alpha(1).restart();
    },
    initZoom() {
      const svg = this.d3.select(this.$refs.graphContainer).select('svg')

      // Initialize zoomGroup if it doesn't exist
      if (!this.zoomGroup) {
        this.zoomGroup = svg.append('g')
      }

      this.zoom = this.d3.zoom()
        .scaleExtent([0.1, 20])
        .on('zoom', (event) => {
          if (this.zoomGroup) {
            this.zoomGroup.attr('transform', event.transform)
          }
        })

      svg.call(this.zoom)
    },
    clearSelection() {
      this.selectedNode = null
      this.selectedConnection = null
    },
    resetZoom() {
      const svg = this.d3.select(this.$refs.graphContainer).select('svg')
      svg.transition()
        .duration(250)
        .call(this.zoom.transform, this.d3.zoomIdentity)
    },
    processLinks() {
      const nodeMap = new Map(this.nodes.map(node => [node.id, node]))
      this.processedLinks = this.filteredLinks
        .map(link => {
          // Handle both ID references and object references
          const source = nodeMap.get(link.source?.id || link.source);
          const target = nodeMap.get(link.target?.id || link.target);
          
          if (!source || !target) {
            console.warn('Invalid link:', link);
            return null;
          }
          
          return {
            ...link,
            source,
            target
          };
        })
        .filter(Boolean);
    },
    getDimensions() {
      return {
        width: this.$refs.graphContainer.clientWidth,
        height: 1080
      };
    },

    initGraph() {
       const container = this.$refs.graphContainer
      if (!container) return

      container.innerHTML = ''
      const { width, height } = this.getDimensions()
      
      // Create SVG first
      const svg = this.d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('background', '#f7ede2')

      // Initialize zoom group before creating graph elements
      this.zoomGroup = svg.append('g')

      
      // Create simulation
      this.simulation = this.d3.forceSimulation()
        .force('charge', this.d3.forceManyBody().strength(-10000))
        .force('center', this.d3.forceCenter(width / 2, height / 2))
        .force('link', this.d3.forceLink(this.processedLinks).id(d => d.id).distance(1000))
        .force('collision', this.d3.forceCollide().radius(5))

      const nodeGroups = this.zoomGroup
        .append('g')
        .selectAll('g.node-group')
        .data(this.nodes)
        .join('g')
        .attr('class', 'node-group')
        .call(this.dragHandler());

      // Add invisible hit area
      nodeGroups.append('circle')
        .attr('r', 15)
        .attr('fill', 'transparent')
        .attr('pointer-events', 'visible');

      // Add visible node circle
      nodeGroups.append('circle')
        .attr('r', 5)
        .attr('fill', '#264653');

      // Add text labels
      nodeGroups.append('text')
        .text(d => d.id)
        .attr('dx', 8)
        .attr('dy', 4)
        .style('font-size', '10px')
        .style('fill', '#264653')
        .style('pointer-events', 'none');      

      const link = this.zoomGroup
        .append('g')
        .selectAll('line')
        .data(this.processedLinks)
        .join('line')
        .attr('stroke', d => this.getLinkColor(d))
        .attr('stroke-width', 5)
        .attr('stroke-opacity', 0.3) // Keep visible but subtle
        .attr('pointer-events', 'visible');

      const node = this.zoomGroup
        .append('g')
        .selectAll('circle')
        .data(this.nodes)
        .join('circle')
        .attr('r', 5)
        .attr('fill', '#264653')
        .attr('pointer-events', 'visible')
        .call(this.dragHandler())
      
        // Simulation handler
      this.simulation.nodes(this.nodes)
        .on('tick', () => {
          link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y)

          node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y)

          nodeGroups
            .attr('transform', d => `translate(${d.x},${d.y})`);
        })

      node
        .on('mouseover', (event, d) => {
          this.hoveredElement = { type: 'node', data: d }
          this.updateMousePosition(event)
        })
        .on('mouseout', () => {
          this.hoveredElement = null
        })
        .on('mousemove', this.updateMousePosition)

      // Add hover handlers to links
      link
        .on('mouseover', (event, d) => {
          this.hoveredElement = { type: 'link', data: d }
          this.updateMousePosition(event)
        })
        .on('mouseout', () => {
          this.hoveredElement = null
        })
        .on('mousemove', this.updateMousePosition)

      // Update existing node click handler
      node
      .on('click', (event, d) => {
        this.selectedNode = d
        this.selectedConnection = null  // Clear link selection
        event.stopPropagation()
      })

      link
      .on('click', (event, clickedLink) => {
        event.stopPropagation()
        
        // Find all links between these two nodes (both directions)
        const nodePair = [
          clickedLink.source.id, 
          clickedLink.target.id
        ].sort().join('|')
        
        const allLinks = this.processedLinks.filter(l => {
          const currentPair = [l.source.id, l.target.id].sort().join('|')
          return currentPair === nodePair
        })

        this.selectedConnection = {
          nodes: [clickedLink.source, clickedLink.target],
          links: allLinks
        }
        
        this.selectedNode = null
      })

      nodeGroups
        .on('mouseover', (event, d) => {
          this.hoveredElement = { type: 'node', data: d };
          this.updateMousePosition(event);
        })
        .on('click', (event, d) => {
          this.selectedNode = d;
          this.selectedConnection = null;
          event.stopPropagation();
        });

      const svg_mouse = this.d3.select(this.$refs.graphContainer).select('svg')
      svg_mouse.on('mousemove', this.updateMousePosition)
     
      this.simulation.on('end', () => {
        this.nodes.forEach(n => {
          n.fx = null;
          n.fy = null;
        });
      });
    },

    dragHandler() {
      return this.d3.drag()
        .on('start', event => {
          if (!event.active) this.simulation.alphaTarget(0.3).restart()
          event.subject.fx = event.x
          event.subject.fy = event.y
        })
        .on('drag', event => {
          const [x, y] = this.d3.pointer(event, this.zoomGroup.node())
          event.subject.fx = x
          event.subject.fy = y
          this.simulation.alpha(0.5).restart()
        })
        .on('end', event => {
          if (!event.active) this.simulation.alphaTarget(0)
          event.subject.fx = null
          event.subject.fy = null
        })
    },

    handleBackgroundClick() {
      this.clearSelection()
    },

    updateMousePosition(event) {
      const container = this.$refs.graphContainer.getBoundingClientRect()
      const transform = this.d3.zoomTransform(this.zoomGroup.node())
      
      this.mousePosition = {
        x: (event.clientX - container.left - transform.x) / transform.k,
        y: (event.clientY - container.top - transform.y) / transform.k
      }
    },

    formatBiasName(biasKey) {
      return biasKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    },

    updateGraphData(filteredLinks) {
      if (!this.d3 || !this.simulation) return;

      // Process new links with proper node references
      const nodeMap = new Map(this.nodes.map(n => [n.id, n]));
      this.processedLinks = filteredLinks.map(link => ({
        ...link,
        source: nodeMap.get(link.source),
        target: nodeMap.get(link.target)
      }));

      // Update simulation forces
      this.simulation
        // .force('link', this.d3.forceLink(this.processedLinks).id(d => d.id).distance(100))
        // .alpha(1)
        .restart();
      
      const nodePositions = new Map(this.nodes.map(n => [n.id, { x: n.x, y: n.y }]));

      // Get current dimensions
      const { width, height } = this.getDimensions();

      // DATA JOIN with proper key function
      const links = this.zoomGroup.selectAll('line')
        .data(this.processedLinks, d => 
          `${d.source?.id}-${d.target?.id}-${d.type}`
        );

      // EXIT old links
      links.exit()
        .transition()
        .duration(500)
        .style('opacity', 0)
        .remove();

      // ENTER new links
      const enterLinks = links.enter()
        .append('line')
        .attr('stroke', d => this.getLinkColor(d))
        .attr('stroke-width', 5)
        .style('opacity', 0)
        .on('mouseover', (event, d) => {
          this.hoveredElement = { type: 'link', data: d };
          this.updateMousePosition(event);
        });

      // UPDATE existing + new links
      links.merge(enterLinks)
        .transition()
        .duration(500)
        .style('opacity', 0.7)
        .attr('stroke', d => this.getLinkColor(d))
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      // Restart simulation with new data
      this.simulation
        .nodes(this.nodes)
        .force('link', this.d3.forceLink(this.processedLinks))
        .alphaTarget(0.3)
        .restart();

          // Restore positions after data update
      this.nodes.forEach(n => {
        const pos = nodePositions.get(n.id);
        if (pos) {
          n.x = pos.x;
          n.y = pos.y;
          n.fx = pos.x;
          n.fy = pos.y;
        }
      });

      this.simulation.alpha(0.5).restart();

      console.log('Active links:', this.processedLinks.length);
      console.log('Sample link:', this.processedLinks[0]);
      console.log('Processed links:', this.processedLinks);
      console.log('First processed link:', this.processedLinks[0] && {
        source: this.processedLinks[0].source?.id,
        target: this.processedLinks[0].target?.id,
        type: this.processedLinks[0].type
  });
    },

    handleLinkClick(event, clickedLink) {
      event.stopPropagation();
      const nodePair = [
        clickedLink.source.id, 
        clickedLink.target.id
      ].sort().join('|');
      
      const allLinks = this.filteredLinks.filter(l => {
        const currentPair = [l.source.id, l.target.id].sort().join('|');
        return currentPair === nodePair;
      });

      this.selectedConnection = {
        nodes: [clickedLink.source, clickedLink.target],
        links: allLinks
      };
      this.selectedNode = null;
    },

    getLinkColor(link) {
      // Add null checks
      if (!link?.bias_types || this.selectedBiases.length === 0) {
        return '#2a9d8f';
      }

      const activeBiases = Object.entries(link.bias_types)
        .filter(([bias]) => this.selectedBiases.includes(bias));

      if (activeBiases.length === 0) return '#2a9d8f';

      // Handle empty bias values
      const prominentBias = activeBiases.reduce((prev, current) => 
        (prev[1].length > current[1].length) ? prev : current
      )[0];

      return this.biasColorScale(prominentBias);
    }
    
  }
}
</script>



<style>
.reset-zoom {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 100;
  padding: 5px 10px;
  cursor: pointer;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.tooltip {
  position: absolute;
  background: white;
  border: 1px solid #ccc;
  padding: 8px 12px;
  border-radius: 4px;
  pointer-events: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  font-size: 14px;
  z-index: 100;
  max-width: 200px;
  color: #264653;
}

.graph-container {
  position: relative;
}

.graph-wrapper {
  display: flex;
  position: relative;
}

.side-menu {
  width: 300px;
  background: white;
  border-right: 1px solid #ccc;
  height: 100vh;
  overflow-y: auto;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
  z-index: 100;
  position: fixed;
  left: 0;
  top: 0;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
  color:#264653
}

.menu-header button {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
}

.menu-content {
  padding: 15px;
  color: #264653;

}

.graph-container {
  flex-grow: 1;
  margin-left: 300px; /* Match side menu width */
  height: 100vh;
  position: relative;
}

.link-item {
  margin: 10px 0;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
}

.link-item pre {
  margin: 0;
  font-size: 0.9em;
}

.node-group text {
  user-select: none;
  -webkit-user-select: none;
}

.link-properties {
  margin-bottom: 8px;
}

.link-properties div {
  margin: 4px 0;
  font-size: 0.9em;
  color: #2a9d8f;
}

pre {
  font-size: 0.8em;
  opacity: 0.7;
}

.filter-panel {
  position: fixed;
  right: 20px;
  top: 20px;
  background: white;
  padding: 15px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
  max-height: 80vh;
  overflow-y: auto;
  max-width: 300px;
}

.filter-item {
  margin: 5px 0;
}

.filter-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color:#264653
}

.filter-item input {
  margin: 0;
}

.bias-item {
  margin: 8px 0;
  padding: 6px;
  background: #f7f7f7;
  border-radius: 4px;
}

.bias-value {
  font-size: 0.85em;
  color: #666;
  margin-left: 12px;
}

.bias-color-indicator {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-right: 8px;
  border: 1px solid #ddd;
}

.filter-item label {
  color: #264653; /* Dark blue */
  font-weight: 500;
}

.filter-item label {
  transition: color 0.2s ease;
}

.filter-item label:hover {
  color: #e76f51; /* Your coral color on hover */
}

.filter-panel h4 {
  color: #2a9d8f; /* Your teal color */
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.filter-item input[type="checkbox"] {
  accent-color: #2a9d8f; /* Match your color scheme */
}

.legend {
  position: fixed;
  right: 20px;
  bottom: 20px;
  background: white;
  padding: 15px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
  max-height: 50vh;
  overflow-y: auto;
}

.legend-item {
  display: flex;
  align-items: center;
  margin: 5px 0;
}

.legend-color {
  width: 15px;
  height: 15px;
  border-radius: 3px;
  margin-right: 10px;
  border: 1px solid #ddd;
}

.legend-label {
  font-size: 0.9em;
}

line {
  stroke-opacity: 0.7 !important;
  stroke-width: 3px !important;
}

.filter-panel {
  width: 300px;
  padding: 15px;
}

.filter-group {
  margin-bottom: 15px;
}

.filter-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #2a9d8f;
}

.filter-select {
  width: 100%;
  min-height: 100px;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
}

.filter-select option {
  padding: 3px;
  cursor: pointer;
}

.filter-select option:hover {
  background-color: #f0f0f0;
}

line.exit {
  opacity: 0 !important;
  pointer-events: none;
}
</style>
