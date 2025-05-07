<script>
	import { onMount } from 'svelte';
	import cytoscape from 'cytoscape';
	import { fetchTree } from '$lib/api';

	let cy; //cytosscape, uses webgl by default
	let container; //dom element reference
	let treeData = []; //URL entries loaded from sessionStorage
	let rootLabel = 'ROOT'; //default root domain label

	//severity colors
	const severityColors = {
		high: '#e74c3c',     // Red
		medium: '#f39c12',   // Orange
		low: '#2ecc71',      // Green
		info: '#95a5a6',     // Gray
		unknown: '#7f8c8d'   // Dark Gray for undefined/invalid
	};

	//used to get color for a given severity
	function getSeverityColor(severity) {
		return severityColors[severity?.toLowerCase()] || severityColors.unknown;
	}

	//used if result entry does not have a severity entry but does have a status code entry, matches the logic for crawler
	function calculateSeverity(status) {
		if (status < 100 || status >= 600) {
			return 'unknown';
		} else if (status >= 100 && status < 200) {
			return 'info';
		} else if (status >= 200 && status < 300) {
			return 'low';
		} else if (status >= 300 && status < 400) {
			return 'medium';
		} else {
			return 'high';
		}
	}

	//used to build the node & edge elements from treeData
	function buildElements(data) {
		const elements = [];
		const nodeMap = new Map(); //used to try and avoid duplicate nodes

		data.forEach(node => {
			try {
				const fullUrl = new URL(node.url);
				const hostname = fullUrl.hostname;
				const segments = fullUrl.pathname.split('/').filter(Boolean);

				let path = '';
				let parentId = hostname;

				//determine severity based off the status code or severity
				const severity = node.severity?.toLowerCase() || calculateSeverity(node.status_code);

				//where we add the root domain node
				if (!nodeMap.has(hostname)) {
					nodeMap.set(hostname, true);
					elements.push({
						data: {
							id: hostname,
							label: hostname,
							severity
						}
					});
				}

				//used to add path nodes and edges
				for (let i = 0; i < segments.length; i++) {
					path += '/' + segments[i];
					const fullPath = `${hostname}${path}`;
					const label = '/' + segments[i];

					if (!nodeMap.has(fullPath)) {
						nodeMap.set(fullPath, true);
						elements.push({
							data: {
								id: fullPath,
								label,
								severity
							}
						});
						elements.push({
							data: {
								source: parentId,
								target: fullPath
							}
						});
					}

					parentId = fullPath;
				}
			} catch (err) {
				console.warn('Invalid URL skipped:', node.url);
			}
		});

		return elements;
	}

	//all the zoom controls that are needed per the SRS
	function resetZoom() {
		if (cy) cy.fit();
	}

	function zoomIn() {
		if (cy) cy.zoom(cy.zoom() * 1.2);
	}

	function zoomOut() {
		if (cy) cy.zoom(cy.zoom() * 0.8);
	}

	onMount(async () => {
		const project = sessionStorage.getItem('name');   // chosen in TreeList
		if (!project) return;

		try {
			// ① call the new /tree/{project} endpoint
			const { nodes } = await fetchTree(project);

			// ② convert each node so existing buildElements() still works
			treeData = nodes.map(n => ({
				url: (n.id.startsWith('http') ? n.id : 'https://' + n.id),          // backend returns label
				severity: n.severity,
				status_code: n.status_code ?? 0 // keep calc‑severity fallback
			}));

			// ③ create / refresh the graph
			if (cy) cy.destroy();              // hot‑reload friendly
			cy = cytoscape({
				container,
				elements: buildElements(treeData),
				layout: {
					name: 'breadthfirst',
					directed: true,
					padding: 10,
					spacingFactor: 1.75
				},
				style: [
					{                       /* ← OPEN node‑style object */
						selector: 'node',
						style: {
						shape: 'roundrectangle',
						'background-color': ele => getSeverityColor(ele.data('severity')),
						label: 'data(label)',
						'text-valign': 'center',
						'text-halign': 'center',
						color: '#fff',
						'font-size': 10,
						'text-wrap': 'wrap',
						'text-max-width': 80,
						width: 100,
						height: 50,
						'border-width': 2,
						'border-color': '#444'
						}
					},                      /* ← CLOSE node‑style object, comma to add edge block */
					{
						selector: 'edge',
						style: {
						width: 2,
						'line-color': '#ccc',
						'target-arrow-color': '#ccc',
						'target-arrow-shape': 'triangle'
						}
					}
					],                        /* ← CLOSE style array */
					wheelSensitivity: 0.2
					});
				} catch (err) {
  console.error('Failed to fetch tree:', err);
}
});                      /* end onMount */
</script>   

<!-- Graph container -->
<div class="tree-container" bind:this={container}></div>

<!-- Zoom control buttons -->
<div class="controls">
	<button on:click={zoomIn}>+</button>
	<button on:click={zoomOut}>-</button>
	<button on:click={resetZoom}>Reset</button>
</div>

<style>
	/* Graph container fills space except for sidebar */
	.tree-container {
		position: absolute;
		top: 0;
		bottom: 0;
		left: 10%; /* account for left sidebar */
		right: 0;
		z-index: 0;
	}

	/*bottom right controls(zoom controls) */
	.controls {
		position: absolute;
		bottom: 1rem;
		right: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		z-index: 1;
	}

	.controls button {
		background-color: #444;
		color: white;
		border: none;
		padding: 0.5rem 0.75rem;
		font-size: 1.2rem;
		border-radius: 4px;
		cursor: pointer;
	}

	.controls button:hover {
		background-color: #666;
	}
</style>
