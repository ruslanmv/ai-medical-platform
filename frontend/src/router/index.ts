import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
      meta: {
        title: 'Login Page' // Breadcrumb display title
      }
    },
    {
      path: '/',
      redirect: { name: 'Home' },
      component: () => import('@/layouts/BaseLayout.vue'),
      meta: {
        requiresAuth: true // Whether login verification is required, configure the root route, and sub-routes will inherit
      },
      children: [
        {
          path: '/home',
          name: 'Home',
          component: () => import('@/views/home/HomeView.vue'),
          meta: { title: 'Home' }
        },
        // ---------------------
        //     Product
        // ---------------------
        {
          path: '/product',
          name: 'Product',
          redirect: { name: 'ProductList' },
          meta: { title: 'Product Management' },
          children: [
            {
              path: '/product/list',
              name: 'ProductList',
              component: () => import('@/views/product/ProductListView.vue'),
              meta: { title: 'Product List' }
            },
            {
              path: '/product/create',
              name: 'ProductCreate',
              component: () => import('@/views/product/ProductEditView.vue'),
              meta: { title: 'Add Product' }
            },
            {
              path: '/product/:productId/edit',
              name: 'ProductEdit',
              component: () => import('@/views/product/ProductEditView.vue'),
              meta: { title: 'Edit Product' },
              props: true
            }
          ]
        },
        // ---------------------
        //     Digital Human Management
        // ---------------------
        {
          path: '/digital_human',
          name: 'DigitalHuman',
          redirect: { name: 'DigitalHumanList' },
          meta: { title: 'Digital Human Management' },
          children: [
            {
              path: '/digital_human/list',
              name: 'DigitalHumanList',
              component: () => import('@/views/digital-human/DigitalHumanView.vue'),
              meta: { title: 'Role Management' }
            }
          ]
        },
        // ---------------------
        //     Live Streaming Management
        // ---------------------

        {
          path: '/streaming',
          name: 'Streaming',
          redirect: { name: 'StreamingOverview' },
          meta: { title: 'Streaming Management' },
          children: [
            {
              path: '/streaming/overview',
              name: 'StreamingOverview',
              component: () => import('@/views/streaming/StreamingRoomListView.vue'),
              meta: { title: 'Live Room Management' }
            },
            {
              path: '/streaming/create',
              name: 'StreamingCreate',
              component: () => import('@/views/streaming/StreamingRoomeEditView.vue'),
              meta: { title: 'Create Live Room' }
            },
            {
              path: '/streaming/:roomId/edit',
              name: 'StreamingEdit',
              component: () => import('@/views/streaming/StreamingRoomeEditView.vue'),
              meta: { title: 'Edit Live Room' },
              props: true
            },
            {
              path: '/streaming/:roomId/on-air',
              name: 'StreamingOnAir',
              component: () => import('@/views/streaming/StreamingOnAirView.vue'),
              meta: { title: 'Live Room' },
              props: true
            }
          ]
        },
        // ---------------------
        //     Order Management
        // ---------------------
        {
          path: '/order',
          name: 'Order',
          redirect: { name: 'OrderOverview' },
          meta: { title: 'Order Management' },
          children: [
            {
              path: '/order/overview',
              name: 'OrderOverview',
              component: () => import('@/views/order/OrderView.vue'),
              meta: { title: 'Order Management' }
            }
          ]
        },
        // ---------------------
        //     System Configuration
        // ---------------------
        {
          path: '/system',
          name: 'System',
          redirect: { name: 'SystemPlugins' },
          meta: { title: 'System Configuration' },
          children: [
            {
              path: '/system/plugins',
              name: 'SystemPlugins',
              component: () => import('@/views/system/SystemPluginsView.vue'),
              meta: { title: 'Component Status' }
            }
          ]
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/NotFound.vue'),
      meta: { title: '404' }
    }
  ]
})

import { useTokenStore } from '@/stores/userToken'

router.beforeEach((to, from, next) => {
  if (to.matched.some((r) => r.meta?.requiresAuth)) {
    // Login status caching
    const tokenStore = useTokenStore()

    if (!tokenStore.token.access_token) {
      // Not logged in, redirect to the login page, and record the address you want to go to (to.fullPath) to facilitate redirection after login
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }
  // Dynamically change page title
  to.matched.some((item) => {
    if (!item.meta.title) return ''

    const Title = 'Top Sales - Live Streaming Seller Large Model'
    if (Title) document.title = `${item.meta.title} | ${Title}`
    else document.title = item.meta.title
  })

  next()
})

export default router