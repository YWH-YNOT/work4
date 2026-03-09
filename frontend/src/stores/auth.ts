import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface User {
    id: number
    username: string
    email: string | null
    full_name: string | null
    role: 'student' | 'teacher' | 'admin'
    is_active: boolean
}

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(localStorage.getItem('token'))
    const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))

    const isLoggedIn = computed(() => !!token.value)
    const isStudent = computed(() => user.value?.role === 'student')
    const isTeacher = computed(() => user.value?.role === 'teacher')
    const isAdmin = computed(() => user.value?.role === 'admin')

    function setAuth(newToken: string, newUser: User) {
        token.value = newToken
        user.value = newUser
        localStorage.setItem('token', newToken)
        localStorage.setItem('user', JSON.stringify(newUser))
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    }

    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        delete axios.defaults.headers.common['Authorization']
    }

    function updateUser(newUser: Partial<User>) {
        if (user.value) {
            user.value = { ...user.value, ...newUser }
            localStorage.setItem('user', JSON.stringify(user.value))
        }
    }

    // Restore axios header on page reload
    if (token.value) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }

    return { token, user, isLoggedIn, isStudent, isTeacher, isAdmin, setAuth, logout, updateUser }
})
