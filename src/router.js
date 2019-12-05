import Vue from 'vue';
import Router from 'vue-router';
import Index from './components/Index';
import SharedFiles from './components/SharedFiles';
import Results from './components/Results';
import History from './components/History';
import HelloWorld from './components/HelloWorld';

Vue.use(Router);

const router = new Router({
    mode: 'history',
    base: process.env.BASE_URL,
    routes: [
        //Redirections
        {
            path: '/',
            redirect: {name: 'index'},
        },
        {
            path: '/index',
            name: 'index',
            component: Index,
        },

        {
            path: '/results/:pattern',
            name: 'results',
            component: Results,
        },

        {
            path: '/shared-files',
            name: 'shared-files',
            component: SharedFiles
        },
        {
            path: '/history',
            name: 'history',
            component: History
        },

        {
            path: '/hello-world',
            name: '/hello-world',
            component: HelloWorld
        },
    ]
});

export default router;
