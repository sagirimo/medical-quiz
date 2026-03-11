import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SubjectView from '../views/SubjectView.vue'
import QuizView from '../views/QuizView.vue'
import WrongBookView from '../views/WrongBookView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/subject/:subject',
    name: 'subject',
    component: SubjectView
  },
  {
    path: '/quiz/:subject',
    name: 'quiz',
    component: QuizView
  },
  {
    path: '/wrong-book',
    name: 'wrong-book',
    component: WrongBookView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
