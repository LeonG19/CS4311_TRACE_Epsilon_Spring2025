<script>

	import { onMount } from 'svelte';
	import { goto } from '$app/navigation'; //used for view button

	let projectName = ''; //loaded from session
	let groupedRoots = []; //group results by their root
	let filteredRoots = [];
	let searchQuery = ''; //search bar input

	//controls for filter panel
	let showAdvancedFilters = false;
	let sortBy = 'domain'; // default sort mode
	let enabledSeverities = { high: true, medium: true, low: true };
	let showUnknown = true; // whether to include entries with malformed or unknown root

	//staging values for overlay before filters are applied
	let pendingSort = sortBy;
	let pendingSeverities = { ...enabledSeverities };
	let pendingShowUnknown = showUnknown;

	//runs once component loads
	onMount(async () => {
		projectName = sessionStorage.getItem('name'); //retrieve the project name from previous page
		if (projectName) {
			try {
				//fetch scan results for the current project
				const response = await fetch(`http://localhost:8000/getResult/${projectName}`); //call the database method to get all the project results
				const data = await response.json();
				groupedRoots = groupByRoot(data); //group results by domain
			} catch (err) {
				console.error("Failed to fetch results:", err);
			}
		}
	});

	//groups entries by root domain, if invalid URL set to 'unknown'
	function groupByRoot(results) {
		const groups = {};
		for (const entry of results) {
			if (!entry.url) continue;
			try {
				const url = new URL(entry.url);
				const root = url.hostname;
				if (!groups[root]) groups[root] = [];
				groups[root].push(entry);
			} catch {    //if URL parsing fails, assign to 'unknown'
				if (!groups["unknown"]) groups["unknown"] = [];
				groups["unknown"].push(entry);
			}
		}
		//convert to array for easier iteration
		return Object.entries(groups).map(([root, entries]) => ({ root, entries }));
	}

	//go to the tree view and store selected group in sessionStorage
	function viewTree(group) {
		sessionStorage.setItem('treeData', JSON.stringify(group.entries));
		sessionStorage.setItem('treeRoot', group.root);
		goto('/main/tools/TreeView'); //TreeView path
	}

	//extract severity level from first entry of group, used in the tree list root entries
	function getSeverityLevel(group) {
		return group.entries[0]?.severity?.toLowerCase() || 'info';
	}

	//used to match severity to a color
	function getSeverityColor(group) {
		const level = getSeverityLevel(group);
		if (level === 'high') return 'red';
		if (level === 'medium') return 'orange';
		if (level === 'low') return 'green';
		return 'gray'; // fallback for unknown severities
	}

	//used in the search bar to parse input
	function parseQuery(input) {
		const parts = input.trim().toLowerCase().split(/\s+/);
		const query = { severity: '', freeText: '' };

		for (const part of parts) {
			if (part.startsWith('severity:')) {
				query.severity = part.split(':')[1] || '';
			} else if (['high', 'medium', 'low'].includes(part)) {
				query.severity = part;
			} else {
				query.freeText += part + ' ';
			}
		}

		query.freeText = query.freeText.trim();
		return query;
	}

	//used to check if a root node matches the current filters
	function matchesFilter(group, query) {
		const rootMatch = group.root.toLowerCase().includes(query.freeText);
		const severity = getSeverityLevel(group);
		const severityMatch = enabledSeverities[severity] && (!query.severity || query.severity === severity);
		if (!showUnknown && group.root === 'unknown') return false;
		return rootMatch && severityMatch;
	}

	//used to update the results based on the filters
	$: filteredRoots = (() => {
		const parsedQuery = parseQuery(searchQuery);
		const filtered = groupedRoots.filter(group => matchesFilter(group, parsedQuery));

		//severity weight for sorting
		const severityRank = { high: 3, medium: 2, low: 1 };
		const getRank = (g) => severityRank[getSeverityLevel(g)] || 0;

		//sorting logic
		if (sortBy === 'domain') {
			filtered.sort((a, b) => a.root.localeCompare(b.root));
		} else if (sortBy === 'domain_desc') {
			filtered.sort((a, b) => b.root.localeCompare(a.root));
		} else if (sortBy === 'severity') {
			filtered.sort((a, b) => getRank(b) - getRank(a));
		} else if (sortBy === 'severity_asc') {
			filtered.sort((a, b) => getRank(a) - getRank(b));
		}
		return filtered;
	})();

	//applies the advanced filter values to main filter
	function applyFilters() {
		sortBy = pendingSort;
		enabledSeverities = { ...pendingSeverities };
		showUnknown = pendingShowUnknown;
		showAdvancedFilters = false;

		//used to force update by tweaking input value slightly
		searchQuery = searchQuery.trim() + ' ';
		searchQuery = searchQuery.trim();
	}
</script>

<!-- PAGE TITLE -->
<h1 class="section-title">Tree Graph</h1>

<!-- Search input and filter button -->
<div class="search-container">
	<input
		type="text"
		placeholder="Search (e.g. discord severity:low)"
		bind:value={searchQuery}
		class="search-bar"
	/>
	<button class="filter-button" on:click={() => showAdvancedFilters = !showAdvancedFilters}>
		Filter
	</button>
</div>

