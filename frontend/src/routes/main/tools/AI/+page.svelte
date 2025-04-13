<script>
  
  let wordlistInput = { id: "wordlist", type: "file", accept: ".json, .txt", label: "Word List", value: "", example: "Ex: wordlist.txt", required: true }

  let usernameInput = [
    { id: "userChar", type: "checkbox", label: "Characters", isChecked: true},
    { id: "userNum", type: "checkbox", label: "Numbers", isChecked: true},
    { id: "userSymb", type: "checkbox", label: "Symbols", isChecked: true}
  ];

  let passwordInput = [
    { id: "passChar", type: "checkbox", label: "Characters", isChecked: true},
    { id: "passChar", type: "checkbox", label: "Numbers", isChecked: true},
    { id: "passSymb", type: "checkbox", label: "Symbols", isChecked: true}
  ]

  let usernameLenInput = { id: "userLen", type: "number", label: "Length", value: "", example: "Ex: 12", required: true }
  let passwordLenInput = { id: "passLen", type: "number", label: "Length", value: "", example: "Ex: 12", required: true }

  let aiParams = {
    wordlist : ""
  }

  let aiResult = []

  let acceptingParams = true;
  let generating = false;
  let displayingResults = false;

  function paramsToGenerate(){
    acceptingParams = false;
    generating = true;
  }

  function generatingToResults(){
    generating = false;
    displayingResults = true;
  }

  function resultsToParams(){
    displayingResults = false;
    acceptingParams = true;
  }

  function dynamicAiParamUpdate(id, value) {
  }

  // This is for inputs to be sent to the backend for computation.
  async function handleSubmit() {
    console.log("Form Submitted");
  }

  async function handleFile() {
    console.log("File Submitted");
  }
</script>
  
  <div class="aiConfigPage">
    <div>
      <h1>AI Generator</h1>
      {#if acceptingParams}
        <div>
            <form onsubmit= "{(e) => {e.preventDefault(); handleSubmit(); paramsToGenerate()}}">

                {wordlistInput.label}
                <input accept=wordlistInput.accept type={wordlistInput.type} bind:value={wordlistInput.id} placeholder={wordlistInput.example} requirement={wordlistInput.required} oninput={(e) => {dynamicAiParamUpdate(wordlistInput.id, e.target.value); handleFile()}}/>

                <div class="input-container">
                  <div class="column">
                  <label>Username</label>
                  {#each usernameInput as param}
                      <label>
                          {param.label}:
                          <input type="checkbox" bind:checked={param.isChecked} oninput={(e) => dynamicAiParamUpdate(param.id, e.target.value)} />
                      </label>
                  {/each}

                  <label>
                    {usernameLenInput.label}:
                    <input type={usernameLenInput.type} bind:value={usernameLenInput[usernameLenInput.id]} placeholder={usernameLenInput.example} requirement={usernameLenInput.required} oninput={(e) => dynamicAiParamUpdate(usernameLenInput.id, e.target.value)}/>
                  </label>

                  </div>

                  <div class="column">
                  <label>Password</label>
                  {#each passwordInput as param}
                      <label>
                          {param.label}:
                          <input type="checkbox" bind:checked={param.isChecked} oninput={(e) => dynamicAiParamUpdate(param.id, e.target.value)} />
                      </label>
                  {/each}

                  <label>
                    {passwordLenInput.label}:
                    <input type={passwordLenInput.type} bind:value={passwordLenInput[passwordLenInput.id]} placeholder={passwordLenInput.example} requirement={passwordLenInput.required} oninput={(e) => dynamicAiParamUpdate(passwordLenInput.id, e.target.value)}/>
                  </label>

                  </div>
                </div>

            <button type="submit">Submit</button>
          </form>
        </div>
      {/if}

      {#if generating}
        <div>
          <h2>Generating Credentials...</h2>
        </div>
      {/if}

      {#if displayingResults}
        <h2>AI Credential Generator Results</h2>
        <div>
          <button onclick={(e) => { resultsToParams()}}>Back to Param Setup</button>
        </div>
      {/if}

    </div>
  </div>
    
  <style>
    form {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 10px;
      width: 400px;
      margin: 50px auto;
      padding: 20px;
      border: 1px solid #ccc;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .input-container {
    display: flex;
    gap: 20px; /* Adjust spacing between columns */
    justify-content: space-between; /* Distributes columns evenly */
    }

    .column {
        display: flex;
        flex-direction: column;
        gap: 10px; /* Adjusts spacing between elements */
        width: 48%; /* Ensures equal width */
    }
  
    label {
      width: 100%;
      display: flex;
      flex-direction: column;
      font-weight: bold;
    }
    
    .input-label {
    display: flex;
    align-items: center;
    gap: 10px; /* Adjust spacing between label and input */
    }

    .row {
      display: flex;
      flex-direction: row;
      margin: 10px;
      padding: 5px;
      border-bottom: 1px solid #ccc;
    }

    .row span {
      margin-right: 15px;
    }

  </style>