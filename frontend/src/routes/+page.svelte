<h1> This is the Welcome screen </h1>

<script>

function gotoMainMenu() {
  window.location.href = "/main";
}

</script>

<nav>

  <button on:click={gotoMainMenu}>Main Menu</button>

</nav>