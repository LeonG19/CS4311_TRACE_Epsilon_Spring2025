<script>
  import { onMount } from 'svelte';
  import { preventDefault } from "svelte/legacy";
  let wordlistInput = { id: "word_list", type: "file", accept: ".json, .txt", label: "Word List", value: "", example: "Ex: wordlist.txt", required: true };

  let bruteForceInput = [
    { id: "target_url", label: "Target URL", type: "text", value: "", example: "Ex: https://example.com/path", required: true },
    { id: "top_level_directory", label: "Top Level Directory", type: "text", value: "", example: "/", required: true },
    { id: "hide_status_code", label: "Hide Status Code", type: "text", value: "", example: "403, 500", required: false },
    { id: "show_status_code", label: "Show Only Status Code", type: "text", value: "", example: "200, 500", required: false },
    { id: "filter_by_content_length", label: "Filter by Content Length", type: "number", value: "", example: ">100, <500", required: false },
    { id: "additional_param", label: "Additional Parameter", type: "text", value: "", example: "Ex: some_param=value", required: false }
  ];

  let bruteForceParams = {
    target_url: "", 
    word_list: "",
    additional_param: "",
    show_results: true
  };

  let results = [];
  let acceptingParams = true;
  let isRunning = false;
  let displayingResults = false;
  let showResultsButton = false; // New state variable
  let selectedFileName = "No file selected"; // Track selected file name
  let fileUploaded = false; // Track if file was successfully uploaded
  let activeController = null;
  let showTerminal = false;
  let logOutput = '';
  let visibleResults=[];
  let popoutWindow;
  let terminalOutput = []; 
  let formattedLine;

  // Track progress
  let progress = 0;
  let processedRequests = 0;
  let filteredRequests = 0;
  let requestsPerSecond = 0;
  let startTime = null;
  let elapsedTime = "0s";
  let timerInterval;

  // Control flags
  let pauseAvailable = true;
  let resumeAvailable = false;
  
  //database project name for path
  let projectName = ""; // to store the project name

  //applying crawler sorter i added over there to here
  let sortConfig = {
  column: "",
  direction: 'asc'
  };

  function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
      const seconds = Math.floor((Date.now() - startTime) / 1000);
      elapsedTime = `${seconds}s`;
    }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
  }

  function paramsToRunning() {
    acceptingParams = false;
    isRunning = true;
    showResultsButton = false; // Reset button 
  }

  function runningToResults() {
    isRunning = false;
    displayingResults = true;
    showResultsButton = true; // Hide button after navigating
  }

  function resultsToParams() {
    displayingResults = false;
    isRunning = false;   
    acceptingParams = true;
    results = [];
  }

  function pauseBruteForce(e) {
    preventDefault(e);
    pauseToResumeButton();
    stopTimer();
    addToTerminal('Pausing BruteForce..', 'warning');
    apiCall('pause_brute', () => {}, 'BruteForce paused');
  }

  function resumeBruteForce(e){
    preventDefault(e);
    resumeToPauseButton();
    startTimer();
    addToTerminal('Resuming BruteForce...', 'success');
    apiCall('resume_brute', () => {}, 'BruteForce resumed');
  }

  function stopBruteForce() {
    stopTimer();
    isRunning = false;
    displayingResults= true;
    addToTerminal('Stopping BruteForce...', 'error');
    
    if (activeController) activeController.abort();
    apiCall('stop_brute', () => {}, 'BruteForce stopped');
  }

  function restartBruteForce() {
    console.log("Restart clicked");
    terminalOutput = [];

    // If the popout is open, clear its contents
    if (popoutWindow && !popoutWindow.closed) {
      const termEl = popoutWindow.document.getElementById('terminal-content');
      if (termEl) termEl.innerHTML = '';
    }

    results = [];
    displayingResults = false; // hide final results
    stopTimer();
    handleSubmit(); // starts fresh
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

  function resetTimer() {
    stopTimer();
    elapsedTime = "0s";
  }

  function dynamicBruteForceParamUpdate(id, value) {
    bruteForceParams[id] = value;
    if (id === 'hide_status_code') {
      bruteForceParams.hide_status = value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));
    }

    if (id === 'show_status_code') {
      bruteForceParams.show_status = value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));
    }

    if (id === 'filter_by_content_length') {
      const numeric = parseInt(value);
      if (!isNaN(numeric)) bruteForceParams.filter_by_content_length = numeric;
    }

    if (id === 'additional_param') {
    bruteForceParams.additional_param = value;
    }

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

  // Function to handle file upload for wordlist
  async function handleFile(event) {
    console.log("File Submitted");
    
    const fileInput = event.target;
    if (!fileInput.files || fileInput.files.length === 0) {
      console.log("No file selected");
      selectedFileName = "No file selected";
      fileUploaded = false;
      return;
    }
    
    const file = fileInput.files[0];
    selectedFileName = file.name;
    console.log("Selected file:", file.name);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/upload-wordlist', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }
      
      const result = await response.json();
      console.log("File uploaded successfully:", result);
      
      bruteForceParams.word_list = result.path;
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
        statusElement.textContent = `Error uploading the file: ${error.message}`;
        statusElement.className = 'selected-file error';
      }
    }
  }

  // inputs to be sent to the backend for brute-forcing
  async function handleSubmit() {
    console.log("handleSubmit called");

    // Validation checks for required fields
    if (!bruteForceParams.target_url) {
      alert('Target URL is required');
      return;
    }

    if (!fileUploaded && !bruteForceParams.word_list) {
      alert('Please upload a wordlist file first');
      return;
    }

    console.log("Brute force parameters before fetch:", bruteForceParams); // Debugging log

    // Reset state
    paramsToRunning();
    resetTimer();
    startTimer();
    progress = 0;
    processedRequests = 0;
    filteredRequests = 0;
    requestsPerSecond = 0;
    results = [];
    logOutput = [];
    pauseAvailable = true;
    resumeAvailable = false;

    // Abort previous request if any
    activeController = new AbortController();

    try {
      // Send the brute-force request
      const response = await fetch('http://localhost:8000/bruteforcer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bruteForceParams),
        signal: activeController.signal
      });

      // Handle non-OK responses
      if (!response.ok) {
        throw new Error(`Brute force request failed: ${response.status}`);
      }

      // Read the response in chunks
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          // Show results button after completion
          showResultsButton = true;
          stopTimer();
          runningToResults(); // Transition to results page

          // Submit the brute-force results to the project
          await submitbruteResultsToProject(); // Submit results after brute force finishes
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
          try {
            // Parse each line of response data
            const update = JSON.parse(line);
            console.log('Received update:', update); // Debugging missing table entries

            // Update progress and stats
            if (update.progress) {
              progress = update.progress * 100;
            }
            processedRequests = update.processed_requests || processedRequests;
            filteredRequests = update.filtered_requests || filteredRequests;
            requestsPerSecond = update.requests_per_second || requestsPerSecond;

            // Handle payload results and update terminal/log output
            if (update.payload) {
              addToTerminal(update, ''); // Update terminal with the result
              results = [...results, update]; // Add to results array
              logOutput += `[${update.response}] ${update.payload} \t ${update.length} bytes \t ${update.words} words\n`
            }
          } catch (error) {
            // Handle any parsing errors
            addToTerminal(`ERROR: ${error.message}`, 'error');
          }
        }
      }
    } catch (error) {
      // Handle any errors during the fetch process
      addToTerminal(`ERROR: ${error.message}`, 'error');
      showResultsButton = true;
      stopTimer();
    }
  }

  function exportResults() { 
    const dataStr = JSON.stringify(results, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

    const exportFileDefaultName = 'bruteforce_results.json';

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }

  function sortTable(column) {
    const { direction } = sortConfig;

    // Toggle sorting direction
    sortConfig.direction = direction === 'asc' ? 'desc' : 'asc';
    sortConfig.column = column;

    console.log(`Sorting by column: ${column}, direction: ${sortConfig.direction}`);

    results = [...results].sort((a, b) => {
      const aValue = a[column];
      const bValue = b[column];

      // Ensure we are working with numbers where appropriate
      const aValueParsed = typeof aValue === 'number' ? aValue : parseFloat(aValue);
      const bValueParsed = typeof bValue === 'number' ? bValue : parseFloat(bValue);

      if (aValueParsed < bValueParsed) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      } else if (aValueParsed > bValueParsed) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }

    // toggleTerminal function
  function toggleTerminal(e) {
    if (e) preventDefault(e);
    
    if (popoutWindow && !popoutWindow.closed) {
      popoutWindow.focus();
      return;
    }
    
    const width = 600, height = 400;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    
    popoutWindow = window.open('', 'BruteForceWindow', 
      `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`);
    
    const doc = popoutWindow.document;
    doc.title = "BruteForce Terminal Output";
    
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
        <span>BruteForce Terminal Output</span>
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
    if (typeof result === 'string') {
      // just log the message
      formattedLine = result;
    } else {
      // assume it's a full scan-result object
      const id   = String(result.id || '').padStart(2, '0');
      formattedLine = `${id} : ${result.response} ${result.lines} L ${result.words} W ${result.chars} CH`;
    }
    logOutput += formattedLine + '\n';
    terminalOutput.push({ text: formattedLine, type });
    if (popoutWindow && !popoutWindow.closed) {
      popoutWindow.addTerminalLine(formattedLine, type);
    }
  }

  onMount(() => {
    projectName = "Mayra_Demo"; //hardcoded for testing into db
    bruteForceParams.project_name = projectName;
    console.log("Project Name:", projectName);
  });

  // this is where we pass the file to db
  async function submitbruteResultsToProject() {
    try {
      // Ensure the `results` variable holds the actual brute force results as a JSON object
      const resultsData = {
        type: "bruteforcer", // Set type to "bruteforcer"
        projectName: projectName, // Ensure this is set correctly before calling
        results: results // This is the actual results from brute force, should be a JSON object
      };

      console.log("Submitting brute force results to project:", resultsData); // Debugging log

      // Sending the POST request with the results to the appropriate endpoint
      const response = await fetch(`http://localhost:8000/submit_results/bruteforcer/${projectName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(resultsData) // Send the `resultsData` as the body
      });

      if (!response.ok) {
        throw new Error(`Failed to submit results: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("Results submitted successfully:", result);
      addToTerminal('Results submitted successfully', 'success'); // Update the terminal with success message
    } catch (error) {
      console.error("Error submitting brute force results:", error);
      addToTerminal(`Error submitting results: ${error.message}`, 'error'); // Update the terminal with error message
    }
  }

</script>

<div class="bruteForceConfigPage">
  <div>
    <h1>Brute Force Configuration</h1>

    {#if acceptingParams}
      <div>
        <form on:submit={(e) => {e.preventDefault(); handleSubmit()}}>
          {#each bruteForceInput as param}
            {#if param.type === 'file'}
              <div>
                <label for={param.id}><span>{param.label}</span></label>
                <input
                  id={param.id}
                  accept={param.accept}
                  type={param.type}
                  required={param.required}
                  on:change={handleFile}
                />
                <div id="file-status" class="selected-file">{selectedFileName}</div>
              </div>
            {:else}
              <div>
                <label for={param.id}>{param.label}:</label>
                <input
                  id={param.id}
                  type={param.type}
                  bind:value={bruteForceParams[param.id]}
                  placeholder={param.example}
                  required={param.required}
                  on:input={(e) => dynamicBruteForceParamUpdate(param.id, e.target.value)}
                />
              </div>
            {/if}
          {/each}

          <div>
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

          <button type="submit" class="submit-button">Start Brute Force</button>
          <a href="/main/tools" class="home-button">Return To Tools</a>

        </form>
      </div>
    {/if}

    {#if isRunning}
    <div class = "brute-section">
      <div>
        <h2>Running...</h2>
        <!-- Progress Bar -->
        <div class="progress-bar">
          <div class="progress" style="width: {progress}%"></div>
        </div>
        <!-- Metrics -->
        <div class="metrics">
          <div class="metric-item">
            <strong>Processed</strong>
            <span>{processedRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Filtered</strong>
            <span>{filteredRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Requests/sec</strong>
            <span>{requestsPerSecond}</span>
          </div>
          <div class="metric-item">
            <strong>Elapsed Time</strong>
            <span>{elapsedTime}</span>
          </div>
        </div>
        <!-- Live Table -->
        <div class = "results-table-scrollable">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Lines</th>
              <th>Words</th>
              <th>Chars</th>
              <th>Payload</th>
              <th>Length</th>
            </tr>
          </thead>
          <tbody>
            {#each results as result, index}
              <tr>
                <td>{index + 1}</td>
                <td>{result.response}</td>
                <td>{result.lines}</td>
                <td>{result.words}</td>
                <td>{result.chars}</td>
                <td>{result.payload}</td>
                <td>{result.length}</td>
              </tr>
            {/each}
          </tbody>
        </table>
        </div>
      </div>
    </div>
    {/if}

    {#if displayingResults}
      <div class = "brute-section">
        <h2>Brute Force Results</h2>
        <div class="metrics">
          <div class="metric-item">
            <strong>Running Time:</strong>
            <span>{elapsedTime}</span>
          </div>
          <div class="metric-item">
            <strong>Processed Requests:</strong>
            <span>{processedRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Filtered Requests:</strong>
            <span>{filteredRequests}</span>
          </div>
          <div class="metric-item">
            <strong>Requests/sec:</strong>
            <span>{requestsPerSecond}</span>
          </div>
        </div>

        <div class = "results-table-scrollable">
        <table>
          <thead>
            <tr>
              <th on:click={() => sortTable('id')}>ID
                {#if sortConfig.column === 'id'}
                  {sortConfig.direction === 'asc' ? '▲' : '▼'}
                {/if}
              </th>
              <th on:click={() => sortTable('response')}>Response
                {#if sortConfig.column === 'response'}
                  {sortConfig.direction === 'asc' ? '▲' : '▼'}
                {/if}
              </th>
              <th on:click={() => sortTable('lines')}>Lines
                {#if sortConfig.column === 'lines'}
                  {sortConfig.direction === 'asc' ? '▲' : '▼'}
                {/if}
              </th>
              <th on:click={() => sortTable('words')}>Words
                {#if sortConfig.column === 'words'}
                  {sortConfig.direction === 'asc' ? '▲' : '▼'}
                {/if}
              </th>
              <th on:click={() => sortTable('chars')}>Chars
                {#if sortConfig.column === 'chars'}
                  {sortConfig.direction === 'asc' ? '▲' : '▼'}
                {/if}
              </th>
              
              <th>Payload</th>

              <th on:click={() => sortTable('length')}>Length
                {#if sortConfig.column === 'length'}
                  {sortConfig.direction === 'asc' ? '▲' : '▼'}
                {/if}
              </th>
            </tr>
          </thead>
          <tbody>
            {#each results as result (result.id)} <!-- Key by result.id -->
              <tr>
                <td>{result.id}</td> <!-- Display result.id instead of index + 1 -->
                <td>{result.response}</td>
                <td>{result.lines}</td>
                <td>{result.words}</td>
                <td>{result.chars}</td>
                <td>{result.payload}</td>
                <td>{result.length}</td>
              </tr>
            {/each}
          </tbody>
        </table>
        </div>
      </div>
    {/if}
  </div>
</div>

  <!-- ✅ These are always visible when done -->
  {#if isRunning || displayingResults}
  <div class="action-buttons-bottom">
    {#if pauseAvailable}
    <button on:click={pauseBruteForce}>Pause</button>
    {/if}
    {#if resumeAvailable}
      <button on:click={resumeBruteForce}>Resume</button>
    {/if}
    <button on:click={stopBruteForce}>Stop</button>
    <button on:click={restartBruteForce}>Restart</button>
    <button on:click={toggleTerminal}>View Terminal</button>
    <button on:click={() => resultsToParams()}>Back to Param Setup</button>
    {#if showResultsButton}
      <button on:click={exportResults}>Export Results</button>
    {/if}
  </div>
{/if}

<!-- Optional fallback -->
{#if !acceptingParams && !isRunning && !displayingResults}
  <p style="color: red; text-align: center; margin-top: 2rem;">⚠️ Nothing is being displayed. Check state logic.</p>
{/if}

<style>
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

  /* .results-table {
    margin-top: 20px; 
  }

  .results-table button {
    margin-top: 20px; 
  } */

  .brute-section {
    background-color: #1f1f1f;
    padding: 1.5rem;
    border-radius: 1rem;
    margin-top: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }

  .bruteForceConfigPage {
  width: 100%;  /* Adjusted width to give more space */
  margin: 10vh auto; /* Centered with some spacing from the top */
  padding: 20px;
  background: transparent;
  border-radius: 8px;
  /* box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); */
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #f5f5f5; /* Set text color to dark gray for better contrast */
}

  .results-table-scrollable {
    height: 400px;
    overflow-y: auto;
    border: 1px solid #ccc;
    border-radius: 10px;
    margin-top: 1rem;
  }

  .action-buttons-bottom {
    margin-top: 2rem;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 1rem;
  }

  .action-buttons-bottom button {
    background-color:  #3b82f6;
    color: white;
    padding: 0.75rem 1.5rem;
    font-weight: bold;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .action-buttons-bottom button:hover {
    background-color: #2563eb;
  }

  /* .terminal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999;
  }

  .terminal-window {
    background: #111;
    color: rgb(255, 255, 255);
    width: 80%;
    max-height: 70vh;
    border-radius: 8px;
    overflow-y: auto;
    padding: 1rem;
  }

  .terminal-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .terminal-content {
    font-family: monospace;
    white-space: pre-wrap;
    word-break: break-word;
  } */

  /* Button styling */
  .home-button {
    border-radius: 8px;
    border: 1px solid transparent;
    padding: 0.6em 1.2em;
    font-size: 1em;
    font-weight: 500;
    font-family: inherit;
    background-color: #3b82f6;
    cursor: pointer;
    transition: border-color 0.25s;
    text-decoration: none;
    width: 100%;
    max-width: 450px; /* Matches input size */
    color: white;
    text-align: center;

  }

  .home-button:hover {
    background-color: #2563eb;
  }
  
  .home-button:focus,
  .home-button:focus-visible {
    outline: 4px auto -webkit-focus-ring-color;
  }


</style>