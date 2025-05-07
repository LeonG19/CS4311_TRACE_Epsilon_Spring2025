<script>
  import {onMount} from 'svelte';
	import { preventDefault } from 'svelte/legacy';
  let typeOfTool
  let choosingScan = true
  let displayingResultsOfSelectedScan = false
  let scansInProject = []
  let specificScanResults = []

  function choosingScanToDisplayingResults(){
  choosingScan = false
  displayingResultsOfSelectedScan = true
  }

  function returnToScanTable(){
  choosingScan = true
  displayingResultsOfSelectedScan = false
  }

  async function handleRowClick(run_id){
    const response = await fetch(`http://localhost:8000/getScanResults/${run_id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    specificScanResults = await response.json();
    console.log(specificScanResults)
    choosingScanToDisplayingResults();
  }

  onMount(async () => {
    typeOfTool = sessionStorage.getItem("prev_results_type");
    console.log(typeOfTool)
    try{
      const response = await fetch(`http://localhost:8000/getScan/${sessionStorage.getItem('name')}/${typeOfTool}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      scansInProject = await response.json()
    } catch (error) {
      alert(`An error occurred during retreival of scans: ${error.message}`);
      console.error('Error during retreival of scans:', error);
      return;
    }
  });

</script>
<div>
  <h1 class="center-wrapper" style="color: white">Previous {typeOfTool} Results</h1>
  <div>
      {#if choosingScan}
      <div class="table-container">
        <table>
          <tbody>
              {#each scansInProject as scan, i}
                <tr on:click={(e) => {preventDefault(e); handleRowClick(scan.run_id)}}>
                  <td>{typeOfTool} {i}</td>
                </tr>
              {/each}
            
          </tbody>
        </table>
      </div>
      {/if}
  </div>
  <div>
    {#if displayingResultsOfSelectedScan}
      <div class = "table-container">
        <table>
          <tbody>
            {#if typeOfTool == "crawler"}
              {#each specificScanResults as scanResult, index}
                <tr>
                  <td>{index}</td>
                  <td>{scanResult.url}</td>
                  <td>{scanResult.title}</td>
                  <td>{scanResult.word_count}</td>
                  <td>{scanResult.char_count}</td>
                  <td>{scanResult.link_count}</td>
                  <td>{scanResult.error ? 'True' : 'False'}</td>
                  <td>{scanResult.severity}</td>
                </tr>
              {/each}
            {/if}
            {#if typeOfTool == "fuzzer"}
              {#each specificScanResults as scanResult, index}
                  <tr>
                    <td>{index}</td>
                    <td>{scanResult.response}</td>
                    <td>{scanResult.lines}</td>
                    <td>{scanResult.words}</td>
                    <td>{scanResult.chars}</td>
                    <td>{scanResult.payload}</td>
                    <td>{scanResult.length}</td>
                    <td>{scanResult.error ? 'Yes' : 'No'}</td>
                  </tr>
                {/each}
            {/if}
            {#if typeOfTool == "bruteforcer"}
              {#each specificScanResults as scanResult, index} <!-- Key by result.id -->
                <tr>
                  <td>{index}</td> <!-- Display result.id instead of index + 1 -->
                  <td>{scanResult.response}</td>
                  <td>{scanResult.lines}</td>
                  <td>{scanResult.words}</td>
                  <td>{scanResult.chars}</td>
                  <td>{scanResult.payload}</td>
                  <td>{scanResult.length}</td>
                </tr>
              {/each}
            {/if}
            {#if typeOfTool == "AI"}
              {#each specificScanResults as scanResult, index}
                <tr>
                  <td>{scanResult.Username}</td>
                  <td>{scanResult.Password}</td>
                </tr>
              {/each}
            {/if}
            {#if typeOfTool == "sqli"}
            {#each specificScanResults as scanResult, index}
              <tr>
                <td>{index}</td>
                <td>{scanResult.target}</td>
                <td>{scanResult.port}</td>
                <td>{scanResult.timeout}</td>
                <td>{scanResult.headers}</td>
                <td>{scanResult.payload}</td>
                <td>{scanResult.status_code}</td>
                <td>{scanResult.snippet}</td>
                <td>{scanResult.vulnerable}</td>
                <td>{scanResult.vulnerable}</td>
              </tr>
            {/each}
          {/if}
          </tbody>
        </table>
      </div>
      <button on:click={(e) => {preventDefault(e); returnToScanTable()}}>Return To Scans</button>
    {/if}
  </div>
</div>

<style>
  .center-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
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
    color: white;
    margin: 0 auto; /* Center horizontally */
    align-items: center;
  }

  .table-container table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed /* Prevents the columns from adjusting dynamically*/
  }

  .table-container td {
    padding: 8px;
    text-align: center;
    border-bottom: 1px solid #ccc;
    white-space: nowrap; /* Prevents text from wrapping */
    overflow: hidden; /* Hides overflow text */
    text-overflow: ellipsis; /* Adds ellipsis for overflow text */
  }
</style>