<!-- ADVANCED FILTER OVERLAY -->
{#if showAdvancedFilters}
	<div class="filter-overlay">
		<div class="filter-panel">
			<h4>Advanced Filters</h4>

			<!-- Dropdown for sorting -->
			<div>
				<label>Sort by:</label>
				<select bind:value={pendingSort}>
					<option value="domain">Domain (A-Z)</option>
					<option value="domain_desc">Domain (Z-A)</option>
					<option value="severity">Severity (High → Low)</option>
					<option value="severity_asc">Severity (Low → High)</option>
				</select>
			</div>

			<!-- Severity checkboxes -->
			<div>
				<label>Severity:</label>
				<div class="checkbox-group-vertical">
					<label class="vertical-label">High<input type="checkbox" bind:checked={pendingSeverities.high} /></label>
					<label class="vertical-label">Medium<input type="checkbox" bind:checked={pendingSeverities.medium} /></label>
					<label class="vertical-label">Low<input type="checkbox" bind:checked={pendingSeverities.low} /></label>
				</div>
			</div>

			<!-- Unknown domain checkbox -->
			<div class="checkbox-group">
				<label class="vertical-label">
					Include Unknown Roots
					<input type="checkbox" bind:checked={pendingShowUnknown} />
				</label>
			</div>

			<!-- Apply filters -->
			<button class="apply-button" on:click={applyFilters}>Apply Filters</button>
		</div>
	</div>
{/if}

<!-- SCAN RESULT LIST -->
{#if filteredRoots.length}
	<div class="card-container">
		{#each filteredRoots as group}
			<div class="result-card">
				<div class="card-left">
					<!-- Domain name -->
					<div class="parent">{group.root}</div>
					<!-- Severity label with background color -->
					<div class="severity {getSeverityColor(group)}">
						Severity: {getSeverityLevel(group)}
					</div>
				</div>
				<!-- Button to navigate to tree view -->
				<button class="view-button" on:click={() => viewTree(group)}>View</button>
			</div>
		{/each}
	</div>
{:else}
	<!-- Message shown when no results match -->
	<p>No scan results found for project: <code>{projectName}</code>.</p>
{/if}

<!-- STATIC PROGRESS BAR PLACEHOLDER -->
<div class="progress-container">
	<div class="progress-label">Brute Force Tester Scan</div>
	<progress max="100" value="0"></progress>
</div>

<!-- STYLES -->
<style>
	:global(body) {
		background-color: #1e1e1e;
		color: white;
	}

	.section-title {
		font-size: 2rem;
		margin-bottom: 1rem;
	}

	.search-container {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.search-bar {
		flex-grow: 1;
		padding: 0.5rem;
		border-radius: 5px;
		border: 1px solid #ccc;
		background-color: #2c2c2c;
		color: white;
	}

	.filter-button,
	.view-button,
	.apply-button {
		background-color: #555;
		color: white;
		border: none;
		border-radius: 5px;
		padding: 0.5rem 1rem;
		cursor: pointer;
		transition: background-color 0.2s ease;
	}

	.filter-button:hover,
	.view-button:hover,
	.apply-button:hover {
		background-color: #777;
	}

	.filter-overlay {
		position: fixed;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		background-color: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 999;
	}

	.filter-panel {
		background-color: #2c2c2c;
		border: 1px solid #444;
		padding: 1.5rem;
		border-radius: 12px;
		color: white;
		width: 320px;
		box-shadow: 0 0 20px rgba(0, 0, 0, 0.6);
	}

	.filter-panel h4 {
		margin-top: 0;
		font-size: 1.3rem;
	}

	.checkbox-group,
	.checkbox-group-vertical {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 0.5rem;
	}

	.checkbox-group-vertical {
		flex-direction: row;
		justify-content: space-between;
	}

	.vertical-label {
		display: flex;
		flex-direction: column;
		align-items: center;
		font-size: 0.95rem;
		gap: 0.25rem;
	}

	select {
		padding: 0.3rem;
		border-radius: 5px;
		border: 1px solid #ccc;
		background-color: #1e1e1e;
		color: white;
	}

	.card-container {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.result-card {
		display: flex;
		justify-content: space-between;
		align-items: center;
		border: 1px solid #444;
		border-radius: 8px;
		padding: 1rem;
		background-color: #2a2a2a;
	}

	.card-left {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.parent {
		font-weight: bold;
		color: white;
	}

	.severity {
		font-size: 0.9rem;
		padding: 0.2rem 0.5rem;
		border-radius: 5px;
		color: white;
		width: fit-content;
	}

	.severity.red {
		background-color: #e74c3c;
	}

	.severity.orange {
		background-color: #f39c12;
	}

	.severity.green {
		background-color: #2ecc71;
	}

	.severity.gray {
		background-color: #7f8c8d;
	}

	.progress-container {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		padding: 0.5rem;
		background-color: #1a1a1a;
		border-top: 1px solid #333;
		text-align: center;
	}

	.progress-label {
		font-size: 0.75rem;
		margin-bottom: 0.2rem;
		color: white;
	}

	progress {
		width: 100%;
		height: 6px;
		border-radius: 4px;
		overflow: hidden;
	}

	progress::-webkit-progress-bar {
		background-color: #333;
		border-radius: 4px;
	}

	progress::-webkit-progress-value {
		background-color: #3498db;
	}
</style>
