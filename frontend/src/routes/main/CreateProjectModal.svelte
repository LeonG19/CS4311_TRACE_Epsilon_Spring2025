<script>
    import { createEventDispatcher } from 'svelte';
  
    const dispatch = createEventDispatcher();
  
    let projectName = '';
    let startDate = '';
    let endDate = '';
    let description = '';
    let leadAnalystInitials = '';
    let fileNames = null;
    let files = null; // Declare files variable
    let error = null;
    let localFilePath = '';
  
    async function handleSubmit() {
      const formData = new FormData();
      formData.append('project_name', projectName);
      formData.append('start_date', startDate);
      formData.append('end_date', endDate);
      formData.append('description', description);
      formData.append('lead_analyst_initials', leadAnalystInitials);
      formData.append('local_file_path', localFilePath);
  
      if (files) {
        // Append each file
        fileNames = Array.from(files).map(file => file.name);
        for (let file of files) {
          formData.append('files', file); // Use 'files' for file uploads
        }
        formData.append('file_names', JSON.stringify(fileNames));
      }
  
      try {
        const response = await fetch(`http://169.254.7.176/create/`, {
          method: 'POST',
          body: formData
        });
  
        if (response.ok) {
          dispatch('projectCreated');
          resetForm();
        } else {
          const data = await response.json();
          error = data.error || 'Failed to create project';
        }
      } catch (err) {
        error = 'Error creating project: ' + err.message;
      }
    }
  
    function resetForm() {
      projectName = '';
      startDate = '';
      endDate = '';
      description = '';
      leadAnalystInitials = '';
      fileNames = null;
      files = null; // Reset files
      localFilePath = '';
      error = null;
    }
  
    function closeModal() {
      resetForm();
      dispatch('close');
    }
  </script>
  
  <div class="modal fade show" style="display: block;" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header" style="background-color: #232323;">
          <h5 class="modal-title" style="color: white;">Create New Project</h5>
          <button type="button" class="btn-close" on:click={closeModal} aria-label="Close"></button>
        </div>
        <div class="modal-body" style="background-color: #2e2e2e;">
          {#if error}
            <div class="alert alert-danger">{error}</div>
          {/if}
          <form on:submit|preventDefault={handleSubmit}>
            <div class="mb-3">
              <label for="project_name" class="form-label">Project Name</label>
              <input
                type="text"
                class="form-control"
                id="project_name"
                bind:value={projectName}
                required
              />
            </div>
            <div class="mb-3">
              <label for="start_date" class="form-label">Start Date</label>
              <input
                type="date"
                class="form-control"
                id="start_date"
                bind:value={startDate}
                required
              />
            </div>
            <div class="mb-3">
              <label for="end_date" class="form-label">End Date</label>
              <input
                type="date"
                class="form-control"
                id="end_date"
                bind:value={endDate}
                required
              />
            </div>
            <div class="mb-3">
              <label for="description" class="form-label">Description</label>
              <textarea
                class="form-control"
                id="description"
                bind:value={description}
              ></textarea>
            </div>
            <div class="mb-3">
              <label for="lead_analyst_initials" class="form-label">Lead Analyst Initials</label>
              <input
                type="text"
                class="form-control"
                id="lead_analyst_initials"
                bind:value={leadAnalystInitials}
                required
              />
            </div>
            <div class="mb-3">
              <label for="file_names" class="form-label">Upload Files (optional)</label>
              <input
                type="file"
                class="form-control"
                id="file_names"
                multiple
                on:change={(e) => (files = e.target.files)}
              />
            </div>
            <div class="mb-3">
              <label for="local_file_path" class="form-label">Local File Path (optional)</label>
              <input
                type="text"
                class="form-control"
                id="local_file_path"
                bind:value={localFilePath}
              />
            </div>
            <div class="modal-footer">
              <button type="submit" class="btn btn-primary">Create Project</button>
              <button type="button" class="btn btn-secondary" on:click={closeModal}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
  <div class="modal-backdrop fade show"></div>