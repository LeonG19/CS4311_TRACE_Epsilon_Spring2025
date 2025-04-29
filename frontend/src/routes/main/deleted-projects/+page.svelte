<script>
  import { onMount } from 'svelte';

  let deletedProjects = [];
  let error = null;
  let initials = '';

  // Fetch projects on mount
  onMount(async () => {
    initials = sessionStorage.getItem('analyst_initials');
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
      // Filter projects to show only those with is_deleted = true
      deletedProjects = (data.my_projects || []).filter(project => project.is_deleted === true);
    } catch (err) {
      error = 'Failed to load deleted projects: ' + err.message;
      console.error('Fetch error:', err);
    }
  }

  async function restoreProject(projectName) {
    try {
      const response = await fetch(`http://localhost:8000/restore/${projectName}/`, {
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
      const response = await fetch(`http://localhost:8000/delete/${projectName}/`, {
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
    const jsonData = [
    {
        "id": 1,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133028,
        "payload": "root",
        "length": 134038,
        "error": false
    },
    {
        "id": 2,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133035,
        "payload": "admin",
        "length": 134045,
        "error": false
    },
    {
        "id": 3,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133028,
        "payload": "test",
        "length": 134038,
        "error": false
    },
    {
        "id": 4,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133035,
        "payload": "guest",
        "length": 134045,
        "error": false
    },
    {
        "id": 5,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133028,
        "payload": "info",
        "length": 134038,
        "error": false
    },
    {
        "id": 6,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133021,
        "payload": "adm",
        "length": 134031,
        "error": false
    },
    {
        "id": 7,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133035,
        "payload": "mysql",
        "length": 134045,
        "error": false
    },
    {
        "id": 8,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133028,
        "payload": "user",
        "length": 134038,
        "error": false
    },
    {
        "id": 9,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133091,
        "payload": "administrator",
        "length": 134101,
        "error": false
    },
    {
        "id": 10,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133042,
        "payload": "oracle",
        "length": 134052,
        "error": false
    },
    {
        "id": 11,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133021,
        "payload": "ftp",
        "length": 134031,
        "error": false
    },
    {
        "id": 12,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133014,
        "payload": "pi",
        "length": 134024,
        "error": false
    },
    {
        "id": 13,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133042,
        "payload": "puppet",
        "length": 134052,
        "error": false
    },
    {
        "id": 14,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133049,
        "payload": "ansible",
        "length": 134059,
        "error": false
    },
    {
        "id": 15,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133056,
        "payload": "ec2-user",
        "length": 134066,
        "error": false
    },
    {
        "id": 16,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133049,
        "payload": "vagrant",
        "length": 134059,
        "error": false
    },
    {
        "id": 17,
        "response": 200,
        "lines": 1103,
        "words": 6907,
        "chars": 133063,
        "payload": "azureuser",
        "length": 134073,
        "error": false
    }
];

    try {
      const response = await fetch(`http://localhost:8000/submit_results/Fuzzer/Delete_test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)  // Send the fixed JSON data
      });
      console.log('Response:', response);
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
<h1>Deleted Projects</h1>
</div>

<!-- Deleted Projects Table -->
<h2 class="mt-4">Deleted Projects</h2>
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
          <td>{project.name}</td>
          <td>
            {project.deleted_date?.slice(0, 10) + " T:" + project.deleted_date?.slice(11, 19) ||
              'N/A'}
          </td>
          <td>{project.analyst_initials || 'N/A'}</td>
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

<!-- Button to send test data -->
<div class="d-flex justify-content-between align-items-center mt-4">
<h1>Test Data Sending</h1>
<button class="btn btn-danger" on:click={sendTestData}>
  Send Test Data
</button>
</div>

<style>
.badge {
  font-size: 0.9rem;
}
</style>
