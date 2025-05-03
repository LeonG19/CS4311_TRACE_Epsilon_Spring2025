<script>
	import { goto } from '$app/navigation';
  import { page } from '$app/stores';
	import { onMount } from 'svelte';


  onMount(() => {
    // This runs as soon as the component is mounted (after page load)
    if (sessionStorage.getItem('analyst_initials') == '') {
        goto('/');
    }
  });

  // Dynamically determines if the current route is under /main/tools
  $: isToolsPage = $page.url.pathname.startsWith('/main/tools');

  // Sidebar items for the main sidebar
  const mainSidebarItems = [
      { name: 'Project Selection', icon: 'fas fa-clipboard-list', route: '/main/', title: 'Access Project Selection' },
      { name: 'Project Folders', icon: 'fas fa-folder', route: '/main/project-folders/', title: 'Access Project Folders' },
      { name: 'Deleted Projects', icon: 'fas fa-trash', route: '/main/deleted-projects/', title: 'Open Archived projects' }
  ];

  // Sidebar items for the tools sidebar
  const toolsSidebarItems = [
      { name: 'Tools', icon: 'fas fa-wrench', route: '/main/tools', title: 'Navigates back to the Tools Page' },
      { name: 'Tree Graph', icon: 'fas fa-tree', route: '/main/tools/TreeList', title: 'Navigates to the Tree Graph Page' },
      { name: 'AI Credential Generator', icon: 'fas fa-brain', route: '/main/tools/AI', title: 'Navigates to the AI Credential Generator Page' },
      { name: 'DB Enumerator', icon: 'fas fa-database', route: '/main/tools/DBEnumerator', title: 'Navigates to the DB Enumerator Upload Page' } 
  ];

  // Dynamically choose the sidebar items based on the route
  $: sidebarItems = isToolsPage ? toolsSidebarItems : mainSidebarItems;

  // Pop up to confirm if user wishes to leave the tools page.
  function handleLogoClick(event) {
    if (isToolsPage) {
      const confirmed = window.confirm("Are you sure you wish to leave this page?");
      if (confirmed) {
        window.location.href = '/main/'; // Redirect to the main page
      } else {
        event.preventDefault(); // Prevent the default action if the user cancels
      }
    }
  }

  // Pop up to confirm if user wishes to leave the tools page.
  function handleLogOut(event) {
    const confirmed = window.confirm("Are you sure you wish to log out?");
    if (confirmed) {
      sessionStorage.setItem('analyst_initials', '');
      window.location.href = '/'; // Redirect to the main page
    } else {
      event.preventDefault(); // Prevent the default action if the user cancels
    }
  }

</script>

<!-- This is where the containers to hold either the main menu side bar or the tools sidebar is created-->
<div class="SB-container">
  <nav class="sidebar">
      <div class="TraceLogo">
          <a href="/main" title="Navigates back to Project Management page" on:click = {handleLogoClick}>
              <i class="fas fa-code-branch"></i>
          </a>
      </div>

      <div class="button-group">
          {#each sidebarItems as item}
              <a href={item.route} title={item.title}>
                  <button class="barButtons">
                      <i class={item.icon}></i>
                  </button>
              </a>
          {/each}
      </div>
      <div class="LogOut">
        <a href="/" title="Logs user Out" on:click = {handleLogOut}>
            <i class="fas fa-sign-out"></i>
        </a>
    </div>
  </nav>

  <div class="main-content">
      <slot></slot>
  </div>
</div>

<style>

  .SB-container {
      display: flex;
      height: 100%;
      width: 100%;
      margin: 0;
      padding: 0;
      overflow: auto;
  }

  .sidebar {
      background-color: #2e2e2e;
      color: #646cff;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      width: 100px;
  }

  .TraceLogo {
      margin-bottom: 1rem;
      font-size: 2rem;
  }

  .button-group {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex-grow: 1;
      justify-content: center;
  }

  .sidebar button {
      display: flex;
      width: 50px;
      height: 50px;
      border-radius: 50%;
      margin-bottom: 1rem;
      background-color: #353535;
      color: white;
      cursor: pointer;
      justify-content: center;
      align-items: center;
  }

  .sidebar button:hover {
      background-color: #007bff;
  }

  .main-content {
      flex: 1;
      padding: 1rem;
      overflow: auto;
      background-color: #1e1e1e
  }
</style>