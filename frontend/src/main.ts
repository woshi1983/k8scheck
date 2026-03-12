import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import App from './App.vue'
import { setupRouter } from './router'

const app = createApp(App)
app.use(ElementPlus)

// 设置路由
setupRouter()

app.mount('#app')
