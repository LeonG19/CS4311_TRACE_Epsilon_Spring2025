<script lang="ts">
	import { writable } from 'svelte/store';

	let url = 'https://example.com';
	let headers = 'Content-Type: application/json';
	let hideStatusCode = false;
	let proxy = 'http://proxyserver:8080';
	let requestBody = '{"key": "value"}';
	let additionalParams = '?debug=true';
	let method = 'PUT';

	let response = writable(null);
	let currentStage = writable('Configuration');
	let loading = writable(false);
	let error = writable(null);

	async function startTest() {
		currentStage.set('Running');
		loading.set(true);
		error.set(null);
		response.set(null);

		try {
			const res = await fetch('http://${import.meta.env.VITE_API_URL}/proxy-request', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ url: url + additionalParams, method })
			});
			const data = await res.json();
			response.set(data);
			currentStage.set('Results');
		} catch (err) {
			error.set(err.message);
			currentStage.set('Results');
		} finally {
			loading.set(false);
		}
	}
</script>

<style>
	body {
		background-color: #1e1e1e;
		color: #e0e0e0;
		font-family: Arial, sans-serif;
	}

	.container {
		max-width: 1200px;
		background-color: #2d2d2d;
		padding: 2rem;
		border-radius: 12px;
		margin: auto;
		margin-top: 2rem;
		border: 1px solid #444;
		display: flex;
		gap: 2rem;
	}

	.progress-bar {
		display: flex;
		justify-content: space-between;
		margin-bottom: 2rem;
	}

	.stage {
		flex: 1;
		text-align: center;
		padding: 0.5rem;
		border-bottom: 4px solid gray;
		color: white;
	}

	.stage.active {
		border-bottom: 4px solid #00aced;
		font-weight: bold;
		color: #00aced;
	}

	.form-grid {
		display: grid;
		grid-template-columns: 180px 1fr;
		gap: 1rem;
		align-items: center;
	}

	label {
		font-weight: bold;
		font-size: 0.9rem;
		color: #dcdcdc;
	}

	input[type='text'],
	input[type='url'],
	textarea,
	select {
		width: 100%;
		padding: 0.6rem;
		background-color: #1e1e1e;
		border: 1px solid #666;
		border-radius: 5px;
		color: #fff;
		font-size: 0.95rem;
	}

	input[type='checkbox'],
	input[type='radio'] {
		transform: scale(1.2);
		margin-right: 0.5rem;
	}

	.textarea-wide {
		grid-column: 1 / span 2;
	}

	button {
		background-color: #92d3c6;
		color: #000;
		font-weight: bold;
		padding: 0.75rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		width: 100%;
		margin-top: 2rem;
		transition: background 0.2s;
	}

	button:hover {
		background-color: #283331;
	}

	pre {
		background-color: #1e1e1e;
		padding: 1rem;
		border-radius: 6px;
		overflow: auto;
		border: 1px solid #444;
		color: #eee;
	}

	h1 {
		text-align: center;
		margin-bottom: 2rem;
		color: #fff;
	}

	.status-box {
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-weight: bold;
		margin-bottom: 1rem;
		display: inline-block;
	}

	.status-box.success {
		background-color: #2a4;
		color: white;
	}

	.status-box.error {
		background-color: #a22;
		color: white;
	}

	.left-column {
		flex: 1;
	}

	.right-column {
		flex: 1;
		background-color: #1a1a1a;
		border: 1px solid #444;
		border-radius: 10px;
		padding: 1rem;
	}
	.right-column pre {
		max-width: 100%;
		white-space: pre-wrap;
		word-wrap: break-word;
		overflow-x: auto;
	}

</style>

<div class="container">
	<div class="left-column">
		<h1>HTTP Tester</h1>

		<div class="progress-bar">
			<div class="stage" class:active={$currentStage === 'Configuration'}>Configuration</div>
			<div class="stage" class:active={$currentStage === 'Running'}>Running</div>
			<div class="stage" class:active={$currentStage === 'Results'}>Results</div>
		</div>

		<div class="form-grid">
			<label>Target URL:</label>
			<input bind:value={url} type="url" placeholder="https://example.com" />

			<label>Header:</label>
			<input bind:value={headers} placeholder="Content-Type: application/json" />

			<label>Hide Status Code:</label>
			<input type="checkbox" bind:checked={hideStatusCode} />

			<label>Proxy:</label>
			<input bind:value={proxy} placeholder="http://proxyserver:8080" />

			<label>Additional Parameters:</label>
			<input bind:value={additionalParams} placeholder="?debug=true" />

			<label>HTTP Method:</label>
			<div>
				<label><input type="radio" bind:group={method} value="GET" /> GET</label>
				<label><input type="radio" bind:group={method} value="PUT" /> PUT</label>
				<label><input type="radio" bind:group={method} value="POST" /> POST</label>
			</div>

			<label>Request Body:</label>
			<textarea bind:value={requestBody} placeholder='&#123;"key":"value"&#125;' class="block w-full mb-2"></textarea>
		</div>

		<button on:click={startTest}>Start</button>

		{#if $loading}
			<p class="mt-4">Running HTTP Test...</p>
		{/if}

		{#if $error}
			<p class="mt-4" style="color: red;">Error: {$error}</p>
		{/if}
	</div>

	<div class="right-column">
		{#if $response}
			<h2 class="mt-6">Result:</h2>

			<div
				class="status-box"
				class:success={$response.status_code >= 200 && $response.status_code < 300}
				class:error={$response.status_code >= 400}
			>
				Status Code: {$response.status_code}
			</div>

			<pre>{JSON.stringify($response.body, null, 2)}</pre>
		{/if}
	</div>
</div>
