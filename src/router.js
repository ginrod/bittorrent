import Vue from 'vue';
import Router from 'vue-router';
import Index from './components/Index';
import SharedFiles from './components/SharedFiles';
import Results from './components/Results';

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
            path: '/results',
            name: 'results',
            component: Results,
        },
        {
            path: '/shared-files',
            name: 'shared-files',
            component: SharedFiles
        }
    ]
});

export default router;
