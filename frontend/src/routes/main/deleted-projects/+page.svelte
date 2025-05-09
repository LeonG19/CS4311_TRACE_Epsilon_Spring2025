<script>
  import { onMount } from 'svelte';

  let deletedProjects = [];
  let error = null;
  let initials = '';
  let file;

  // Fetch projects on mount
  onMount(async () => {
    initials = sessionStorage.getItem('analyst_initials');
    await fetchProjects();
  });

  async function fetchProjects() {
    try {
      const response = await fetch(`http://169.254.7.176:8000/dashboard/${initials}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      console.log('Fetched data:', data);
      // Filter projects to show only those with is_deleted = true
      deletedProjects = (data.my_projects || []).filter(project => project.is_deleted === true);
    } catch (err) {
      error = 'Failed to load deleted projects: ' + err.message;
      console.error('Fetch error:', err);
    }
  }

  async function restoreProject(projectName) {
    try {
      const response = await fetch(`http://169.254.7.176:8000/restore/${projectName}/`, {
        method: 'POST'
      });
      if (response.ok) {
        deletedProjects = deletedProjects.filter(project => project.name !== projectName);
      } else {
        throw new Error('Failed to restore project');
      }
    } catch (err) {
      error = err.message;
    }
  }

  async function deleteForever(projectName) {
    try {
      const response = await fetch(`http://169.254.7.176:8000/delete/${projectName}/`, {
        method: 'POST'
      });
      if (response.ok) {
        deletedProjects = deletedProjects.filter(project => project.name !== projectName);
      } else {
        throw new Error('Failed to delete project permanently');
      }
    } catch (err) {
      error = err.message;
    }
  }

  // Function to send the specific test data
  async function sendTestData() {
    try {
      const formData = new FormData();
      const fileInput = document.querySelector('#fileInput'); // Asegúrate de tener un input de archivo en tu HTML

      if (!fileInput.files.length) {
      throw new Error('No file selected');
    }

      const file = fileInput.files[0];
      formData.append('file', file);

      const response = await fetch('http://169.254.7.176:8000/submit_txt_results/AI/Hacking_Mexico', {
      method: 'POST',
      body: formData // No necesitas headers, fetch los pone automáticamente con FormData
  });
      console.log('Response:', formData.getAll('file'));
      if (response.ok) {
        const result = await response.json();
        console.log('Data sent successfully:', result);
      } else {
        throw new Error('Failed to send test data');
      }
    } catch (err) {
      error = err.message;
      console.error('Send error:', err);
    }
  }
</script>

{#if error}
<div class="alert alert-danger">{error}</div>
{/if}

<!-- Header with Title -->
<div class="d-flex justify-content-between align-items-center mt-4">
<h1 style="color: white">Deleted Projects</h1>
</div>

<!-- Deleted Projects Table -->
<h2 class="mt-4" style="color: white">Deleted Projects</h2>
<div class="tab-content mt-3">
{#if deletedProjects.length > 0}
  <table class="table table-striped">
    <thead>
      <tr>
        <th>Project Name</th>
        <th>Deleted Date</th>
        <th>Lead Analyst</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#each deletedProjects as project}
        <tr data-project-name={project.name}>
          <td style="color: white">{project.name}</td>
          <td style="color: white">
            {project.deleted_date?.slice(0, 10) + " T:" + project.deleted_date?.slice(11, 19) ||
              'N/A'}
          </td>
          <td style="color: white">{project.analyst_initials || 'N/A'}</td>
          <td class="d-flex gap-2 align-items-center">
            <button
              class="btn btn-sm btn-primary"
              on:click={() => restoreProject(project.name)}
            >
              Restore
            </button>
            <button
              class="btn btn-sm btn-danger"
              on:click={() => deleteForever(project.name)}
            >
              Delete Forever
            </button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
{:else}
  <p>No deleted projects available.</p>
{/if}
</div>
