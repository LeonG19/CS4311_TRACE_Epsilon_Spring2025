<script>

  import { preventDefault } from "svelte/legacy";

  import { onDestroy } from 'svelte';

let time = 0; // time in milliseconds
let displayTime = '0.00';
let finalTime = '0.00';
let interval;

function startTimer() {
  time = 0;
  clearInterval(interval);
  interval = setInterval(() => {
    time += 10;
    displayTime = (time / 1000).toFixed(2);
  }, 10);
}

function stopTimer() {
  clearInterval(interval);
}

$: if (generating) {
  startTimer();
} else {
  stopTimer();
}

$: if (displayingResults) {
  finalTime = displayTime;
} else {
}

onDestroy(() => {
  clearInterval(interval);
});

  import {onMount} from "svelte";
  let err = ""
  let wordlistInput = { id: "wordlist", type: "file", accept: ".txt", label: "Word List", value: "", example: "Ex: wordlist.txt", required: true }

  let usernameInput = [
    { id: "userChar", type: "checkbox", label: "Characters", isChecked: true},
    { id: "userNum", type: "checkbox", label: "Numbers", isChecked: true},
    { id: "userSymb", type: "checkbox", label: "Symbols", isChecked: true}
  ];

  let passwordInput = [
    { id: "passChar", type: "checkbox", label: "Characters", isChecked: true},
    { id: "passNum", type: "checkbox", label: "Numbers", isChecked: true},
    { id: "passSymb", type: "checkbox", label: "Symbols", isChecked: true}
  ]

  let usernameLenInput = { id: "userLen", type: "number", label: "Length", value: "", example: "Ex: 12", required: true }
  let passwordLenInput = { id: "passLen", type: "number", label: "Length", value: "", example: "Ex: 12", required: true }

  let usernameNumInput = { id: "userNum2", type: "number", label: "Username Amount", value: "", example: "Ex: 25", required: true }
  let passwordNumInput = { id: "passNum2", type: "number", label: "Password Amount", value: "", example: "Ex: 25", required: true }
  let projectName
  let wordlist;
  let uDict ={};
  onMount(async()=>{
    projectName= sessionStorage.getItem('name');
    aiParams["projectName"] = projectName
    console.log("Project Name:", projectName);
  })

  let aiParams = {
    wordlist : "",
  }

  let abortController = null;

  for(let i = 0; i < usernameInput.length;i++){
    aiParams[usernameInput[i].id] = usernameInput[i].isChecked;
  }
  console.log("Populated aiParams with Username checkbox...");

  for(let i = 0; i < passwordInput.length;i++){
    aiParams[passwordInput[i].id] = passwordInput[i].isChecked;
  }
  console.log("Populated aiParams with Password checkbox...");

  let aiResult = [];

  let acceptingParams = true;
  let generating = false;
  let displayingResults = false;
  let showWordlists = false;

  function paramsToGenerate(){
    acceptingParams = false;
    generating = true;
  }

  function paramsToWordlist(){
    acceptingParams = false;
    showWordlists = true;
  }

  function wordlistToParams(){
    acceptingParams = true;
    showWordlists = false;
  }

  function generatingToResults(){
    generating = false;
    displayingResults = true;
  }

  function resultsToParams(){
    displayingResults = false;
    acceptingParams = true;
  }

  function generatingToParams(){
    generating = false;
    acceptingParams = true;
  }

  function regenerateCredentials(){
    displayingResults = false;
    generating = true;

    aiResult = [];

    console.log("Removed previous wordlist results", aiResult)

    handleSubmit();
  }



  function saveWordlist(){
    let textContent = "Username,Password\n";
    textContent += aiResult[0].credentials.map(([username, password]) => `${username},${password}`).join("\n");

    // Create a Blob and Object URL
    const blob = new Blob([textContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    // Create a temporary download link
    const a = document.createElement("a");
    a.href = url;
    a.download = "GeneratedWordlist.txt"; // Default file name
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Cleanup
    URL.revokeObjectURL(url);
  }

  function dynamicAiParamUpdate(id, value) {
    aiParams[id] = value;
    console.log(`Updated ${id}: ${value}`);
  }

  async function handleDelete(file){
    console.log(file)
    try {
      const response = await fetch(("http://localhost:8000/delete_AI/"+file), {
        method: "GET"
      });

      if(response.ok){
        console.log("Delete Successful")
      }

    } catch (error) {
      console.error("Error fetching user list:", error);
    }
  }

  async function stopAI() {
  try {
    const response = await fetch("http://localhost:8000/stop_AI", {
      method: "POST"
    });

    if (response.ok) {
      console.log("AI generation stopped.");
    } else {
      console.error("Failed to stop AI generation:", response.statusText);
    }
  } catch (error) {
    console.error("Error during stopAI request:", error);
  } finally {
    generatingToParams(); // Transition UI back to param input
  }
}

  // Checks that the file is exclusively txt file and updates our file accordingly
  async function handleFile(event) {
    const selectedFile = event.target.files[0];

    if (selectedFile && selectedFile.type === "text/plain") {
      wordlist = selectedFile;

      // Update param after file validation
      dynamicAiParamUpdate(wordlistInput.id, selectedFile);
      console.log("Valid file selected:", wordlist.name);

    } else {
      alert("Please select a valid .txt file");
      event.target.value = ""; // Reset input
      wordlist = null;
    }
  }

  function handleStop() {
    console.log("Stop Generation Not implemented")
    //if (abortController) {
    //  abortController.abort();
    //}
}

  async function fetchUserList() {
    try {
      const response = await fetch(("http://localhost:8000/ai_results/" + projectName), {
        method: "GET",
      });
      const data = await response.json();

      uDict = data
      

      console.log("Retrieved wordlist: ", uDict)
    } catch (error) {
      console.error("Error fetching user list:", error);
    }
  }

  // This is for inputs to be sent to the backend for computation.
  async function handleSubmit() {
    console.log("Form Submitted", aiResult);

    const formData = new FormData();

    if(wordlist) {
      formData.append("file", wordlist);
    }

    formData.append("data", JSON.stringify(aiParams));

    try{
      const response = await fetch('http://localhost:8000/generate-credentials', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        console.log("Generating...")
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;

        while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const updates = chunk.split('\n').filter(Boolean).map(JSON.parse);
          aiResult = [...aiResult, ...updates];

          console.log("Processed Credentials...", aiResult[0].credentials);
          }
        }
        generatingToResults();
      } else {
        console.error("Error starting generate:", response.statusText);
      }
    } catch (error) {
        console.error("Request failed:", error);
        err = error;
    }
  }

  async function handleSave() {
    let textContent = "Username,Password\n";
    textContent += aiResult[0].credentials.map(([username, password]) => `${username},${password}`).join("\n");

    console.log("Saving File... ");

    const file = new File([textContent], "user_credentials.txt", {type: "text/csv"});

    const formData = new FormData();
    formData.append("file",file);

    try{
      const response = await fetch(("http://localhost:8000/submit_txt_results/AI/"+projectName), {
      method: "POST",
      body: formData
      });

      if (response.ok) {
        console.log("File saved!");
      } else {
        console.error("Error saving file:", response.statusText);
      }
    } catch (error) {
        console.error("Request failed:", error);
        err = error;
    }
}



