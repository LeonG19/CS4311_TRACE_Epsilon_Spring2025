<script>
    import { createEventDispatcher } from 'svelte';

    const dispatch = createEventDispatcher();

    let folderName = '';
    let error = null;

    async function handleSubmit() {
        if (!folderName.trim()) {
            error = 'Folder name is required.';
            return;
        }

        const formData = new FormData();
        formData.append('folder_name', folderName);

        try {
            const response = await fetch('http://localhost:8000/create_folder/', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                dispatch('folderCreated');
                resetForm();
            } else {
                const data = await response.json();
                error = data.error || 'Failed to create folder';
            }
        } catch (err) {
            error = 'Error creating folder: ' + err.message;
        }
    }

    function resetForm() {
        folderName = '';
        error = null;
    }

    function closeModal() {
        resetForm();
        dispatch('close');
    }
</script>

<!-- Modal layout -->
<div class="modal fade show" style="display: block;" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Create New Folder</h5>
                <button type="button" class="btn-close" on:click={closeModal} aria-label="Close"></button>
            </div>
            <div class="modal-body">
                {#if error}
                    <div class="alert alert-danger">{error}</div>
                {/if}
                <form on:submit|preventDefault={handleSubmit}>
                    <div class="mb-3">
                        <label for="folder_name" class="form-label">Folder Name</label>
                        <input
                            type="text"
                            class="form-control"
                            id="folder_name"
                            bind:value={folderName}
                            required
                        />
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-primary">Create Folder</button>
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
