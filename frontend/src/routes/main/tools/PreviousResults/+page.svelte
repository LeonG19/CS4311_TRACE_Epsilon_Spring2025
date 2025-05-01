<script>
  import {onMount} from 'svelte';
  let typeOfTool

  onMount(async () => {
    typeOfTool = sessionStorage.getItem("prev_results_type")
    console.log(typeOfTool)

  });

</script>
<div>
    <h1>Hello {typeOfTool}</h1>
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