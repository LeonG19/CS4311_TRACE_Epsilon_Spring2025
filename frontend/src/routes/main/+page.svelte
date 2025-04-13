<h1> This is the Main Menu screen </h1>

<script>

function gotoTools() {
    window.location.href = "/main/tools";
}

function gotoSettings() {
    window.location.href = "/main/settings";
}
    
</script>
    
<nav>

    <button on:click={gotoTools}>Tools</button>

    <button on:click={gotoSettings}>Settings</button>
    
</nav>