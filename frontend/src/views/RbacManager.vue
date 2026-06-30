<template>
  <div class="rbac-manager">
    <div class="page-header">
      <div>
        <h2 class="page-title">🛡️ 角色权限管理</h2>
        <p class="page-subtitle">基于角色的访问控制（RBAC）——角色、权限、用户角色分配</p>
      </div>
      <div>
        <el-button type="primary" @click="openAssignDialog">分配用户角色</el-button>
        <el-button @click="loadAll">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：角色列表 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>角色列表</span>
              <el-tag v-if="permissionStore.isAdmin" type="danger" size="small">管理员</el-tag>
            </div>
          </template>
          <el-table
            v-loading="roleLoading"
            :data="roles"
            highlight-current-row
            @current-change="onRoleSelect"
            size="small"
          >
            <el-table-column prop="display_name" label="角色" min-width="100" />
            <el-table-column prop="code" label="代码" min-width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_system ? 'warning' : 'info'">
                  {{ row.code || row.name }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="系统" width="60" align="center">
              <template #default="{ row }">
                <el-icon v-if="row.is_system" color="#E6A23C"><Star /></el-icon>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="roles.length === 0 && !roleLoading" class="empty-tip">暂无角色数据</div>
        </el-card>
      </el-col>

      <!-- 右侧：权限分配 -->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>
                权限分配
                <el-tag v-if="selectedRole" type="success" size="small" style="margin-left: 8px;">
                  {{ selectedRole.display_name }}
                </el-tag>
              </span>
              <div v-if="selectedRole && canEditRole">
                <el-button type="primary" size="small" :loading="saveLoading" @click="savePermissions">
                  保存权限
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="!selectedRole" class="empty-tip">请从左侧选择角色</div>
          <div v-else-if="selectedRole.is_system && selectedRole.code === 'ADMIN'" class="empty-tip">
            ADMIN 系统角色拥有全部权限，不可修改
          </div>
          <div v-else>
            <el-tree
              ref="permTreeRef"
              :data="permissionTree"
              :props="treeProps"
              show-checkbox
              node-key="code"
              default-expand-all
              :default-checked-keys="checkedKeys"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户角色分配对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配用户角色" width="640px">
      <el-form :inline="true" size="small" @submit.prevent>
        <el-form-item label="用户ID">
          <el-input v-model="assignForm.userId" placeholder="输入用户ID" style="width: 160px;" />
        </el-form-item>
        <el-form-item>
          <el-button @click="loadUserRoles">查询当前角色</el-button>
        </el-form-item>
      </el-form>

      <div v-if="userCurrentRoles.length" class="current-roles">
        <span class="label">当前角色：</span>
        <el-tag
          v-for="r in userCurrentRoles"
          :key="r.role_id"
          closable
          :type="r.role_code === 'ADMIN' ? 'danger' : 'success'"
          style="margin-right: 6px;"
          @close="removeUserRole(r.role_id)"
        >
          {{ r.display_name }} ({{ r.role_code }})
        </el-tag>
      </div>

      <el-divider content-position="left">选择要分配的角色</el-divider>
      <el-checkbox-group v-model="assignForm.roleIds">
        <el-checkbox v-for="r in roles" :key="r.id" :label="r.id" style="display: block; margin-bottom: 8px;">
          {{ r.display_name }} ({{ r.code || r.name }})
          <span class="role-desc">{{ r.description }}</span>
        </el-checkbox>
      </el-checkbox-group>

      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assignLoading" @click="submitAssign">保存分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Star } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { usePermissionStore } from '@/stores/permission'

const permissionStore = usePermissionStore()

const roles = ref([])
const permissions = ref([])
const selectedRole = ref(null)
const checkedKeys = ref([])
const permTreeRef = ref(null)

const roleLoading = ref(false)
const saveLoading = ref(false)
const assignLoading = ref(false)

// 用户角色分配对话框
const assignDialogVisible = ref(false)
const assignForm = ref({ userId: '', roleIds: [] })
const userCurrentRoles = ref([])

const treeProps = { label: 'name', children: 'children' }

/** 是否可编辑角色权限（需 role:update 权限） */
const canEditRole = computed(() => permissionStore.hasPermission('role:update'))

/** 将权限列表按模块组织成树形结构 */
const permissionTree = computed(() => {
  const modules = {}
  for (const p of permissions.value) {
    if (!modules[p.module]) {
      modules[p.module] = {
        code: `${p.module}:*`,
        name: moduleLabel(p.module),
        children: [],
      }
    }
    modules[p.module].children.push({ code: p.code, name: `${p.action || ''} · ${p.name}` })
  }
  return Object.values(modules).sort((a, b) => a.name.localeCompare(b.name))
})

function moduleLabel(module) {
  const labels = {
    case: '接口用例',
    scenario: '测试场景',
    suite: '回归套件',
    environment: '环境配置',
    variable: '全局变量',
    mock: 'Mock 服务',
    schedule: '定时任务',
    audit: '审计日志',
    user: '用户管理',
    role: '角色管理',
  }
  return labels[module] || module
}

/** 加载角色列表 */
async function loadRoles() {
  roleLoading.value = true
  try {
    const res = await request.get('/admin/rbac/roles')
    roles.value = res || []
  } catch (e) {
    // 非 admin 用户会收到 403，静默处理
    roles.value = []
  } finally {
    roleLoading.value = false
  }
}

/** 加载所有权限 */
async function loadPermissions() {
  try {
    const res = await request.get('/admin/rbac/permissions')
    permissions.value = res || []
  } catch (e) {
    permissions.value = []
  }
}

async function loadAll() {
  await Promise.all([loadRoles(), loadPermissions()])
}

/** 选中角色时加载其权限 */
async function onRoleSelect(row) {
  if (!row) return
  selectedRole.value = row
  checkedKeys.value = []
  if (row.is_system && row.code === 'ADMIN') return
  try {
    const res = await request.get(`/admin/rbac/roles/${row.id}/permissions`)
    checkedKeys.value = (res || []).map((p) => p.code)
    // el-tree 需要在渲染后设置勾选
    setTimeout(() => {
      permTreeRef.value && permTreeRef.value.setCheckedKeys(checkedKeys.value)
    }, 50)
  } catch (e) {
    ElMessage.warning('加载角色权限失败')
  }
}

/** 保存角色权限 */
async function savePermissions() {
  if (!selectedRole.value || !permTreeRef.value) return
  const checked = permTreeRef.value.getCheckedKeys()
  const halfChecked = permTreeRef.value.getHalfCheckedKeys()
  // 过滤掉模块通配节点（以 :* 结尾），只提交具体权限码
  const codes = [...checked, ...halfChecked].filter((c) => !c.endsWith(':*'))
  saveLoading.value = true
  try {
    await request.put(`/admin/rbac/roles/${selectedRole.value.id}/permissions`, {
      permission_codes: codes,
    })
    ElMessage.success('权限保存成功')
  } catch (e) {
    ElMessage.error('权限保存失败：' + (e.message || ''))
  } finally {
    saveLoading.value = false
  }
}

function openAssignDialog() {
  if (!permissionStore.hasPermission('user:assign_role')) {
    ElMessage.warning('无分配角色权限（需要 user:assign_role）')
    return
  }
  assignForm.value = { userId: '', roleIds: [] }
  userCurrentRoles.value = []
  assignDialogVisible.value = true
}

/** 查询用户当前角色 */
async function loadUserRoles() {
  if (!assignForm.value.userId) {
    ElMessage.warning('请输入用户ID')
    return
  }
  try {
    const res = await request.get(`/admin/rbac/users/${assignForm.value.userId}/roles`)
    userCurrentRoles.value = res || []
    assignForm.value.roleIds = userCurrentRoles.value.map((r) => r.role_id)
  } catch (e) {
    userCurrentRoles.value = []
    ElMessage.error('查询用户角色失败')
  }
}

/** 提交用户角色分配 */
async function submitAssign() {
  if (!assignForm.value.userId) {
    ElMessage.warning('请输入用户ID')
    return
  }
  assignLoading.value = true
  try {
    await request.put(`/admin/rbac/users/${assignForm.value.userId}/roles`, {
      role_ids: assignForm.value.roleIds,
    })
    ElMessage.success('角色分配成功')
    await loadUserRoles()
  } catch (e) {
    ElMessage.error('角色分配失败：' + (e.message || ''))
  } finally {
    assignLoading.value = false
  }
}

/** 移除单个用户角色 */
async function removeUserRole(roleId) {
  try {
    await ElMessageBox.confirm('确认移除该用户的此角色？', '提示', { type: 'warning' })
  } catch {
    return
  }
  const newIds = assignForm.value.roleIds.filter((id) => id !== roleId)
  assignLoading.value = true
  try {
    await request.put(`/admin/rbac/users/${assignForm.value.userId}/roles`, { role_ids: newIds })
    ElMessage.success('已移除角色')
    await loadUserRoles()
  } catch (e) {
    ElMessage.error('移除失败：' + (e.message || ''))
  } finally {
    assignLoading.value = false
  }
}

onMounted(async () => {
  // 确保权限已加载（用于按钮控制）
  if (!permissionStore.loaded) {
    await permissionStore.fetchPermissions()
  }
  await loadAll()
})
</script>

<style scoped>
.rbac-manager {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-title {
  margin: 0 0 6px 0;
  font-size: 20px;
}
.page-subtitle {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}
.current-roles {
  margin-bottom: 12px;
}
.current-roles .label {
  color: #606266;
  font-size: 13px;
}
.role-desc {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}
</style>
