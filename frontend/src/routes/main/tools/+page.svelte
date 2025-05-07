<script>

    function gotoCrawler() {
      window.location.href = "/main/tools/Crawler";
    }
    function gotoToolResults(toolName){
      sessionStorage.setItem("prev_results_type", toolName)
      window.location.href = "/main/tools/PreviousResults";
    }
    function gotoFuzzer() {
      window.location.href = "/main/tools/Fuzzer";
    }

    function gotoBruteForcer() {
      window.location.href = "/main/tools/BruteForcer";
    }

    function gotoAI() {
      window.location.href = "/main/tools/AI";
    }

    function gotoHTTPTester() {
      window.location.href = "/main/tools/HttpTester";
    }

    function gotosql() {
      window.location.href = "/main/tools/sql";
    }

    function gotoDBEnum() {
      window.location.href = "/main/tools/DBEnumerator";
    }


    
    </script>
    <nav>
      <div class="toolsConfigPage">
        <h1 style="color: white;"> Tools </h1>
        <div class="tm-row">
          <div><span> Crawler </span></div>
          <div><button on:click={gotoCrawler} title="Navigates to the Crawler page">Scan</button></div>
          <div><button on:click={() => gotoToolResults("crawler")} title="Navigates to the Crawler page">Results</button></div>
        </div>

        <div class="tm-row">
          <div><span> Fuzzer </span></div>
          <div><button on:click={gotoFuzzer} title="Navigates to the Fuzzer page">Scan</button></div>        
          <div><button on:click={() => gotoToolResults("fuzzer")} title="Navigates to the Crawler page">Results</button></div>
        </div>

        <div class="tm-row">
          <div><span> Brute Forcer </span></div>
          <div><button on:click={gotoBruteForcer}>Scan</button></div>
          <div><button on:click={() => gotoToolResults("bruteforcer")} title="Navigates to the Crawler page">Results</button></div>
        </div>

        <div class="tm-row">
          <div><span> AI Credential Generator </span></div>
          <div><button on:click={gotoAI} title="Navigates to the AI Credential Generastor page">Scan</button></div>
          <div><button on:click={() => gotoToolResults("AI")} title="Navigates to the Crawler page">Results</button></div>
        </div>

        <div class="tm-row">
          <div><span> HTTPTester </span></div>
          <div><button on:click={gotoHTTPTester} title="Navigates to the HTTP Tester page">Scan</button></div>
        </div>

        <div class="tm-row">
          <div><span> SQL Injector </span></div>
          <div><button on:click={gotosql} title="Navigates to the SQL Injector page">Scan</button></div>
          <div><button on:click={() => gotoToolResults("sqli")} title="Navigates to the SQLi page">Results</button></div>

        </div>
        
        <div class="tm-row">
          <div><span>DB Enumerator</span></div>
          <div><button on:click={gotoDBEnum} title="Navigates to the DB Enumerator page">Scan</button></div>
          <div><button on:click={() => gotoToolResults("DBEnumerator")} title="Navigates to the DB Enumerator page">Results</button></div>
        </div>    
        
      </div>
    </nav>

    <style>
      .tm-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        border-bottom: 1px solid #ccc;
        margin: 10px;
        padding: 5px;
      }
    </style>