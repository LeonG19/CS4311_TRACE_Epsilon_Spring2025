<div class = "container">
    <nav class = "sidebar">

        <div class="TraceLogo">
            <a href="/main" title="Naviagtes back to Project Management page" on:click|preventDefault= {confirmNavigation}>
                <i class ="fas fa-code-branch"></i>
            </a>
        </div>


        <div class="button-group">

            <a href ="/main/tools" title="Navigates back to the Tools Page">
                <button class="barButtons">
                    <i class="fas fa-wrench"></i>
                </button>
            </a>

            <button class="barButtons" title="Navigates to the Tree Graph Page">
                <i class="fas fa-tree"></i>
            </button>

            <button class="barButtons" title="Naviagtes to the Results Page">
                <i class="fas fa-check"></i>
            </button>

            <a href ="/main/tools/AI" title="Navigates to the AI Credential Generator Page">
                <button class="barButtons" >
                    <i class="fas fa-brain"></i>
                </button>
            </a>
        </div>

        <a href ="/main/settings" title="Navigates to the Settings Page">
            <button class="barButtons settings" >
                <i class="fas fa-cog"></i>
            </button>
        </a>
        

    </nav>
    <div class = "main-content">
        <slot></slot>
    </div>
</div>

<script>
    function confirmNavigation(event) {
        const confirm = window.confirm("Are you sure you want to leave this page?");
        if (confirm) {
            window.location.href = "/main"
        }
    }
</script>

<style>
    .container {
        display: flex;
        height: 100vh;
        overflow: auto;
    }
    .sidebar {
        width: 80px;
        background-color: #1f1f1f;
        color: #646cff;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* Space between buttons */
        align-items: center;

        position: sticky;
        top: 0; /* Sticks to the top of the viewport */
        height: 100vh; /* Full height of the viewport */
    }

    .TraceLogo {
        margin-bottom: 1rem;
        font-size: 2rem;

    }

    .button-group {
        display: flex;
        flex-direction: column; /* Aligns buttons vertically */
        align-items: center; /* Centers buttons horizontally */
        flex-grow: 1; /* Allows the button group to take up available space */
        justify-content: center; /* Centers buttons vertically */
    }
    .sidebar button {
        display: flex;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        margin-bottom: 1rem;
        background-color: #353535;
        color: white;
        cursor: pointer; /* Shows a default cursor*/
        justify-content: center; /* Centers text inside the button*/
        align-items: center; /* Centers text inside the button*/
    }
    .sidebar button.settings {
        margin-bottom: 0; /* No margin for the last button */
    }
    .sidebar button:hover {
        background-color: #007bff;
    }
    .main-content {
        flex: 1;
        padding: 1rem;
    }
</style>