</script>
  
  <div class="aiConfigPage">
    <div>
      {#if acceptingParams}
        <div style="text-align: center;">
            <h1>AI Generator</h1>
            <form onsubmit= "{(e) => {e.preventDefault(); handleSubmit(); paramsToGenerate()}}">

                {wordlistInput.label}
                <input accept=wordlistInput.accept type={wordlistInput.type} placeholder={wordlistInput.example} requirement={wordlistInput.required} onchange={handleFile}/>
             
                <div class="input-container">
                  <div class="column">
                  <label>Username</label>
                  {#each usernameInput as param} 
                      <label>{param.label}</label> 
                      <label class="toggle-switch">                
                          <input type="checkbox" bind:checked={param.isChecked} onchange={(e) => dynamicAiParamUpdate(param.id, e.target.checked)} />
                          <span class="slider"></span>
                      </label>
                  {/each}

                  <label>
                    {usernameLenInput.label}:
                    <input type={usernameLenInput.type} bind:value={usernameLenInput[usernameLenInput.id]} placeholder={usernameLenInput.example} requirement={usernameLenInput.required} oninput={(e) => dynamicAiParamUpdate(usernameLenInput.id, e.target.value)}/>
                  </label>

                  <label>
                    {usernameNumInput.label}:
                    <input type={usernameNumInput.type} bind:value={usernameNumInput[usernameNumInput.id]} placeholder={usernameNumInput.example} requirement={usernameNumInput.required} oninput={(e) => dynamicAiParamUpdate(usernameNumInput.id, e.target.value)}/>
                  </label>

                  </div>

                  <div class="column">
                  <label>Password</label>
                  {#each passwordInput as param}
                      <label>{param.label}</label> 
                      <label class="toggle-switch">                
                        <input type="checkbox" bind:checked={param.isChecked} onchange={(e) => dynamicAiParamUpdate(param.id, e.target.checked)} />
                      <span class="slider"></span>
                  </label>
                  {/each}

                  <label>
                    {passwordLenInput.label}:
                    <input type={passwordLenInput.type} bind:value={passwordLenInput[passwordLenInput.id]} placeholder={passwordLenInput.example} requirement={passwordLenInput.required} oninput={(e) => dynamicAiParamUpdate(passwordLenInput.id, e.target.value)}/>
                  </label>

                  <label>
                    {passwordNumInput.label}:
                    <input type={passwordNumInput.type} bind:value={passwordNumInput[passwordNumInput.id]} placeholder={passwordNumInput.example} requirement={passwordNumInput.required} oninput={(e) => dynamicAiParamUpdate(passwordNumInput.id, e.target.value)}/>
                  </label>

                  </div>
                </div>

            <button type="submit">Submit</button>
          </form>
          <button onclick={(e) => {fetchUserList(); paramsToWordlist()}}>Saved Wordlists</button>
        </div>
      {/if}

      {#if generating}
          <form style="width: 600px; height: 300px; text-align: center; border: 2px solid #5f5f5f;">
            <h2>Generating Credentials...</h2>
            <h3 class="text-2xl font-bold">Time (seconds):</h3>
            <h3>{displayTime}</h3>
            <button onclick={(e) => {preventDefault(e); handleStop()}} title="Completely Stops AI generation">Stop Generation</button>
          </form>
          <div class="lds-dual-ring" style="padding-left: 40%;"></div>
      {/if}

      {#if displayingResults}
        <h2>AI Credential Generator Results</h2>
        <h3 style="text-align: center; font-size: medium">Time: {finalTime} Usernames: {aiParams["userNum2"]} Passwords: {aiParams["passNum2"]}</h3>
        <div class="results-table">
        <table>
          <thead>
            <tr>
              <th style="background-color: #007bff;">Username</th>
              <th style="background-color: #007bff;">Password</th>
            </tr>
          </thead>
          <tbody>
            {#each aiResult[0].credentials as [username, password], index}
              <tr>
                <td>{username}</td>
                <td>{password}</td>
              </tr>
            {/each}
          </tbody>
        </table>
        <button onclick={(e) => {resultsToParams()}}>Back to Param Setup</button>
        <button onclick={(e) => {regenerateCredentials()}}>Regenerate</button>
        <button onclick={(e) => {handleSave()}}>Save Wordlist</button>
      </div>
      {/if}

      {#if showWordlists}
        <h2>AI Credential Generator Results</h2>
        <div class="results-table">
        <table>
          <thead>
            <tr>
              <th style="background-color: #007bff;">Filename</th>
              <th style="background-color: #007bff;">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.entries(uDict) as [filename, value]}
              <tr>
                <td>{filename}</td>
                <td><button id={filename} style="background-color:red; border-radius:10px" onclick={(e) => {handleDelete(value);wordlistToParams()}}>Delete</button></td>
              </tr>
            {/each}
          </tbody>
        </table>
        <button onclick={(e) => {wordlistToParams()}}>Back to Param Setup</button>
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
      width: 100%;
    display: flex;
    gap: 20px; /* Adjust spacing between columns */
    justify-content: space-between; /* Distributes columns evenly */
    }

    .column {
      padding-top: 10px;
      border: 1px solid #5f5f5f;
      border-radius: 10px;
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

    .toggle-switch {
        margin-top: -25px;
        align-self: center;
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
    }

    /* Hide default checkbox */
    .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    /* The track */
    .slider {
        position: absolute;
        cursor: pointer;
        background-color: #ccc;
        border-radius: 24px;
        width: 100%;
        height: 100%;
        transition: background-color 0.3s;
    }

    /* The circular slider */
    .slider::before {
        content: "";
        position: absolute;
        height: 20px;
        width: 20px;
        left: 4px;
        bottom: 2px;
        background-color: white;
        border-radius: 50%;
        transition: transform 0.3s;
    }

    /* Toggled state */
    .toggle-switch input:checked+.slider {
        background-color: #007bff;
    }

    .toggle-switch input:checked+.slider::before {
        transform: translateX(26px);
    }

    
    .lds-dual-ring,
    .lds-dual-ring:after {
      box-sizing: border-box;
    }
    .lds-dual-ring {
      display: inline-block;
      width: 80px;
      height: 80px;
    }
    .lds-dual-ring:after {
      content: " ";
      display: block;
      width: 64px;
      height: 64px;
      margin: 8px;
      border-radius: 50%;
      border: 6.4px solid currentColor;
      border-color: #646cff transparent #646cff transparent;
      animation: lds-dual-ring 1.2s linear infinite;
    }
    @keyframes lds-dual-ring {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }


  </style>