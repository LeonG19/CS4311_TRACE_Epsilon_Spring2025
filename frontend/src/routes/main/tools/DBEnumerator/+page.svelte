<script>
  let dbInputs = [
    {
      id: "host",
      label: "Target URL (DB Host)",
      type: "text",
      value: "",
      example: "127.0.0.1 or remote-db.server.com",
      tooltip: "The database host address (e.g., localhost or external IP)",
      required: true
    },
    {
      id: "port",
      label: "Port",
      type: "number",
      value: "3306",
      example: "3306",
      tooltip: "Default MySQL port is 3306. Adjust if needed.",
      required: true
    },
    {
      id: "username",
      label: "Username",
      type: "text",
      value: "",
      example: "root",
      tooltip: "Database username with privileges to enumerate.",
      required: true
    },
    {
      id: "password",
      label: "Password",
      type: "password",
      value: "",
      example: "your_password",
      tooltip: "The password for the database user.",
      required: true
    }
  ];

  let dbParams = {
    host: '',
    port: 3306,
    username: '',
    password: ''
  };

  let dbResult = null;
  let loading = false;
  let error = null;
  let statusText = "Waiting for input...";
  let progress = 0;
  let errorMessages = {
    host: "",
    port: "",
    username: "",
    password: ""
  };

  function dynamicParamUpdate(id, value) {
    dbParams[id] = value;
  }

  async function handleSubmit(event) {
    dbResult = null;
    error = null;
    loading = true;
    event.preventDefault();
    statusText = "Connecting to database...";
    progress = 25;

    let isValid = true;
    Object.keys(errorMessages).forEach(key => errorMessages[key] = "");

    if (!dbParams.host) {
      errorMessages.host = "Target URL is required!";
      isValid = false;
    }
    if (!dbParams.username) {
      errorMessages.username = "Username is required!";
      isValid = false;
    }
    if (!dbParams.password) {
      errorMessages.password = "Password is required!";
      isValid = false;
    }

    if (!isValid) {
      loading = false;
      statusText = "Validation failed.";
      progress = 0;
      return;
    }

    try {
      progress = 50;
      const response = await fetch('http://localhost:8000/api/db_enumerator', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host: dbParams.host,
          port: parseInt(dbParams.port),
          username: dbParams.username,
          password: dbParams.password
        })
      });

      progress = 75;
      if (!response.ok) throw new Error("Failed to fetch results.");
      dbResult = await response.json();
      statusText = "Enumeration Complete!";
    } catch (err) {
      error = err.message;
      statusText = "Error encountered.";
    } finally {
      loading = false;
      progress = 100;
    }
  }

  function downloadResults() {
    if (!dbResult) return;
    const blob = new Blob([JSON.stringify(dbResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    a.href = url;
    a.download = `db_enum_${dbParams.host}_${timestamp}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="dbEnumContainer">
  <h1>Database Enumerator</h1>

  <div class="status-bar">
    <p>{statusText}</p>
    {#if loading || progress > 0}
      <div class="progress-bar">
        <div class="progress" style="width: {progress}%"></div>
      </div>
    {/if}
  </div>

  <form on:submit={handleSubmit}>
    {#each dbInputs as input}
      <label title={input.tooltip}>
        <span>{input.label}</span>
        <input
          type={input.type}
          bind:value={dbParams[input.id]}
          placeholder={input.example}
          required={input.required}
          on:input={(e) => dynamicParamUpdate(input.id, e.target.value)}
        />
        {#if errorMessages[input.id]}
          <p class="error">{errorMessages[input.id]}</p>
        {/if}
      </label>
    {/each}
    <button type="submit" disabled={loading}>{loading ? "Enumerating..." : "Run Enumeration"}</button>
  </form>

  {#if error}
    <div class="error">Error: {error}</div>
  {/if}

  {#if dbResult}
    <div class="results">
      <h2>Enumeration Results</h2>
      <pre>{JSON.stringify(dbResult, null, 2)}</pre>
      <button on:click={downloadResults}>Download JSON</button>
    </div>
  {/if}
</div>

<style>
  .dbEnumContainer {
    max-width: 700px;
    margin: 30px auto;
    padding: 20px;
    border: 2px solid #444;
    border-radius: 10px;
    background: #1e1e1e;
    color: white;
  }

  input {
    width: 100%;
    padding: 8px;
    margin: 6px 0 12px;
    border: 1px solid #999;
    border-radius: 5px;
    background: #2e2e2e;
    color: white;
  }

  button {
    padding: 10px 20px;
    background-color: #007bff;
    border: none;
    border-radius: 6px;
    color: white;
    cursor: pointer;
  }

  button:hover {
    background-color: #0056b3;
  }

  .status-bar {
    margin-bottom: 20px;
    font-weight: bold;
  }

  .progress-bar {
    width: 100%;
    background-color: #444;
    height: 10px;
    border-radius: 5px;
    overflow: hidden;
    margin-top: 5px;
  }

  .progress {
    width: 0%;
    height: 100%;
    background-color: #646cff;
    transition: width 0.5s ease-in-out;
  }

  .results {
    margin-top: 20px;
    padding: 15px;
    border: 1px solid #666;
    background: #2c2c2c;
    border-radius: 8px;
  }

  .error {
    margin-top: 10px;
    color: red;
    font-size: 0.85rem;
  }

  label {
    display: block;
    margin-bottom: 15px;
  }

  span {
    font-weight: bold;
    display: flex;
    align-items: center;
    margin-bottom: 5px;
  }
</style>
