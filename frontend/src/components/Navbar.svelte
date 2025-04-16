<script>
    import { page } from '$app/stores'; // Track current route
    import { goto } from '$app/navigation'; // For navigation
  
    // Navigation items based on your routes
    const navItems = [
      { name: 'Project Selection', icon: '📁', route: '/main/', hoverText: 'Access project selection' },
      { name: 'Project Folders', icon: '📂', route: '/main/project-folders/', hoverText: 'Access project folders' },
      { name: 'Deleted Projects', icon: '🗑️', route: '/main/deleted-projects/', hoverText: 'Open archived projects' },
      { name: 'Settings', icon: '⚙️', route: '/main/settings/', hoverText: 'Configure settings' }
    ];
  
    function handleLogoClick() {
      goto('/main/'); // Go to root (Project Selection)
    }
  </script>
  
  <style>
    .sidebar {
      background-color: #f8f9fa;
      padding: 1rem;
      height: 100vh;
      position: sticky;
      top: 0;
    }
    .logo {
      display: block;
      text-align: center;
      margin-bottom: 1.5rem;
      cursor: pointer;
      font-size: 1.5rem;
      font-weight: bold;
      color: #333;
    }
    .nav-item {
      margin: 0.75rem 0;
      position: relative;
    }
    .nav-link {
      display: flex;
      align-items: center;
      padding: 0.5rem;
      border-radius: 4px;
      text-decoration: none;
      color: #333;
      font-size: 1rem;
      transition: background-color 0.2s;
    }
    .nav-link:hover {
      background-color: #e9ecef;
    }
    .nav-link.active {
      background-color: #007bff;
      color: white;
    }
    .icon {
      margin-right: 0.5rem;
      font-size: 1.2rem;
    }
    .tooltip {
      visibility: hidden;
      position: absolute;
      left: 100%;
      top: 50%;
      transform: translateY(-50%);
      background-color: #333;
      color: white;
      padding: 0.5rem;
      border-radius: 4px;
      white-space: nowrap;
      z-index: 10;
      font-size: 0.9rem;
    }
    .nav-link:hover .tooltip {
      visibility: visible;
    }
  </style>
  
  <nav class="sidebar col-md-2">
    <div class="logo" on:click={handleLogoClick} role="button" tabindex="0" on:keydown={(e) => e.key === 'Enter' && handleLogoClick()}>
      TRACE
    </div>
    <ul class="nav flex-column">
      {#each navItems as item}
        <li class="nav-item">
          <a
            href={item.route}
            class="nav-link {item.route === $page.url.pathname ? 'active' : ''}"
          >
            <span class="icon">{item.icon}</span>
            <span>{item.name}</span>
            <span class="tooltip">{item.hoverText}</span>
          </a>
        </li>
      {/each}
    </ul>
  </nav>