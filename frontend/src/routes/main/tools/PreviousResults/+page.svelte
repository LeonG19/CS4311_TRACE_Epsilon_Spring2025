<script>
  import {onMount} from 'svelte';
  let typeOfTool
  let choosingScan = true
  let displayingResultsOfSelectedScan = false
  let scansInProject = []

  function choosingScanToDisplayingResults(){
  let choosingScan = false
  let displayingResultsOfSelectedScan = true
  }

  function handleRowClick(run_id){
    console.log(run_id)
  }

  onMount(async () => {
    typeOfTool = sessionStorage.getItem("prev_results_type");
    console.log(typeOfTool);
    console.log(sessionStorage.getItem("name"));
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
  <h1 class="center-wrapper">Previous {typeOfTool} Results</h1>
  <div class="table-container">
    <table>
      <tbody>
        {#each scansInProject as scan, i}
          <tr on:click={() => handleRowClick(scan.run_id)}>
            <td>{typeOfTool} {i}</td>
          </tr>
        {/each}
      </tbody>
    </table>
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