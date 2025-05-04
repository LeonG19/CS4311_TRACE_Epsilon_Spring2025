<script lang="ts">
    // ──────────────────────────── state ────────────────────────────
    let target_url = '';
    let port       = 80;
    let timeout    = 5;
    let enum_level = 0;
    let headers_raw = '';
  
    let result: any = null;
    let error:  string | null = null;
    let loading = false;
  
    // ─────────────────────── helpers & validation ──────────────────
    function validateInputs() {
      if (!target_url.trim()) {
        error = 'Target URL is required.';
        return false;
      }
      if (![0, 1].includes(+enum_level)) {
        error = 'Enum level must be 0 or 1.';
        return false;
      }
      return true;
    }
  
    async function runInjection() {
      if (!validateInputs()) return;
  
      loading = true;
      error   = null;
      result  = null;
  
      // parse optional headers
      let headers: Record<string,string> = {};
      try {
        headers = headers_raw ? JSON.parse(headers_raw) : {};
      } catch {
        error   = 'Invalid JSON in headers.';
        loading = false;
        return;
      }
  
      try {
        const res = await fetch('http://localhost:8000/api/sql_injection', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_url,
            port:      +port,
            timeout:   +timeout,
            headers,
            enum_level:+enum_level
          })
        });
  
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`${res.status} ${res.statusText}: ${text}`);
        }
  
        result = await res.json();
      } catch (err: any) {
        error = 'Failed to contact backend: ' + err.message;
      } finally {
        loading = false;
      }
    }
  </script>
  
  <div class="crawlerConfigPage">
    <h1>SQL Injection Tool</h1>
  
    <!-- ─────────────── configuration form ─────────────── -->
    <form on:submit|preventDefault={runInjection}>
      <label>
        Target URL
        <input
          placeholder="http://example.com"
          bind:value={target_url}
        />
      </label>
  
      <label>
        Port
        <input type="number" bind:value={port} />
      </label>
  
      <label>
        Timeout (sec)
        <input type="number" bind:value={timeout} />
      </label>
  
      
  
      <label>
        Optional Headers (JSON)
        <textarea rows="4" bind:value={headers_raw}></textarea>
      </label>
  
      <button type="submit" disabled={loading}>
        {loading ? 'Running…' : 'Run Injection'}
      </button>
    </form>
  
    <!-- ─────────────── results / status ─────────────── -->
    {#if loading}
      <p>Loading…</p>
  
    {:else if error}
      <p style="color:red;">{error}</p>
  
    {:else if result}
      <h2>Scan Results</h2>
      <p><strong>Vulnerable:</strong> {result.vulnerable ? 'Yes' : 'No'}</p>
  
      <div class="results-container">
        <table class="results-table">
          <thead>
            <tr>
              <th>Payload</th>
              <th>Status</th>
              <th>Snippet</th>
            </tr>
          </thead>
          <tbody>
            {#each result.results as r}
              <tr>
                <td>{r.payload}</td>
                <td>{r.status_code}</td>
                <td><pre class="snippet">{r.snippet}</pre></td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
  
      {#if result.tables}
        <h3>Enumerated Tables</h3>
        <ul>
          {#each result.tables as table}
            <li>{table}</li>
          {/each}
        </ul>
      {/if}
    {/if}
  </div>
  
  <style>

    .snippet {
      white-space: pre-wrap;
      background: #111;
      color: #0f0;
      padding: 0.75rem;
      border-radius: 6px;
    }
  </style>
  