// https://nuxt.com/docs/api/configuration/nuxt-config
// export default defineNuxtConfig({
//   devtools: { enabled: true },
//   srcDir: "src/",
//   routeRules: {
//     '/api/**': {
//       proxy: process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000/api/**" : "/api/**",
//     },
//     '/docs': {
//       proxy: "http://127.0.0.1:8000/docs",
//     },
//     '/openapi.json': {
//       proxy: "http://127.0.0.1:8000/openapi.json",
//     }
//   } 
// })

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },
  srcDir: "src/",
  routeRules: {
    '/api/**': {
      proxy: process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000/**" : (process.env.API_URL || "http://localhost:8000") + "/**",
    },
    '/docs': {
      proxy: "http://127.0.0.1:8000/docs",
    },
    '/openapi.json': {
      proxy: "http://127.0.0.1:8000/openapi.json",
    }
  },
  vite: {
    optimizeDeps: {
      include: ['plotly.js-dist-min']  // Optimize Plotly.js for Vite
    }
  },
  // Optional: Add Axios module if you prefer using Axios over useFetch
  // modules: ['@nuxtjs/axios'],
  
  compatibilityDate: "2025-03-16",
  components: [
    {
      path:'~/components',
      pathPrefix: false,
    }
  ],
  modules:['@nuxt/ui', "@nuxtjs/color-mode"],
  css:['./assets/css/main.css'],
  build: {
    standalone: true,
    parallel: false,
    cache: true,
    hardSource: false
  },
  nitro: {
    devServer: {
      watch: ['./src/**']
    }
  },
    features: {
    devLogs: false,
    transitions: false
  } 
})
