<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchTree } from '$lib/api';
  
	// inject defaultProject from +page.ts
	export let data: { defaultProject: string };
  
	// read user-chosen or fallback to default from load()
	let projectName = sessionStorage.getItem('name') || 'Hacking_Mexico';
  
	// groupedRoots holds domain groups for display
	let groupedRoots: { root: string; entries: any[] }[] = [];
	let filteredRoots: typeof groupedRoots = [];
	let searchQuery = '';
  
	// advanced filter controls
	let showAdvancedFilters = false;
	let sortBy = 'domain';
	let enabledSeverities = { high: true, medium: true, low: true };
	let showUnknown = true;
	let pendingSort = sortBy;
	let pendingSeverities = { ...enabledSeverities };
	let pendingShowUnknown = showUnknown;
  
	async function loadTree() {
	if (!projectName) return;
	try {
		const { nodes } = await fetchTree(projectName);
		const entries = nodes.map((n: any) => ({ url: n.label || n.url, severity: n.severity }));
		groupedRoots = groupByRoot(entries);
	} catch (err) {
		console.error('Failed to fetch tree:', err);
	}
	}
  
	onMount(loadTree);
  
	function groupByRoot(results: { url: string; severity: string }[]) {
	  const groups: Record<string, typeof results> = {};
	  for (const entry of results) {
		const raw = entry.url;
		if (!raw) continue;
		try {
		  const safe = raw.startsWith('http') ? raw : 'https://' + raw;
		  const root = new URL(safe).hostname;
		  (groups[root] ||= []).push(entry);
		} catch {
		  (groups['unknown'] ||= []).push(entry);
		}
	  }
	  return Object.entries(groups).map(([root, entries]) => ({ root, entries }));
	}
  
	function viewTree(group: { root: string; entries: any[] }) {
	  sessionStorage.setItem('treeData', JSON.stringify(group.entries));
	  sessionStorage.setItem('treeRoot', group.root);
	  // navigate to TreeView as before
	  location.href = `/main/tools/TreeView`;
	}
  
	const severityRank = { high: 3, medium: 2, low: 1 };
	const sevColorMap = { high: 'red', medium: 'orange', low: 'green', info: 'gray' };
	function sevLevel(g: { entries: any[] }) {
	  return g.entries[0]?.severity?.toLowerCase() || 'info';
	}
	function sevColorOf(g: { entries: any[] }) {
	  return sevColorMap[sevLevel(g)] ?? 'gray';
	}
  
	function parseQuery(txt: string) {
	  const parts = txt.trim().toLowerCase().split(/\s+/);
	  const q = { severity: '', freeText: '' };
	  for (const p of parts) {
		if (p.startsWith('severity:')) q.severity = p.split(':')[1] || '';
		else if (['high','medium','low'].includes(p)) q.severity = p;
		else q.freeText += p + ' ';
	  }
	  q.freeText = q.freeText.trim();
	  return q;
	}
  
	function matches(g: { root: string }, q: { severity: string; freeText: string }) {
	  const rootOk = g.root.toLowerCase().includes(q.freeText);
	  const sev = sevLevel(g as any);
	  const sevOk = enabledSeverities[sev] && (!q.severity || q.severity === sev);
	  if (!showUnknown && g.root === 'unknown') return false;
	  return rootOk && sevOk;
	}
  
	$: filteredRoots = (() => {
	  const q = parseQuery(searchQuery);
	  const arr = groupedRoots.filter(g => matches(g, q));
	  if (sortBy === 'domain') arr.sort((a,b)=>a.root.localeCompare(b.root));
	  else if (sortBy === 'domain_desc') arr.sort((a,b)=>b.root.localeCompare(a.root));
	  else if (sortBy === 'severity') arr.sort((a,b)=>severityRank[sevLevel(b)]-severityRank[sevLevel(a)]);
	  else if (sortBy === 'severity_asc') arr.sort((a,b)=>severityRank[sevLevel(a)]-severityRank[sevLevel(b)]);
	  return arr;
	})();
  
	function applyFilters() {
	  sortBy = pendingSort;
	  enabledSeverities = { ...pendingSeverities };
	  showUnknown = pendingShowUnknown;
	  showAdvancedFilters = false;
	  // trigger reactivity
	  searchQuery = searchQuery.trim() + ' ';
	  searchQuery = searchQuery.trim();
	}
  </script>
  
  <h1 class="section-title">Tree Graph</h1>
  <button class="refresh" on:click={loadTree}>⟳ Refresh</button>
  
  <div class="search-container">
	<input type="text" placeholder="Search (e.g. discord severity:low)" bind:value={searchQuery} class="search-bar" />
	<button class="filter-button" on:click={() => showAdvancedFilters = !showAdvancedFilters}>Filter</button>
  </div>
  
  {#if showAdvancedFilters}
	<div class="filter-overlay">
	  <div class="filter-panel">
		<h4>Advanced Filters</h4>
		<label>Sort by:
		  <select bind:value={pendingSort}>
			<option value="domain">Domain (A‑Z)</option>
			<option value="domain_desc">Domain (Z‑A)</option>
			<option value="severity">Severity (High→Low)</option>
			<option value="severity_asc">Severity (Low→High)</option>
		  </select>
		</label>
		<label>Severity:</label>
		<div class="checkbox-row">
		  <label>High <input type="checkbox" bind:checked={pendingSeverities.high} /></label>
		  <label>Medium <input type="checkbox" bind:checked={pendingSeverities.medium} /></label>
		  <label>Low <input type="checkbox" bind:checked={pendingSeverities.low} /></label>
		</div>
		<label>
		  Include Unknown Roots <input type="checkbox" bind:checked={pendingShowUnknown} />
		</label>
		<button class="apply-button" on:click={applyFilters}>Apply Filters</button>
	  </div>
	</div>
  {/if}
  
  {#if filteredRoots.length}
	<div class="card-container">
	  {#each filteredRoots as group}
		<div class="result-card">
		  <div class="card-left">
			<div class="parent">{group.root}</div>
			<div class="severity {sevColorOf(group)}">Severity: {sevLevel(group)}</div>
		  </div>
		  <button class="view-button" on:click={() => viewTree(group)}>View</button>
		</div>
	  {/each}
	</div>
  {:else}
	<p>No scan results found for project: <code>{projectName}</code>.</p>
  {/if}
  
  <div class="progress-container">
	<div class="progress-label">Brute Force Tester Scan</div>
	<progress max="100" value="0"></progress>
  </div>
  
  <style>
	:global(body) { background:#1e1e1e; color:#fff; }
	.refresh { position:absolute; top:1rem; right:1rem; padding:.4rem .8rem; background:#555; color:#fff; border:none; border-radius:4px; cursor:pointer; }
	.refresh:hover { background:#777; }
	.section-title { font-size:2rem; margin-bottom:1rem; }
	.search-container { display:flex; gap:.5rem; margin-bottom:1rem; }
	.search-bar { flex:1; padding:.5rem; border-radius:5px; border:1px solid #444; background:#2c2c2c; color:#fff; }
	.filter-button, .view-button, .apply-button { background:#555; color:#fff; border:none; padding:.5rem 1rem; border-radius:5px; cursor:pointer; transition:background .2s; }
	.filter-button:hover, .view-button:hover, .apply-button:hover { background:#777; }
	.filter-overlay { position:fixed; inset:0; background:rgba(0,0,0,.7); display:flex; align-items:center; justify-content:center; }
	.filter-panel { background:#2c2c2c; border:1px solid #444; padding:1.5rem; border-radius:12px; width:320px; box-shadow:0 0 20px rgba(0,0,0,.6); }
	.checkbox-row { display:flex; gap:.5rem; margin:.5rem 0; }
	.card-container { display:flex; flex-direction:column; gap:1rem; }
	.result-card { display:flex; justify-content:space-between; align-items:center; background:#2a2a2a; border:1px solid #444; border-radius:8px; padding:1rem; }
	.card-left { display:flex; flex-direction:column; gap:.25rem; }
	.parent { font-weight:bold; }
	.severity { font-size:.9rem; padding:.2rem .5rem; border-radius:5px; color:#fff; }
	.severity.red { background:#e74c3c; }
	.severity.orange { background:#f39c12; }
	.severity.green { background:#2ecc71; }
	.severity.gray { background:#7f8c8d; }
	.progress-container { position:fixed; bottom:0; left:0; right:0; background:#1a1a1a; border-top:1px solid #333; text-align:center; padding:.5rem; }
	.progress-label { font-size:.75rem; margin-bottom:.2rem; }
	progress { width:100%; height:6px; border-radius:4px; overflow:hidden; }
	progress::-webkit-progress-bar { background:#333; }
	progress::-webkit-progress-value { background:#3498db; }
  </style>
  