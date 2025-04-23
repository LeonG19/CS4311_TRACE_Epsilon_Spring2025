<script>
  import { preventDefault } from "svelte/legacy";

  let crawlerInput = [
    { id: "url", label: "Target URL", type: "text", value: "", example: "Ex: https://example.com", required: true },
    { id: "depth", label: "Crawl Depth", type: "number", value: "", example: "Ex: 2", required: false },
    { id: "max_pages", label: "Max Pages", type: "number", value: "", example: "Ex: 15", required: false },
    { id: "user_agent", label: "User Agent", type: "text", value: "", example: "Ex: Mozilla/5.0", required: false },
    { id: "delay", label: "Request Delay", type: "number", value: "", example: "Ex: 5", required: false },
    { id: "proxy", label: "Proxy", type: "text", value: "", example: "Ex: 8080", required: false }
  ];

  let crawlerParams = {
    url: "",
    depth: "",
    max_pages: "",
    user_agent: "",
    delay: "",
    proxy: ""
  };

  let crawlResult = []; // Updated dynamically during crawling

  let acceptingParams = true;
  let crawling = false;
  let displayingResults = false;

  let totalPages = 0;
  let crawledPages = 0;

  let startTime = null;
  let accumulatedTime = 0
  let elapsedTime = "0s";
  let timerInterval;

  let processedRequests = 0;
  let filteredRequests = 0;
  let requestsPerSecond = 0;
  let activeController = null;

  let pauseAvailable = 1
  let resumeAvailable = 0

  let errorMessages = {
    url: "",
    max_pages: "",
    depth: "",
    delay: "",
    proxy: "",
  };

  // Correct initialization of sortConfig
  let sortConfig = {
    column: "",
    direction: 'asc'
  };

  // Start timer function
  // function startTimer() {
  //   startTime = Date.now();
  //   timerInterval = setInterval(() => {
  //     const seconds = Math.floor((Date.now() - startTime) / 1000);
  //     elapsedTime = `${seconds}s`;
  //   }, 1000);
  // }

  // function stopTimer() {
  //   clearInterval(timerInterval);
  // }

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
    accumulatedTime += Date.now() - startTime; // add the current session's time
  }

  function resetTimer() {
    clearInterval(timerInterval);
    accumulatedTime = 0;
    elapsedTime = '0s';
  }

  function paramsToCrawling() {
    acceptingParams = false;
    crawling = true;
  }

  function crawlingToResults() {
    crawling = false;
    displayingResults = true;
  }

  function resultsToParams() {
    displayingResults = false;
    acceptingParams = true;
    crawlResult = [];
  }

  function pauseToResumeButton(){
    pauseAvailable = false;
    resumeAvailable = true;
  }

  function resumeToPauseButton(){
    resumeAvailable = false;
    pauseAvailable = true;
  }

  //instead of hard coded values in dict, dynamically add items to dictionary
  function dynamicCrawlerParamUpdate(id, value) {
    crawlerParams[id] = value;
  }

  async function stopCrawler() {
    if (activeController) {
      activeController.abort();
    }
    const response = await fetch('http://localhost:8000/stop_crawler', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      console.log("Stopped successfully");
    } else {
      console.error("Error stopping crawler:", response.statusText);
    }
  }

  async function pauseCrawler(){
    pauseToResumeButton();
    stopTimer();
    const response = await fetch('http://localhost:8000/pause_crawler', { //This is where the params are being sent
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      console.log("Paused successfully");
    } else {
      console.error("Error pausing crawler:", response.statusText);
    }
  }

  async function resumeCrawler(){
    resumeToPauseButton();
    startTimer();
    const response = await fetch('http://localhost:8000/resume_crawler', { //This is where the params are being sent
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      console.log("resumed successfully");
    } else {
      console.error("Error resuming crawler:", response.statusText);
    }
  }

  // Validate input parameters before starting crawl
  function validateParams() {
    let isValid = true;

    // Reset error messages
    Object.keys(errorMessages).forEach(key => {
      errorMessages[key] = "";
    });

    if (!crawlerParams.url) {
      errorMessages.url = "URL is required!";
      isValid = false;
    }

    if (crawlerParams.max_pages && parseInt(crawlerParams.max_pages) < 0) {
      errorMessages.max_pages = "Max Pages cannot be a negative number!";
      isValid = false;
    }

    if (crawlerParams.depth && parseInt(crawlerParams.depth) < 0) {
      errorMessages.depth = "Crawl Depth cannot be a negative number!";
      isValid = false;
    }

    if (crawlerParams.delay && parseInt(crawlerParams.delay) < 0) {
      errorMessages.delay = "Request Delay cannot be a negative number!";
      isValid = false;
    }

    return isValid;
  }

  // This is for inputs to be sent to the backend for computation.
  async function handleSubmit() {
    resetTimer();
    // Validate the input before proceeding
    if (!validateParams()) {
      return; // Do not proceed if validation fails
    }

    // This try catch is to validate whether the URL is valid or not
    try {
      const validateURL = await fetch('http://localhost:8000/validate_url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: crawlerParams.url })
      });

      const validationResponse = await validateURL.json();

      // if the URL is not valid, show an error message
      if (!validateURL.ok || !validationResponse.valid) {
        alert(`URL validation failed: ${validationResponse.message || 'Unknown error'}`);
        return;
      }
    }
    catch (error) {
      alert(`An error occurred during URL validation: ${error.message}`);
      console.error('Error during URL validation:', error);
      return;
    }


    paramsToCrawling();
    startTimer();
    crawledPages = 0;
    totalPages = crawlerParams.max_pages || 0;
    activeController = new AbortController();

    const response = await fetch('http://localhost:8000/crawler', { //This is where the params are being sent
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(crawlerParams),
      signal: activeController.signal
    });

    if (response.ok) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        try {
          if (activeController.signal.aborted) {
            break;
          }
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            const updates = chunk.split('\n').filter(Boolean).map(JSON.parse);
            crawlResult = [...crawlResult, ...updates];
            crawledPages += updates.length; // Update progress

            processedRequests += updates.length;
            filteredRequests = crawlResult.filter((item) => !item.error).length;
            requestsPerSecond = (processedRequests / ((Date.now() - startTime) / 1000)).toFixed(2);
          }
        } catch (err) {
          if (err.name === 'AbortError') {
            done = true;
            console.log("real-time results stopped to end crawl");
          }
          else {
            console.error('Error: ', err);
          }
        }
      }

      crawlingToResults();
    } else {
      console.error("Error starting crawler:", response.statusText);
    }
    stopTimer();
  }

  // Sorting function
  function sortTable(column) {
    const { direction } = sortConfig;

    // Toggle sorting direction
    sortConfig.direction = direction === 'asc' ? 'desc' : 'asc';
    sortConfig.column = column;

    console.log(`Sorting by column: ${column}, direction: ${sortConfig.direction}`);

    crawlResult = [...crawlResult].sort((a, b) => {
        const aValue = a[column];
        const bValue = b[column];

        // Ensure we are working with numbers where appropriate
        const aValueParsed = typeof aValue === 'number' ? aValue : parseFloat(aValue);
        const bValueParsed = typeof bValue === 'number' ? bValue : parseFloat(bValue);

        console.log(`Comparing ${a[column]} with ${b[column]}`);

        if (aValueParsed < bValueParsed) {
            return sortConfig.direction === 'asc' ? -1 : 1;
        } else if (aValueParsed > bValueParsed) {
            return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
    });
    console.log("Sorted Result: ", crawlResult);
}

function exportToCSV(data) {
  let filename = crawlerParams['url'];
  filename = urlToFilename(filename);
  
  // convert json to array of dicts
  const dataArray = Object.values(data);
  
  //Sets up label row
  const keys = Object.keys(dataArray[0]);
  const headerRow = keys.join(',');
  
  const dataRows = dataArray.map(row => {
    return keys.map(key => {
      // incase of empty info
      if (row[key] === null || row[key] === undefined) {
        return '""';
      } else if (typeof row[key] === 'object') {
        //convert to string
        //.replace(/"/g, '""'): csv quirk: double quotes must be wrapped by another set of double quotes to export
        return `"${JSON.stringify(row[key]).replace(/"/g, '""')}"`;
      } else {
        // Handle strings and numbers
        return `"${String(row[key]).replace(/"/g, '""')}"`;
      }
    }).join(',');
  });
  
  const csvContent = [headerRow, ...dataRows].join('\n');
  
  //creates and downloads csv
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
    .replace(/^https?:\/\//, '')   // remove http:// or https://
    .replace(/[^a-z0-9]/gi, '_')    // replace anything not alphanumeric with _
    .toLowerCase();                 // optional: lowercase for consistency
}


</script>

<div class="crawlerConfigPage">
  <div>
    <h1>Crawler</h1>

    {#if acceptingParams}
    <div>
      <form onsubmit="{(e) => {e.preventDefault(); handleSubmit()}}">
        {#each crawlerInput as param}
        <label>
          <span>{param.label}:</span>
          <input
            type={param.type}
            bind:value={crawlerParams[param.id]}
            placeholder={param.example}
            required={param.required}
            oninput={(e) => dynamicCrawlerParamUpdate(param.id, e.target.value)}
          />
          {#if errorMessages[param.id]}
          <p class="error">{errorMessages[param.id]}</p>
          {/if}
        </label>
        {/each}

        <button type="submit" title="Begins Crawling with the set Parameters">Submit</button>
      </form>
    </div>
    {/if}

    {#if crawling}
    <div class="crawl-section">
      <div>
        <h2>Running...</h2>
        <div class="progress-bar">
          <div
            class="progress"
            style="width: {totalPages > 0 ? (crawledPages / totalPages) * 100 : 0}%"
          ></div>
        </div>
        <p>{crawledPages} / {totalPages || "∞"} pages crawled</p>
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
        
        <div class="results-table">
          {#if crawlResult.length === 0}
          <p>No data received yet. Please wait...</p>
          {/if}
          <div class = "table-container">
            <table>
              <thead>
                <tr>
                  <th onclick={() => sortTable('id')}>ID</th>
                  <th>URL</th>
                  <th>Title</th>
                  <th onclick={() => sortTable('word_count')}>Word Count</th>
                  <th onclick={() => sortTable('char_count')}>Character Count</th>
                  <th onclick={() => sortTable('link_count')}>Links</th>
                  <th>Error</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {#each crawlResult as crawledURL, index (crawledURL.id)}  
                <tr>
                  <td>{crawledURL.id}</td>
                  <td>{crawledURL.url}</td>
                  <td>{crawledURL.title}</td>
                  <td>{crawledURL.word_count}</td>
                  <td>{crawledURL.char_count}</td>
                  <td>{crawledURL.link_count}</td>
                  <td>{crawledURL.error ? 'True' : 'False'}</td>
                  <td>{crawledURL.severity}</td>
                </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <button onclick={(e) => {preventDefault(e); stopCrawler()}} title="Completely Stops Crawling of the website">Stop Crawl</button>
          {#if pauseAvailable == true}
          <button onclick={(e) => {preventDefault(e); pauseCrawler()}} title="Temporarily Stops Crawling of the website">Pause Crawl</button>
          {/if}
          {#if resumeAvailable == true}
          <button onclick={(e) => {preventDefault(e); resumeCrawler()}} title ="Resumes Crawling of the Webstie">Resume Crawl</button>
          {/if}
        </div>
      </div>
    </div>
    {/if}

    {#if displayingResults}
    <div class="crawl-section">
      <h2>Crawl Results</h2>
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

      <div class="results-table">
        <div class="table-container"> 
          <table>
            <thead>
              <tr>
                <th onclick={() => sortTable('id')}>ID 
                  {#if sortConfig.column === 'id'}
                    {sortConfig.direction === 'asc' ? '▲' : '▼'}
                  {/if}
                </th>
              
                <th>URL</th>
              
                <th>Title</th>
              
                <th onclick={() => sortTable('word_count')}>Word Count 
                  {#if sortConfig.column === 'word_count'}
                    {sortConfig.direction === 'asc' ? '▲' : '▼'}
                  {/if}
                </th>
              
                <th onclick={() => sortTable('char_count')}>Character Count 
                  {#if sortConfig.column === 'char_count'}
                    {sortConfig.direction === 'asc' ? '▲' : '▼'}
                  {/if}
                </th>
              
                <th onclick={() => sortTable('link_count')}>Links 
                  {#if sortConfig.column === 'link_count'}
                    {sortConfig.direction === 'asc' ? '▲' : '▼'}
                  {/if}
                </th>
              
                <th>Error</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {#each crawlResult as crawledURL, index (crawledURL.id)}  
              <tr>
                <td>{crawledURL.id}</td>
                <td>{crawledURL.url}</td>
                <td>{crawledURL.title}</td>
                <td>{crawledURL.word_count}</td>
                <td>{crawledURL.char_count}</td>
                <td>{crawledURL.link_count}</td>
                <td>{crawledURL.error ? 'True' : 'False'}</td>
                <td>{crawledURL.severity}</td>
              </tr>
              {/each}
            </tbody>
          </table>
        </div>
        <button onclick={(e) => { resultsToParams() }} title = "Navigates back to the Crawler Parameter page">Restart</button>
        <button onclick={(e) => {preventDefault(e); console.log(crawlerParams['url']); exportToCSV(crawlResult)}} title="Exports the results of the Crawling">Export</button>
      </div>
    </div>
    {/if}
  </div>
</div>

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

  .table-container {
    max-height: 300px;
    overflow-x: auto;
    overflow-y: auto;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    background-color: #1f1f1f;
    width: 100%; /* Ensures the table conainter stays at a fixed width*/
    box-sizing: border-box; /* Ensures padding is included in the width */
  }

  .table-container table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed /* Prevents the columns from adjusting dynamically*/
  }

  .table-container th, .table-container td {
    padding: 8px;
    text-align: left;
    border-bottom: 1px solid #ccc;
    white-space: nowrap; /* Prevents text from wrapping */
    overflow: hidden; /* Hides overflow text */
    text-overflow: ellipsis; /* Adds ellipsis for overflow text */
  }

  .results-table {
    margin-top: 20px; 
  }

  .results-table button {
    margin-top: 20px;
    margin-right: 10px;
    padding: 5px 10px;
    font-size: 1rem;
    width: auto;
    min-width: 80px;
  }

  .crawl-section {
    background-color: #1f1f1f;
    padding: 1.5rem;
    border-radius: 1rem;
    margin-top: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }

  .crawl-section button {
    margin-top: 20px;
    margin-right: 10px;
    padding: 5px 10px;
    font-size: 1rem;
    width: auto;
    min-width: 80px;
  }

  .error {
    color: red;
    font-size: 0.8rem;
  }

  input{
    color: white;
  }
  input:focus {
    color: white;
  }

  input::placeholder {
    color: #aaa; 
  }
</style>
