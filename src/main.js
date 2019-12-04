import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App.vue'
import 'bootstrap'; 
import 'bootstrap/dist/css/bootstrap.min.css';
import router from './router';
// import './assets/vendor/jquery/jquery.min';
// import './assets/vendor/bootstrap/js/bootstrap.bundle.min';
// import './assets/vendor/jquery-easing/jquery.easing.min';
// import './assets/js/sb-admin-2.min';


Vue.use(VueRouter)

Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
