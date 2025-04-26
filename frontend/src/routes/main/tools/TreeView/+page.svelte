<script>
  import { onMount, tick } from 'svelte';
  import cytoscape from 'cytoscape';

  let cy;
  let isLoading = true;
  let error = '';

  // Helper to format URL as [HOSTNAME]\n[PATH]
  function formatUrlLabel(url) {
      try {
          const parsedUrl = new URL(url);
          const hostname = parsedUrl.hostname;
          const pathname = parsedUrl.pathname || '/';
          return `${hostname}\n${pathname}`;
      } catch {
          return url;
      }
  }

  onMount(async () => {
    try {
      const res = await fetch('/api/tree-graph');
      if (!res.ok) throw new Error('Failed to fetch graph data');

      const data = await res.json();
      const elements = [];

      data.nodes.forEach(node => {
        elements.push({
          data: { 
            id: String(node.id), 
            label: formatUrlLabel(node.label), 
            severity: node.color 
          }
        });
      });

      data.edges.forEach(edge => {
        elements.push({
          data: { source: String(edge.from), target: String(edge.to) }
        });
      });

      isLoading = false;   // Trigger DOM update for {#if} block

      await tick();  // Ensure DOM is updated before accessing #cy

      const container = document.getElementById('cy');
      if (!container) {
          console.error('Cytoscape container not found!');
          return;
      }

      cy = cytoscape({
        container: container,
        elements,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': 'data(severity)',
              'label': 'data(label)',
              'color': '#000',
              'text-valign': 'center',
              'text-halign': 'center',
              'shape': 'roundrectangle',
              'padding': '10px',
              'font-size': '10px',
              'text-wrap': 'wrap',
              'text-max-width': 80
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 1,
              'line-color': '#ccc',
              'target-arrow-shape': 'none'
            }
          }
        ],
        layout: {
          name: 'breadthfirst',
          directed: true,
          padding: 10,
          spacingFactor: 1.5
        }
      });

      window.addEventListener('resize', () => cy.resize());

    } catch (err) {
      console.error(err);
      error = 'Unable to load Tree Graph. Please try again later.';
      isLoading = false;
    }
  });
</script>

<style>
  h1 {
    color: #ffffff;
    margin-bottom: 15px;
    font-size: 24px;
  }

  #cy {
    width: 100%;
    height: 80vh;
    background: #f9f9f9;
    border: 1px solid #444;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .legend {
    color: #dddddd;
    font-size: 14px;
    margin-top: 10px;
  }

  .legend p {
    margin: 4px 0;
  }

  .legend span {
    display: inline-block;
    width: 14px;
    height: 14px;
    margin-right: 8px;
    border: 1px solid #666;
    border-radius: 3px;
  }

  .error {
    color: #ff4d4d;
    margin-top: 20px;
    font-weight: bold;
  }
</style>

<h1>Tree Graph View</h1>

{#if isLoading}
  <p class="legend">Loading Tree Graph...</p>
{:else if error}
  <p class="error">{error}</p>
{:else}
  <div id="cy"></div>
  <div class="legend">
    <p><span style="background:#3498db"></span> Info</p>
    <p><span style="background:#f1c40f"></span> Low</p>
    <p><span style="background:#e67e22"></span> Medium</p>
    <p><span style="background:#e74c3c"></span> High</p>
  </div>
{/if}
