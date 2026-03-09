import axios from 'axios'

// Axios 拦截器：统一错误处理
axios.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            // 清空 axios 全局请求头，防止残留旧 token 继续发请求
            delete axios.defaults.headers.common['Authorization']
            window.location.href = '/login'
        }
        return Promise.reject(err)
    }
)

export default axios
