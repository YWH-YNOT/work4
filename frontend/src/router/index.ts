import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', redirect: '/login' },
        { path: '/login', component: () => import('@/views/auth/Login.vue'), meta: { public: true } },
        { path: '/register', component: () => import('@/views/auth/Register.vue'), meta: { public: true } },

        // Student routes
        {
            path: '/student',
            component: () => import('@/layouts/StudentLayout.vue'),
            meta: { role: 'student' },
            children: [
                { path: '', redirect: '/student/dashboard' },
                { path: 'dashboard', component: () => import('@/views/student/Dashboard.vue') },
                { path: 'chat', component: () => import('@/views/student/Chat.vue') },
                { path: 'timetable', component: () => import('@/views/student/Timetable.vue') },
                { path: 'assignments', component: () => import('@/views/student/Assignments.vue') },
                { path: 'quiz', component: () => import('@/views/student/Quiz.vue') },
                { path: 'grades', component: () => import('@/views/student/Grades.vue') },
                { path: 'attendance', component: () => import('@/views/student/Attendance.vue') },
                { path: 'discussions', component: () => import('@/views/student/Discussions.vue') },
                { path: 'resources', component: () => import('@/views/student/Resources.vue') },
            ]
        },

        // Teacher routes
        {
            path: '/teacher',
            component: () => import('@/layouts/TeacherLayout.vue'),
            meta: { role: 'teacher' },
            children: [
                { path: '', redirect: '/teacher/dashboard' },
                { path: 'dashboard', component: () => import('@/views/teacher/Dashboard.vue') },
                { path: 'courses', component: () => import('@/views/teacher/Courses.vue') },
                { path: 'assignments', component: () => import('@/views/teacher/Assignments.vue') },
                { path: 'quiz', component: () => import('@/views/teacher/Quiz.vue') },
                { path: 'resources', component: () => import('@/views/teacher/Resources.vue') },
                { path: 'attendance', component: () => import('@/views/teacher/Attendance.vue') },
                { path: 'grades', component: () => import('@/views/teacher/Grades.vue') },
                { path: 'announcements', component: () => import('@/views/teacher/Announcements.vue') },
                { path: 'discussions', component: () => import('@/views/teacher/Discussions.vue') },
                { path: 'logs', component: () => import('@/views/teacher/Logs.vue') },
            ]
        },

        // Admin routes
        {
            path: '/admin',
            component: () => import('@/layouts/AdminLayout.vue'),
            meta: { role: 'admin' },
            children: [
                { path: '', redirect: '/admin/dashboard' },
                { path: 'dashboard', component: () => import('@/views/admin/Dashboard.vue') },
                { path: 'users', component: () => import('@/views/admin/Users.vue') },
                { path: 'courses', component: () => import('@/views/admin/Courses.vue') },
            ]
        },

        // Legacy redirect
        { path: '/timetable', redirect: '/student/timetable' },
        { path: '/chat', redirect: '/student/chat' },
        { path: '/:pathMatch(.*)*', redirect: '/login' },
    ]
})

// Navigation guard
router.beforeEach((to, _from, next) => {
    const auth = useAuthStore()

    if (to.meta.public) return next()

    if (!auth.isLoggedIn) return next('/login')

    if (to.meta.role && auth.user?.role !== to.meta.role) {
        // Redirect to appropriate portal based on role
        const portals: Record<string, string> = {
            student: '/student/dashboard',
            teacher: '/teacher/dashboard',
            admin: '/admin/dashboard',
        }
        return next(portals[auth.user?.role || 'student'] || '/login')
    }

    next()
})

export default router
