<script>
    import { onMount } from 'svelte';
    import CreateProjectModal from './CreateProjectModal.svelte';
    import { goto } from '$app/navigation';
  
    let myProjects = [];
    let filteredMyProjects = [];
    let sharedProjects = [];
    let filteredSharedProjects = [];
    let showCreateModal = false;
    let error = null;
    let searchQuery = '';
    let statusFilter = 'All';
    let recent_projects=[];
    let initials='';
    
  
    // Fetch projects on mount
    onMount(async () => {
      initials= sessionStorage.getItem('analyst_initials');
      await fetchProjects();
    });
  
    async function fetchProjects() {
      try {
        const response = await fetch(`http://localhost:8000/dashboard/${initials}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch projects: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        console.log('Fetched data:', data);
        myProjects = data.my_projects || [];
        sharedProjects = data.shared_projects || [];
        recent_projects=[...myProjects]
        recent_projects.sort((a,b)=> {
        const dateA=Date.parse(a.last_edit_date);
        const dateB= Date.parse(b.last_edit_date);
        return dateB-dateA;
      })
        applyFilters();
      } catch (err) {
        error = 'Failed to load projects: ' + err.message;
        console.error('Fetch error:', err);
      }
    }
  
    // Apply search and filter
    function applyFilters() {
      let filtered = myProjects;
      if (searchQuery) {
        filtered = filtered.filter(project =>
          project.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      if (statusFilter !== 'All') {
        filtered = filtered.filter(project => project.Status === statusFilter);
      }
      filteredMyProjects = filtered;
  
      filtered = sharedProjects;
      if (searchQuery) {
        filtered = filtered.filter(project =>
          project.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      if (statusFilter !== 'All') {
        filtered = filtered.filter(project => project.Status === statusFilter);
      }
      filteredSharedProjects = filtered;
    }
  
    // Watch for changes in search and filter
    $: searchQuery, statusFilter, applyFilters();

    async function lockProject(projectName, analyst_initials) {
    try {
      const response = await fetch(`http://localhost:8000/lock/${projectName}/${analyst_initials}`, {
        method: 'POST'
      });
      if (response.ok) {
        // Update myProjects
        myProjects = myProjects.map(project =>
          project.name === projectName ? { ...project, locked: true, Status: 'Inactive' } : project
        );
        recent_projects=recent_projects.map(project=>
          project.name === projectName ? {...project, locked: true, Status: 'Inactive'}: project
        );
        // Update sharedProjects if the project exists there
        sharedProjects = sharedProjects.map(project =>
          project.name === projectName ? { ...project, locked: true, Status: 'Inactive' } : project
        );
        applyFilters(); // Refresh filtered lists
      } else {
        throw new Error('Failed to lock project');
      }
    } catch (err) {
      error = err.message;
    }
  }

  async function restoreProject(projectName, analyst_initials) {
    try {
      const response = await fetch(`http://localhost:8000/unlock/${projectName}/${analyst_initials}`, {
        method: 'POST'
      });
      if (response.ok) {
        // Update myProjects
        myProjects = myProjects.map(project =>
          project.name === projectName ? { ...project, locked: false, Status: 'Active' } : project
        );
        recent_projects=recent_projects.map(project=>
          project.name === projectName ? {...project, locked: false, Status: 'Active'}: project
        );
        // Update sharedProjects if the project exists there
        sharedProjects = sharedProjects.map(project =>
          project.name === projectName ? { ...project, locked: false, Status: 'Active' } : project
        );
        applyFilters(); // Refresh filtered lists
      } else {
        throw new Error('Failed to restore project');
      }
    } catch (err) {
      error = err.message;
    }
  }

  async function deleteProject(projectName) {
        try{
            const response= await fetch(`http://localhost:8000/delete/${projectName}`,{
                method: 'POST'
            });
            if (response.ok){
                fetchProjects();
            }
            else {
                throw new Error('Failed to delete project');
            }      
        }catch (err){
            error =err.message;
        }
    }

    async function exportProject(projectName) {
    try {
      const response = await fetch(`http://localhost:8000/export/${projectName}`, {
        method: 'GET'
      });
      if (!response.ok) {
        throw new Error('Failed to export project');
      }
      const data = await response.json();
      if (data.status === 'success') {
        const jsonStr = JSON.stringify(data.data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${projectName}_export.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } else {
        throw new Error(data.error || 'Failed to export project');
      }
    } catch (err) {
      error = 'Failed to export project: ' + err.message;
      console.error('Export error:', err);
    }
  }
  
  
    // Placeholder for Run Scan
    async function runScan(projectName) {
      goto('main/tools/');
      console.log(`Running scan for project: ${projectName}`);
      // Implement API call if needed
    }
  </script>
  
  {#if error}
    <div class="alert alert-danger">{error}</div>
  {/if}
  
  <!-- Header with Title and Buttons -->
  <div class="d-flex justify-content-between align-items-center mt-4">
    <h1 style="color: white">Project Selection</h1>
    <div class="d-flex gap-2">
      <button class="btn btn-outline-secondary">
        <span class="import-icon">🖴</span> Import
      </button>
      <button class="btn create-btn text-white" on:click={() => (showCreateModal = true)}>
        + Create New
      </button>
    </div>
  </div>
  
  <!-- Recent Projects -->
  <div class="container-fluid mt-4">
    <h2 class="mt-4" style="color: white">Recent Projects</h2>
    <div class="row gx-3">
      {#each recent_projects.slice(0, 3) as project}
        <div class="col-md-4 mb-3" style="background-color: #242424; border: 2px solid #2e2e2e;">
          <button type="button" class="card h-100 clickable-card" on:click={() => runScan(project.name)}>
            <div class="card-body">
              <h5 class="card-title" style="color: white">{project.name}</h5>
              <p class="card-text" style="color: white">
                Last Edit: {project.last_edit_date.slice(0, 10) + " T:" + project.last_edit_date.slice(11, 19) || project.Stamp_Date.slice(0, 10) + " T:" + project.Stamp_Date.slice(11, 19) || 'N/A'}
              </p>
            </div>
            <div class="card-footer {project.Status === 'Active' ? 'border-success' : project.Status === 'Error' ? 'border-danger' : 'border-secondary'}">
              <small style="color: white">Status: {project.Status}</small>
            </div>
          </button>
        </div>
      {/each}
      {#if myProjects.length === 0}
        <p>No recent projects available.</p>
      {/if}
    </div>
  </div>
  
  <!-- All Projects -->
  <h2 class="mt-4" style="color: white">All Projects</h2>
  
  <!-- Search and Filter Bar -->
  <div class="d-flex justify-content-end mb-3">
    <div class="input-group w-50">
      <input
        type="text"
        class="form-control"
        placeholder="Search projects..."
        bind:value={searchQuery}
      />
      <select class="form-select" bind:value={statusFilter}>
        <option>All</option>
        <option>Active</option>
        <option>Error</option>
        <option>Inactive</option>
      </select>
    </div>
  </div>
  
  <!-- Tabs -->
  <ul class="nav nav-tabs mt-4" id="projectTabs" role="tablist">
    <li class="nav-item" role="presentation">
      <button
        class="nav-link active"
        id="my-projects-tab"
        data-bs-toggle="tab"
        data-bs-target="#my-projects"
        type="button"
        role="tab"
        aria-controls="my-projects"
        aria-selected="true"
        style="color: white; background-color:#242424; border: 1px solid #2e2e2e;"
      >
        My Projects
      </button>
    </li>
    <li class="nav-item" role="presentation">
      <button
        class="nav-link"
        id="shared-projects-tab"
        data-bs-toggle="tab"
        data-bs-target="#shared-projects"
        type="button"
        role="tab"
        aria-controls="shared-projects"
        aria-selected="false"
        style="color: white; background-color:#242424; border: 1px solid #2e2e2e;"
      >
        Shared Projects
      </button>
    </li>
  </ul>
  
  <div class="tab-content mt-3" id="projectTabsContent">
    <!-- My Projects Tab -->
    <div class="tab-pane fade show active" id="my-projects" role="tabpanel" aria-labelledby="my-projects-tab">
      {#if filteredMyProjects.length > 0}
        <table class="table table-striped">
          <thead>
            <tr>
              <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Project Name</th>
              <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Last Edit</th>
              <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Lead Analyst</th>
              <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Status</th>
              <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Actions</th>
            </tr>
          </thead>
          <tbody style="border: 2px solid #2e2e2e;">
            {#each filteredMyProjects.filter(project=>project.is_deleted===false) as project}
              <tr data-project-name={project.name}>
                <td style="color: white;">{project.name}</td>
                <td style="color: white;">{project.last_edit_date.slice(0,10)+" T:"+ project.last_edit_date.slice(11,19)|| project.Stamp_Date.slice(0,10) +" T:"+ project.Stamp_Date.slice(11,19) || 'N/A'}</td>
                <td style="color: white;">{project.analyst_initials || 'N/A'}</td>
                <td>
                  <span
                    class="badge {project.Status === 'Active'
                      ? 'bg-success'
                      : project.Status === 'Inactive'
                      ? 'bg-secondary'
                      : project.Status === 'Error'
                      ? 'bg-danger'
                      : 'bg-secondary'}"
                  >
                    {project.Status}
                  </span>
                </td>
                <td class="d-flex gap-2 align-items-center">
                  <button
                    class="btn btn-sm btn-primary"
                    disabled={project.Status !== 'Active'}
                    on:click={() => runScan(project.name)}
                  >
                    Run Scan
                  </button>
                  <div class="dropdown">
                    <button
                      class="btn btn-sm btn-outline-secondary"
                      type="button"
                      id={"dropdownMenuButton-"+project.name}
                      data-bs-toggle="dropdown"
                      aria-expanded="false"
                    >
                      ⋮
                    </button>
                    <ul class="dropdown-menu" aria-labelledby={"dropdownMenuButton-"+project.name}>
                      {#if project.locked}
                        <li>
                          <button
                            class="dropdown-item"
                            on:click={() => restoreProject(project.name, "MR")}
                          >
                            Restore
                          </button>
                          <button
                            class="dropdown-item"
                            on:click={() => deleteProject(project.name)}
                          >
                            Delete
                          </button>
                        </li>
                      {:else}
                        <li>
                          <button
                            class="dropdown-item"
                            on:click={() => lockProject(project.name, "MR")}
                          >
                            Lock
                          </button>
                          <button
                            class="dropdown-item"
                            on:click={() => deleteProject(project.name)}
                          >
                            Delete
                          </button>
                        </li>
                      {/if}
                      <li>
                        <button
                          class="dropdown-item"
                          on:click={() => exportProject(project.name)}
                        >
                          Export
                        </button>
                      </li>
                    </ul>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {:else}
        <p>No projects match your criteria.</p>
      {/if}
    </div>
  
    <!-- Shared Projects Tab -->
    <div class="tab-pane fade" id="shared-projects" role="tabpanel" aria-labelledby="shared-projects-tab">
        {#if filteredSharedProjects.length > 0}
        <table class="table table-striped">
            <thead>
            <tr>
                <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Project Name</th>
                <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Last Edit</th>
                <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Lead Analyst</th>
                <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Port</th>
                <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Status</th>
                <th style="color: white; background-color:#242424; border: 2px solid #2e2e2e;">Actions</th>
            </tr>
            </thead>
            <tbody>
            {#each filteredSharedProjects as project}
                <tr>
                <td style="color: white;">{project.name}</td>
                <td style="color: white;">{project.last_edit_date?.slice(0,10) + " T:" + project.last_edit_date?.slice(11,19) || project.Stamp_Date?.slice(0,10) + " T:" + project.Stamp_Date?.slice(11,19) || 'N/A'}</td>
                <td style="color: white;">{project.analyst_initials || 'N/A'}</td>
                <td style="color: white;">{project.port_number || 'N/A'}</td>
                <td>
                    <span
                    class="badge {project.Status === 'Active'
                        ? 'bg-success'
                        : project.Status === 'Inactive'
                        ? 'bg-secondary'
                        : project.Status === 'Error'
                        ? 'bg-danger'
                        : 'bg-secondary'}"
                    >
                    {project.Status}
                    </span>
                </td>
                <td>
                    <button
                    class="btn btn-sm btn-primary"
                    disabled={project.Status !== 'Active'}
                    on:click={() => joinProject(project.name, project.port_number)}
                    title="Join this project session."
                    >
                    Join
                    </button>
                </td>
                </tr>
            {/each}
            </tbody>
        </table>
        {:else}
        <p>No shared projects match your criteria.</p>
        {/if}
    </div>

  </div>
  
  {#if showCreateModal}
    <CreateProjectModal
      on:close={() => (showCreateModal = false)}
      on:projectCreated={() => {
        showCreateModal = false;
        fetchProjects();
      }}
    />
  {/if}
  
  <style>
    .create-btn {
      background-color: #007bff;
    }
    .create-btn:hover {
        background-color: black;
    }
    .import-icon {
      font-size: 1.2rem;
      margin-right: 0.5rem;
    }
    .card-footer {
      background-color: transparent;
    }
    .badge {
      font-size: 0.9rem;
    }
    .clickable-card {
      cursor: pointer;
    transition: background-color 0.2s ease;
    width: 100%; /* Ensure button fills card */
    padding: 0; /* Remove default button padding */
    border: none; /* Remove default button border */
    background: none; /* Remove default button background */
    text-align: left; /* Align content naturally */
    border-radius: 0.5rem; /* Match Bootstrap card style */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Card shadow */
    }
    .clickable-card:hover {
        background-color: #0000004e;
    }
  </style>