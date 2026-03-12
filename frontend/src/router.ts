import { ref } from 'vue'

// 简单的基于 hash 的路由
export const currentRoute = ref('dashboard')

export const setupRouter = () => {
  const handleHashChange = () => {
    const hash = window.location.hash
    if (hash === '#/cluster-management' || hash.startsWith('#/cluster-management?')) {
      currentRoute.value = 'cluster-management'
    } else {
      currentRoute.value = 'dashboard'
    }
  }

  // 初始检查
  handleHashChange()

  // 监听 hash 变化
  window.addEventListener('hashchange', handleHashChange)

  // 监听导航事件
  window.addEventListener('navigate-to-cluster-management', () => {
    window.location.hash = '#/cluster-management'
  })
}

export const navigateTo = (route: string) => {
  if (route === 'cluster-management') {
    window.location.hash = '#/cluster-management'
  } else {
    window.location.hash = '#'
  }
}
