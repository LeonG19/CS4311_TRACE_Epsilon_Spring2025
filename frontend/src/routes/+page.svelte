<script>
  import { goto } from '$app/navigation'; // Import the goto function for navigation

  let initials = '';
  let name = '';
  let errorMessage = null;

  async function handleStart() {
      try{
          const response = await fetch(`http://169.254.7.176:5173/analyst/${initials}/`,{
              method: 'POST'
          });
          const data= await response.json();
          if (data['status']==='success'){
              sessionStorage.setItem('analyst_initials', initials);
              goto('/main');
          }else{
              initials='';
              name = ''
              throw new Error(`Failed to check analyst`);
          }
      } catch (err){
          errorMessage= err.message + ': ERROR';
          console.error('Fetch error:', err);
      }
  }

  async function handleInitCreation(type) {
    try {
      const verification = await fetch(`http://169.254.7.176:5173/analyst/${initials}/`,{
         method: 'POST'
      });

      const data= await verification.json();

      if (data['status']==='success'){
          initials='';
          name='';
          throw new Error('Initials are already in use, Plese enter a new set of initials');
      }  

      const response = await fetch(`http://169.254.7.176:5173/create_initials/${initials}/${type}/${name}`,{
          method: 'POST',
      });

      if (response.ok) {
          handleStart(); //Handle login after creating analyst
      } else {
          const data = await response.json();
          throw new Error( data.error || 'Failed to create analyst');
      }
      
    } catch (err) {
        errorMessage= err.message + ': ERROR';
        console.error('Fetch error:', err);
    }
  }
</script>

<style>

  /* Full-screen landing page with dark gray background */
  .landing-section {
    position: relative;
    height: 100vh;
    width: 100%;
    background-color: #1e1e1e;
    color: #ffffff;
    display: flex;
    flex-direction: column;
  }

  header {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 1rem;
    background: #fff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  header nav a {
    font-size: 1.125rem;
    margin: 0 0.75rem;
    text-decoration: none;
    color: #4b5563;
  }
  header nav a:hover {
    text-decoration: underline;
  }

  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0 1rem;
    text-align: center;
  }

  h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }
  .subtitle {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    max-width: 700px;
  }

  .register-sub{
    font-size: 1rem;
    margin-top: 2rem;
  }

  .error {
    color: #b91c1c;
    font-weight: bold;
    font-size: 1rem;
    padding: 0.5rem;
    border: 1px solid #b91c1c;
    border-radius: 4px;
    margin-bottom: 1rem;
    width: 80%;
    text-align: center;
  }

  /*grey box*/
  .welcome-box {
    width: 450px;
    height: 400px;
    /*display: flex;*/
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 2rem;
    background-color:#2a2a2a;
    border-radius: 8px;
    box-sizing: border-box;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-top: -30px; /* Moves the box upward slightly */
    text-align: center;
  }

  .welcome-box input {
    font-size: 1rem;
    padding: 0.5rem;
    width: 60%;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-bottom: 1rem;
    text-align: center;
  }

  .welcome-box button {
    font-size: 1rem;
    padding: 1rem;
    width: 60%;
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .welcome-box button:hover {
    background-color: #2563eb;
  }

  .register-button{
    background-color: #555555 !important;
    width: 45% !important;
    display:inline-block !important;
  }

  .register-button:hover{
    background-color: #4A4A4A !important;
  }
</style>

<!-- Landing Page -->
<div class="landing-section">

  <!-- Main Content -->
  <main>
    <h1>TRACE</h1>
    <p class="subtitle">
      A Cybersecurity Platform to Protect Your Digital Assets. Detect Vulnerabilities, Strengthen Defense, and Secure Your Network Seamlessly.
      Gain Real-Time Insights and Proactive Protection.
    </p>

    {#if errorMessage}
      <p class="error">{errorMessage}</p>
    {/if}

    <!-- Welcome Box with initials input and Start button -->
    <div class="welcome-box">
      <input
        type="text"
        placeholder="Enter your initials"
        bind:value={initials}
      />
      <input
        type="text"
        placeholder="Enter your name"
        bind:value={name}
      />
      <button on:click={handleStart}>START</button>

      <!--  Button to register new initials to the database, they will be registered as a normal analyst -->
      <p class="register-sub">Don't have your initials registered?</p>
      <button class="register-button" on:click={handleInitCreation(0)}>Register Analyst Initials</button>
      <button class="register-button" on:click={handleInitCreation(1)}>Register Lead Initials</button>
    </div>
  </main>
</div>