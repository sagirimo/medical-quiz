<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app">
    <RouterView />
  </div>
</template>

<style>
:root {
  --primary-color: #4a90d9;
  --card-bg: #ffffff;
  --bg-color: #f5f7fa;
}

@media (prefers-color-scheme: dark) {
  :root {
    --primary-color: #5ca0e9;
    --card-bg: #2a2a2a;
    --bg-color: #1a1a1a;
  }
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: var(--bg-color);
  color: #333;
  line-height: 1.6;
}

.app {
  min-height: 100vh;
}

button {
  font-family: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}
</style>
