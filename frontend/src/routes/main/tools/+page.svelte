<script>

    function gotoCrawler() {
      window.location.href = "/main/tools/Crawler";
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

    function gotoHttpTester() {
      window.location.href = "/main/tools/HttpTester";
    }

    </script>
    <nav>
      <div class="toolsConfigPage">
        <h1 style="color: white;"> Tools </h1>
        <div class="row">
          <div><span> Crawler </span></div>
          <div><button on:click={gotoCrawler} title="Navigates to the Crawler page">Select</button></div>
        </div>

        <div class="row">
          <div><span> Fuzzer </span></div>
          <div><button on:click={gotoFuzzer} title="Navigates to the Fuzzer page">Select</button></div>
        </div>

        <div class="row">
          <div><span> Brute Forcer </span></div>
          <div><button on:click={gotoBruteForcer}>Select</button></div>
        </div>

        <div class="row">
          <div><span> AI Credential Generator </span></div>
          <div><button on:click={gotoAI} title="Navigates to the AI Credential Generastor page">Select</button></div>
        </div>

        <div class="row">
          <div><span> HTTP Tester </span></div>
          <div><button on:click={gotoHttpTester} title="Navigates to the HTTP Tester page">Select</button></div>
        </div>
      </div>
    </nav>