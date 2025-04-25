<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  let isLoading = false;
  let rootUrl = '';
  let avgSeverity = 'Info';
  let searchQuery = '';

  const severityColors = {
    'Info': '#3498db',
    'Low': '#f1c40f',
    'Medium': '#e67e22',
    'High': '#e74c3c'
  };

  onMount(async () => {
    try {
      const res = await fetch('/api/tree-data');
      if (!res.ok) throw new Error('Failed to load data');

      const data = await res.json();
      if (data.length > 0) {
        rootUrl = new URL(data[0].url).origin;
        avgSeverity = data[0].severity || 'Info';
      }
    } catch (err) {
      console.error(err);
      rootUrl = 'Unavailable';
    }
  });

  async function viewTree() {
      isLoading = true;
      await new Promise(r => setTimeout(r, 300)); 
      goto('/main/tools/TreeView');
  }

  // Simple search logic
  $: isVisible = rootUrl.toLowerCase().includes(searchQuery.toLowerCase());
</script>

<style>
  .container { 
    padding: 20px; 
    color: #ffffff;
  }

  h1 {
    margin-bottom: 20px;
    color: #ffffff;
  }

  .search-bar {
    background-color: #dcdcdc;
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    width: 300px;
    margin-bottom: 25px;
  }

  .search-bar input {
    border: none;
    background: transparent;
    margin-left: 8px;
    width: 100%;
    outline: none;
    color: #333;
  }

  .list-item {
    background-color: #e0e0e0;
    padding: 15px 20px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 70%;
    margin-bottom: 20px;
    color: #333333;
  }

  .info-section {
    display: flex;
    align-items: center;
    gap: 20px;
    justify-content: center;
    flex: 1;
  }

  .bullet {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid #666;
  }

  .root-url {
    font-size: 14px;
    color: #000000;   /* Black text */
  }

  .severity-label {
    font-size: 14px;
    font-weight: bold;
  }

  .view-btn {
    background-color: #5dade2;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.3s ease;
    font-size: 14px;
  }

  .view-btn:hover {
    background-color: #3498db;
  }

  .view-btn:disabled {
    background-color: #7fbce2;
    cursor: not-allowed;
  }
</style>

<div class="container">
  <h1>Tree Graph</h1>

  <!-- Search Bar -->
  <div class="search-bar">
    🔍
    <input type="text" placeholder="Search..." bind:value={searchQuery} />
  </div>

  <!-- Show only if search matches -->
  {#if isVisible}
    <div class="list-item">
      <div class="info-section">
        <div class="bullet" style="background-color: {severityColors[avgSeverity]}"></div>
        <span class="root-url">Root URL: {rootUrl}</span>
        <span class="severity-label">{avgSeverity}</span>
      </div>
      <button class="view-btn" on:click={viewTree} disabled={isLoading}>
        {#if isLoading}
          Loading...
        {:else}
          View
        {/if}
      </button>
    </div>
  {/if}
</div>
