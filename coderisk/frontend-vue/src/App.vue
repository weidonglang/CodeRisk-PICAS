<script setup lang="ts">
import {
  DataAnalysis,
  DataBoard,
  Files,
  HomeFilled,
  List,
  Setting,
} from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/dashboard', label: '工作台', icon: HomeFilled },
  { path: '/questions', label: '题目', icon: Files },
  { path: '/tasks', label: '任务', icon: List },
  { path: '/experiments', label: '实验', icon: DataAnalysis },
  { path: '/settings', label: '设置', icon: Setting },
]

const activePath = computed(() => route.path)
</script>

<template>
  <el-config-provider>
    <main class="app-shell">
      <aside class="sidebar" aria-label="主导航">
        <div class="brand">
          <DataBoard class="brand-icon" />
          <div>
            <strong>CodeRisk</strong>
            <span>PICAS</span>
          </div>
        </div>
        <nav>
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            :class="{ active: activePath.startsWith(item.path) }"
          >
            <component :is="item.icon" />
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </aside>
      <section class="main-surface">
        <router-view />
      </section>
    </main>
  </el-config-provider>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 232px minmax(0, 1fr);
  min-height: 100vh;
  background: #f4f7f6;
  color: #16211f;
}

.sidebar {
  border-right: 1px solid #d9e2de;
  background: #ffffff;
  padding: 20px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  margin-bottom: 20px;
}

.brand-icon {
  width: 28px;
  height: 28px;
  color: #0f766e;
}

.brand strong,
.brand span {
  display: block;
}

.brand strong {
  font-size: 18px;
}

.brand span {
  color: #64736f;
  font-size: 12px;
}

nav {
  display: grid;
  gap: 6px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  border-radius: 6px;
  color: #4a5b56;
  padding: 0 10px;
  text-decoration: none;
}

.nav-link svg {
  width: 18px;
  height: 18px;
}

.nav-link.active,
.nav-link:hover {
  background: #e7f3ef;
  color: #0f766e;
}

.main-surface {
  min-width: 0;
  padding: 24px;
}

@media (max-width: 760px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: 0;
    border-bottom: 1px solid #d9e2de;
    padding: 12px;
  }

  nav {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }

  .nav-link {
    justify-content: center;
    padding: 0;
  }

  .nav-link span,
  .brand span {
    display: none;
  }

  .main-surface {
    padding: 16px;
  }
}
</style>
