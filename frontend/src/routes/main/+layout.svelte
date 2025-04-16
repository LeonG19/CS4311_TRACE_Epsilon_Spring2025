<script>
    import { onMount } from 'svelte';
    import Navbar from '../../components/Navbar.svelte';
    import 'bootstrap/dist/css/bootstrap.min.css';
  
    // Load Bootstrap JS only in the browser
    onMount(async () => {
      if (typeof window !== 'undefined') {
        await import('bootstrap/dist/js/bootstrap.bundle.min.js');
      }
    });
  </script>
  
  <div class="container-fluid">
    <div class="row">
      <Navbar />
      <main class="col-md-10 ms-sm-auto px-md-4">
        <slot />
      </main>
    </div>
  </div>
  
  <style>
    main {
      padding-top: 1rem;
    }
  </style>