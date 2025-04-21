<script>
  import { page } from '$app/stores';

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
      { name: 'Tree Graph', icon: 'fas fa-tree', route: '/main/tools', title: 'Navigates to the Tree Graph Page' },
      { name: 'AI Credential Generator', icon: 'fas fa-brain', route: '/main/tools/AI', title: 'Navigates to the AI Credential Generator Page' }
  ];

  // Dynamically choose the sidebar items based on the route
  $: sidebarItems = isToolsPage ? toolsSidebarItems : mainSidebarItems;

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

</script>

<div class="container">
  <nav class="sidebar" style="width: {isToolsPage ? '100px' : '200px'};">
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
  </nav>

  <div class="main-content">
      <slot></slot>
  </div>
</div>

<style>
  .container {
      display: flex;
      height: 100vh;
      overflow: auto;
      margin: 0;
      padding: 0;
  }

  .sidebar {
      background-color: #1f1f1f;
      color: #646cff;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      height: 100vh;
      transition: width 0.3s ease; /* Smooth transition for width changes */
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
  }
</style>