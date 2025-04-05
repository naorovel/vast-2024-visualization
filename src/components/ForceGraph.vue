<template>
  <client-only>
    <div class="graph-wrapper">

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
              <pre>{{ link }}</pre>
            </div>
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
    }
  },
  mounted() {
    if (process.client) {
      import('d3').then(module => {
        this.d3 = module
        this.processLinks()
        this.initGraph()
        this.initZoom()
      })
    }
  },
  methods: {
    // Zoom methods
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
      this.processedLinks = this.links.map(link => {
        const source = nodeMap.get(link.source)
        const target = nodeMap.get(link.target)
        return source && target ? { source, target } : null
      }).filter(Boolean)
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
        .force('charge', this.d3.forceManyBody().strength(-1000))
        .force('center', this.d3.forceCenter(width / 2, height / 2))
        .force('link', this.d3.forceLink(this.processedLinks).id(d => d.id).distance(200))
        .force('collision', this.d3.forceCollide().radius(5))

      const link = this.zoomGroup
        .append('g')
        .selectAll('line')
        .data(this.processedLinks)
        .join('line')
        .attr('stroke', '#2a9d8f')
        .attr('stroke-width', 5) // Increased hit area
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

      const svg_mouse = this.d3.select(this.$refs.graphContainer).select('svg')
      svg_mouse.on('mousemove', this.updateMousePosition)
      
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
</style>