<script>
  import { preventDefault } from "svelte/legacy";

  // Input conf
  let wordlistInput = { id: "word_list", type: "file", accept: ".json, .txt", label: "Word List", required: true };
  let fuzzerInput = [
    { id: "target_url", label: "Target URL", type: "text", example: "Ex: https://example.com", required: true },
    { id: "http_method", label: "HTTP Method", type: "select", options: ["GET", "POST", "PUT"], value: "GET", required: true },
    { id: "cookies", label: "Cookies", type: "text", example: "NULL", required: false },
    { id: "hide_status", label: "Hide Status Code", type: "text", example: "404,403,etc", required: false },
    { id: "show_status", label: "Show Status Code", type: "text", example: "200,500,etc", required: false },
    { id: "filter_by_content_length", label: "Filter by Content Length", type: "text", example: ">100,>500,etc", required: false },
    { id: "proxy", label: "Proxy", type: "text", example: "http://proxy:port", required: false },
    { id: "additional_parameters", label: "Additional Parameters", type: "text", example: "NULL", required: false }
  ];

  // State variables
  let fuzzerParams = { target_url: "", word_list: "", show_results: true };
  let results = []; 
  let acceptingParams = true;
  let isRunning = false;
  let displayingResults = false;
  let selectedFileName = "No file selected";
  let fileUploaded = false;
  let activeController = null;
  let popoutWindow = null;
  let terminalOutput = [];
  
  // Progress tracking
  let progress = 0;
  let processedRequests = 0;
  let filteredRequests = 0;
  let requestsPerSecond = 0;
  let startTime = null;
  let accumulatedTime = 0;
  let elapsedTime = "0s";
  let timerInterval;
  
  // Control flags
  let pauseAvailable = true;
  let resumeAvailable = false;
  
  // Sorting configuration
  let sortConfig = { column: "", direction: 'asc' };

  // Navigation functions
  function goBack() { window.location.href = "/main/tools"; }
  
  function paramsToRunning() {
    acceptingParams = false;
    isRunning = true;
  }
  
  function runningToResults(e) {
    if (e) preventDefault(e);
    isRunning = false;
    displayingResults = true;
  }
  
  function resultsToParams(e) {
    if (e) preventDefault(e);
    displayingResults = false;
    acceptingParams = true;
    results = [];
    terminalOutput = [];
  }
  
  // Timer 
  function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
      const currentElapsed = Date.now() - startTime;
      const totalElapsed = accumulatedTime + currentElapsed;
      elapsedTime = `${Math.floor(totalElapsed / 1000)}s`;
    }, 1000);
  }
  
  function stopTimer() {
    clearInterval(timerInterval);
    if (startTime) accumulatedTime += Date.now() - startTime;
  }
  
  function resetTimer() {
    clearInterval(timerInterval);
    accumulatedTime = 0;
    elapsedTime = '0s';
  }
  
  // Button state 
  function pauseToResumeButton() {
    pauseAvailable = false;
    resumeAvailable = true;
  }
  
  function resumeToPauseButton() {
    resumeAvailable = false;
    pauseAvailable = true;
  }
  
  // input changes
  function dynamicFuzzerParamUpdate(id, value) {
    fuzzerParams[id] = value;
  }
  
  // Sort function
  function sortTable(column) {
    sortConfig.direction = sortConfig.column === column && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    sortConfig.column = column;
    
    results = [...results].sort((a, b) => {
      const aValue = a[column];
      const bValue = b[column];
      
      // numeric vals
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      //strings
      const aString = String(aValue || '').toLowerCase();
      const bString = String(bValue || '').toLowerCase();
      return sortConfig.direction === 'asc' ? aString.localeCompare(bString) : bString.localeCompare(aString);
    });
  }
    // toggleTerminal function
  function toggleTerminal(e) {
    if (e) preventDefault(e);
    
    if (popoutWindow && !popoutWindow.closed) {
      popoutWindow.focus();
      return;
    }
    
    const width = 400, height = 300;//smaller terminal dimensions test
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    
    popoutWindow = window.open('', 'fuzzerTerminal', 
      `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`);
    
    const doc = popoutWindow.document;
    doc.title = "Fuzzer Terminal Output";
    
    // Add styles
    doc.head.innerHTML = `
      <style>
        body {
          font-family: monospace;
          margin: 0;
          padding: 0;
          background-color: #242424;
          color: #FFFFFF;
        }
        .terminal-header {
          background-color: #333;
          padding: 8px 10px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .terminal-content {
          padding: 10px;
          height: calc(100vh - 40px);
          overflow-y: auto;
        }
        .terminal-line {
          white-space: pre;
          margin-bottom: 3px;
        }
        .success { color: #4CAF50; }
        .warning { color: #FF9800; }
        .error { color: #F44336; }
        .auto-scroll {
          margin: 0 15px;
          display: flex;
          align-items: center;
          color: white;
        }
        .auto-scroll input {
          margin-right: 5px;
        }
      </style>
    `;
    
    // auto-scroll checkbox for terminal
    doc.body.innerHTML = `
      <div class="terminal-header">
        <span>Fuzzer Terminal Output</span>
        <div class="auto-scroll">
          <input type="checkbox" id="auto-scroll" checked>
          <label for="auto-scroll">Auto-scroll</label>
        </div>
      </div>
      <div id="terminal-content" class="terminal-content"></div>
    `;
    
    //  add lines
    const script = doc.createElement('script');
    script.textContent = `
      const terminalContent = document.getElementById('terminal-content');
      const autoScrollCheckbox = document.getElementById('auto-scroll');
      
      window.addTerminalLine = function(text, type) {
        const line = document.createElement('div');
        line.className = 'terminal-line';
        if (type) {
          line.classList.add(type);
        }
        line.textContent = text;
        terminalContent.appendChild(line);
        
        if (autoScrollCheckbox.checked) {
          terminalContent.scrollTop = terminalContent.scrollHeight;
        }
      };
    `;
    doc.body.appendChild(script);
    
    // Add existing lines
    terminalOutput.forEach(entry => {
      try {
        popoutWindow.addTerminalLine(entry.text, entry.type);
      } catch (e) {
        console.error('Error adding line to terminal:', e);
      }
    });
  }

  function addToTerminal(result, type = '') {
    const id = String(result.id).padStart(2, '0');
    const formattedLine = `${id} : ${result.response} ${result.lines} L ${result.words} W ${result.chars} CH `;
    terminalOutput.push({ text: formattedLine, type });
    
    if (popoutWindow && !popoutWindow.closed) {
      try {
        popoutWindow.addTerminalLine(formattedLine, type);
      } catch (e) {
        console.error('Error updating terminal:', e);
      }
    }
  }

  // File handle
  async function handleFile(event) {
    const fileInput = event.target;
    if (!fileInput.files || fileInput.files.length === 0) {
      selectedFileName = "No file selected";
      fileUploaded = false;
      return;
    }
    
    const file = fileInput.files[0];
    selectedFileName = file.name;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/upload-wordlist', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
      
      const result = await response.json();
      fuzzerParams.word_list = result.path;
      fileUploaded = true;
      
      const statusElement = document.querySelector('#file-status');
      if (statusElement) {
        statusElement.textContent = `File uploaded: ${file.name}`;
        statusElement.className = 'selected-file success';
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      fileUploaded = false;
      
      const statusElement = document.querySelector('#file-status');
      if (statusElement) {
        statusElement.textContent = `Error uploading file: ${error.message}`;
        statusElement.className = 'selected-file error';
      }
    }
  }
  
  // Export functions
  function exportResults(e) {
    if (e) preventDefault(e);
    const dataStr = JSON.stringify(results, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = 'fuzz_results.json';
    const link = document.createElement('a');
    link.setAttribute('href', dataUri);
    link.setAttribute('download', exportFileDefaultName);
    link.click();
  }
  
  function exportToCSV(e) {
    if (e) preventDefault(e);
    let filename = urlToFilename(fuzzerParams.target_url || 'fuzz_results');
    
    const keys = results.length > 0 ? Object.keys(results[0]) : [];
    const headerRow = keys.join(',');
    
    const dataRows = results.map(row => {
      return keys.map(key => {
        if (row[key] === null || row[key] === undefined) return '""';
        if (typeof row[key] === 'object') return `"${JSON.stringify(row[key]).replace(/"/g, '""')}"`;
        return `"${String(row[key]).replace(/"/g, '""')}"`;
      }).join(',');
    });
    
    const csvContent = [headerRow, ...dataRows].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  function urlToFilename(url) {
    return url
      .replace(/^https?:\/\//, '')
      .replace(/[^a-z0-9]/gi, '_')
      .toLowerCase();
  }
  
  // API call functions with unified error handling
  async function apiCall(endpoint, onSuccess, messagePrefix) {
    try {
      const response = await fetch(`http://localhost:8000/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const result = await response.json();
        onSuccess(result);
        addToTerminal(`${messagePrefix}: ${result.message}`, endpoint.includes('resume') ? 'success' : 
                                                             endpoint.includes('pause') ? 'warning' : 'error');
      } else {
        addToTerminal(`Error with ${endpoint}: ${response.statusText}`, 'error');
      }
    } catch (error) {
      addToTerminal(`Error: ${error.message}`, 'error');
    }
  }
  
  // Handling functions
  function handlePauseFuzz(e) {
    preventDefault(e);
    pauseToResumeButton();
    stopTimer();
    addToTerminal('Pausing fuzzer...', 'warning');
    apiCall('pause_fuzzer', () => {}, 'Fuzzer paused');
  }
  
  function handleResumeFuzz(e) {
    preventDefault(e);
    resumeToPauseButton();
    startTimer();
    addToTerminal('Resuming fuzzer...', 'success');
    apiCall('resume_fuzzer', () => {}, 'Fuzzer resumed');
  }
  
  function handleStopFuzz(e) {
    preventDefault(e);
    stopTimer();
    addToTerminal('Stopping fuzzer...', 'error');
    
    if (activeController) activeController.abort();
    apiCall('stop_fuzzer', () => {}, 'Fuzzer stopped');
  }
  
  function handleRestartFuzz(e) {
    preventDefault(e);
    results = [];
    terminalOutput = [];
    resetTimer();
    handleSubmit();
  }
  
  // Main handler
  async function handleSubmit() {
    if (!fuzzerParams.target_url) {
      alert('Target URL is required');
      return;
    }
    
    if (!fileUploaded && !fuzzerParams.word_list) {
      alert('Please upload a wordlist file first');
      return;
    }
    
    // Reset state
    paramsToRunning();
    resetTimer();
    startTimer();
    progress = 0;
    processedRequests = 0;
    filteredRequests = 0;
    requestsPerSecond = 0;
    results = [];
    terminalOutput = [];
    pauseAvailable = true;
    resumeAvailable = false;
    
    //abort 
    activeController = new AbortController();
    
    try {
      const response = await fetch('http://localhost:8000/fuzzer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fuzzerParams),
        signal: activeController.signal
      });
      
      if (!response.ok) throw new Error(`Fuzzing request failed: ${response.status}`);
      
      // Process streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          stopTimer();
          break;
        }
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          try {
            const update = JSON.parse(line);
            
            // Update progress metrics
            if (update.progress) progress = update.progress * 100;
            processedRequests = update.processed_requests || processedRequests;
            filteredRequests = update.filtered_requests || filteredRequests;
            requestsPerSecond = update.requests_per_second || requestsPerSecond;
            
            // Handle payload results
            if (update.payload) {
              // Determine status type
              let type = update.response >= 400 ? 'error' : 
                        update.response >= 300 ? 'warning' : 'success';
  
              // Add to terminal with the full result object
              addToTerminal(update, type);
  
              // Add to results table and terminal
              results = [...results, update];
              //logOutput += `[${update.response}] ${update.payload}\n`;
            }
          } catch (error) {
            addToTerminal(`ERROR: ${error.message}`, 'error');
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        addToTerminal('Fuzzing operation aborted.', 'error');
      } else {
        addToTerminal(`ERROR: ${error.message}`, 'error');
      }
      stopTimer();
    }
  }
</script>

<div class="crawlerConfigPage">
  <div>
    <h1>Parameter Fuzzing</h1>

    {#if acceptingParams}
      <div>
        <form on:submit="{(e) => {e.preventDefault(); handleSubmit()}}">
          <div class="file-input-container">
            <label for="word_list">{wordlistInput.label}</label>
            <input
              id="word_list"
              accept={wordlistInput.accept}
              type="file"
              placeholder="No file selected."
              required={wordlistInput.required}
              on:change={handleFile}
            />
            <div id="file-status" class="selected-file">{selectedFileName}</div>
          </div>

          {#each fuzzerInput as param}
            {#if param.type === "select"}
              <div class="input-container">
                <label for={param.id}>{param.label}:</label>
                <select
                  id={param.id}
                  bind:value={fuzzerParams[param.id]}
                  required={param.required}
                  on:change={(e) => dynamicFuzzerParamUpdate(param.id, e.target.value)}
                >
                  {#each param.options as option}
                    <option value={option}>{option}</option>
                  {/each}
                </select>
              </div>
            {:else}
              <div class="input-container">
                <label for={param.id}>{param.label}:</label>
                <input
                  id={param.id}
                  type={param.type}
                  bind:value={fuzzerParams[param.id]}
                  placeholder={param.example}
                  required={param.required}
                  on:input={(e) => dynamicFuzzerParamUpdate(param.id, e.target.value)}
                />
              </div>
            {/if}
          {/each}

          <button type="submit" class="submit-button" title="Begin Fuzzing with set parameters">Start Fuzzing</button>
        </form>
      </div>
    {/if}

    {#if isRunning}
      <div class="crawl-section">
        <h2>Running...</h2>
        <div class="progress-bar">
          <div class="progress" style="width: {progress}%"></div>
        </div>
        <p>{progress.toFixed(0)}% Complete</p>
        
        <div class="metrics">
          <div class="metric-item">
            <strong>Running Time</strong>
            <span>{elapsedTime}</span>
          </div>
          <div class="metric-item">
            <strong>Processed Requests</strong>
            <span>{processedRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Filtered Requests</strong>
            <span>{filteredRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Requests/sec</strong>
            <span>{requestsPerSecond}</span>
          </div>
        </div>

        <!-- Results Table -->
        <div class="results-table">
          {#if results.length === 0}
            <p>No data has been received. Please wait...</p>
          {:else}
            <table>
              <thead>
                <tr>
                  <th on:click={() => sortTable('id')}>ID {sortConfig.column === 'id' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                  <th on:click={() => sortTable('response')}>Response {sortConfig.column === 'response' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                  <th on:click={() => sortTable('lines')}>Lines {sortConfig.column === 'lines' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                  <th on:click={() => sortTable('words')}>Words {sortConfig.column === 'words' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                  <th on:click={() => sortTable('chars')}>Chars {sortConfig.column === 'chars' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                  <th>Payload</th>
                  <th on:click={() => sortTable('length')}>Length {sortConfig.column === 'length' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {#each results as result (result.id)}
                  <tr>
                    <td>{result.id}</td>
                    <td class={result.response >= 400 ? 'error' : (result.response >= 300 ? 'warning' : 'success')}>
                      {result.response}
                    </td>
                    <td>{result.lines}</td>
                    <td>{result.words}</td>
                    <td>{result.chars}</td>
                    <td>{result.payload}</td>
                    <td>{result.length}</td>
                    <td>{result.error ? 'Yes' : 'No'}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
            
            <div class="action-buttons">
              <button on:click={runningToResults} class="go-to-results-button">Go to Fuzzing Results</button>
              <button on:click={exportResults} class="export-button">Export as JSON</button>
              <button on:click={exportToCSV} class="export-button">Export as CSV</button>
            </div>
          {/if}
        </div>

        <div class="action-buttons">
          {#if pauseAvailable}
            <button class="pause-button" on:click={handlePauseFuzz} title="Pauses Fuzzing">Pause Fuzzer</button>
          {/if}
          {#if resumeAvailable}
            <button class="resume-button" on:click={handleResumeFuzz} title="Resumes Fuzzing">Resume Fuzzer</button>
          {/if}
          <button class="stop-button" on:click={handleStopFuzz} title="Fully stops the Fuzzing">Stop Fuzzer</button>
          <button class="restart-button" on:click={handleRestartFuzz} title="Restarts Fuzzing with the set parameters">Restart</button>
          <button class="terminal-button" on:click={toggleTerminal} title="Displays Fuzzing in the terminal">Open Terminal</button>
        </div>

      </div>
    {/if}

    {#if displayingResults}
      <div class="crawl-section">
        <h2>Fuzzing Results</h2>
        <div class="metrics">
          <div class="metric-item">
            <strong>Running Time</strong>
            <span>{elapsedTime}</span>
          </div>
          <div class="metric-item">
            <strong>Processed Requests</strong>
            <span>{processedRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Filtered Requests</strong>
            <span>{filteredRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Requests/sec</strong>
            <span>{requestsPerSecond}</span>
          </div>
        </div>

        <div class="results-table">
          <table>
            <thead>
              <tr>
                <th on:click={() => sortTable('id')}>ID {sortConfig.column === 'id' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                <th on:click={() => sortTable('response')}>Response {sortConfig.column === 'response' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                <th on:click={() => sortTable('lines')}>Lines {sortConfig.column === 'lines' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                <th on:click={() => sortTable('words')}>Words {sortConfig.column === 'words' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                <th on:click={() => sortTable('chars')}>Chars {sortConfig.column === 'chars' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                <th>Payload</th>
                <th on:click={() => sortTable('length')}>Length {sortConfig.column === 'length' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {#each results as result (result.id)}
                <tr>
                  <td>{result.id}</td>
                  <td class={result.response >= 400 ? 'error' : (result.response >= 300 ? 'warning' : 'success')}>
                    {result.response}
                  </td>
                  <td>{result.lines}</td>
                  <td>{result.words}</td>
                  <td>{result.chars}</td>
                  <td>{result.payload}</td>
                  <td>{result.length}</td>
                  <td>{result.error ? 'Yes' : 'No'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
          
          <div class="action-buttons">
            <button on:click={resultsToParams} class="back-button" title="Navigates back to Fuzzing Parameters">Back to Param Setup</button>
            <button on:click={toggleTerminal} class="terminal-button" title="Opens a terminal to view">Open Terminal</button>
            <button on:click={exportResults} class="export-button" title="Exports results as a JSON file">Export as JSON</button>
            <button on:click={exportToCSV} class="export-button" title="Exports results as a CSV file">Export as CSV</button>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  /*using  global CSS for most stylesonly have specific ones here for fuzzer */
  .file-input-container {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-bottom: 10px;
  }

  .selected-file {
    font-size: 0.9em;
    margin-top: 5px;
    position: static;
    background: transparent;
  }

  .selected-file.success { color: #4CAF50; }
  .selected-file.error { color: #F44336; }

  .input-container {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .success { color: #4CAF50; }
  .warning { color: #FF9800; }
  .error { color: #F44336; }

  .progress-bar {
    width: 100%;
    background-color: #e0e0e0;
    border-radius: 5px;
    overflow: hidden;
    margin: 10px 0;
  }

  .progress {
    height: 20px;
    background-color: #646cff;
    transition: width 0.3s ease;
  }

  .results-table {
    margin-top: 20px;
    max-height: 300px;
    overflow: auto;
    border: 1px solid #333;
    border-radius: 5px;
    width: 100%;        /* keeps a static width */
    table-layout: fixed; /* Ensures equal column widths */
  }

  .results-table th,
  .results-table td {
    padding: 8px;
    text-align: left;
    border-bottom: 1px solid #ccc;
    white-space: nowrap; /* Prevents text from wrapping */
    overflow: hidden; /* Hides overflow text */
    text-overflow: ellipsis; /* Adds ellipsis for overflow text */
  }

  .action-buttons button {
    margin-top: 20px;
    margin-right: 10px;
    padding: 5px 10px;
    font-size: 1rem;
    width: auto;
    min-width: 80px;
  }

  .terminal-button {
    margin-left: 40px; /* Has the terminal button a little further right*/
  }

  th {
    position: sticky;
    top: 0;
    background-color: #646cff;
    color: white;
    padding: 10px;
    cursor: pointer;
  }
</style>