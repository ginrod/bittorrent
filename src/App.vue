<template>
  <div id="app">
    <img alt="Vue logo" src="./assets/logo.png">
    <!-- <index></index> -->
    <!-- <shared-files></shared-files> -->
    <results></results>
    <!-- <HelloWorld msg="Welcome to Your Vue.js App"/> -->
    <router-view></router-view>
  </div>
</template>

<script>

// import Index from './components/Index.vue';
// import SharedFiles from './components/SharedFiles.vue';
// import Results from './components/Results.vue';

export default {
  name: 'app',
  // components: {
  //   'index': Index,
  //   // 'shared-files': SharedFiles,
    // 'results': Results,
  // },
  data() {
    return {
    };
  },
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

    /* @import "assets/css/sb-admin-2.min.css";
    @import "assets/vendor/fontawesome-free/css/all.min.css"; */

</style>
