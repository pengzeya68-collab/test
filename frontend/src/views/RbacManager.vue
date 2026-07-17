<template>
  <div class="rbac-manager">
    <div class="page-header">
      <div>
        <h2 class="page-title">馃洝锔?瑙掕壊鏉冮檺绠＄悊</h2>
        <p class="page-subtitle">鍩轰簬瑙掕壊鐨勮闂帶鍒讹紙RBAC锛夆€斺€旇鑹层€佹潈闄愩€佺敤鎴疯鑹插垎閰</p>
      </div>
      <div>
        <el-button type="primary" @click="openAssignDialog">鍒嗛厤鐢ㄦ埛瑙掕壊</el-button>
        <el-button @click="loadAll">鍒锋柊</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 宸︿晶锛氳鑹插垪琛?-->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>瑙掕壊鍒楄〃</span>
              <el-tag v-if="permissionStore.isAdmin" type="danger" size="small">绠＄悊鍛</el-tag>
            </div>
          </template>
          <el-table
            v-loading="roleLoading"
            :data="roles"
            highlight-current-row
            @current-change="onRoleSelect"
            size="small"
          >
            <el-table-column prop="display_name" label="瑙掕壊" min-width="100" />
            <el-table-column prop="code" label="浠ｇ爜" min-width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_system ? 'warning' : 'info'">
                  {{ row.code || row.name }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="绯荤粺" width="60" align="center">
              <template #default="{ row }">
                <el-icon v-if="row.is_system" color="#E6A23C"><Star /></el-icon>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="roles.length === 0 && !roleLoading" class="empty-tip">鏆傛棤瑙掕壊鏁版嵁</div>
        </el-card>
      </el-col>

      <!-- 鍙充晶锛氭潈闄愬垎閰?-->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>
                鏉冮檺鍒嗛厤
                <el-tag v-if="selectedRole" type="success" size="small" style="margin-left: 8px;">
                  {{ selectedRole.display_name }}
                </el-tag>
              </span>
              <div v-if="selectedRole && canEditRole">
                <el-button type="primary" size="small" :loading="saveLoading" @click="savePermissions">
                  淇濆瓨鏉冮檺
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="!selectedRole" class="empty-tip">璇蜂粠宸︿晶閫夋嫨瑙掕壊</div>
          <div v-else-if="selectedRole.is_system && selectedRole.code === 'ADMIN'" class="empty-tip">
            ADMIN 绯荤粺瑙掕壊鎷ユ湁鍏ㄩ儴鏉冮檺锛屼笉鍙慨鏀?          </div>
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

    <!-- 鐢ㄦ埛瑙掕壊鍒嗛厤瀵硅瘽妗?-->
    <el-dialog v-model="assignDialogVisible" title="鍒嗛厤鐢ㄦ埛瑙掕壊" width="640px">
      <el-form :inline="true" size="small" @submit.prevent>
        <el-form-item label="鐢ㄦ埛ID">
          <el-input v-model="assignForm.userId" placeholder="杈撳叆鐢ㄦ埛ID" style="width: 160px;" />
        </el-form-item>
        <el-form-item>
          <el-button @click="loadUserRoles">鏌ヨ褰撳墠瑙掕壊</el-button>
        </el-form-item>
      </el-form>

      <div v-if="userCurrentRoles.length" class="current-roles">
        <span class="label">褰撳墠瑙掕壊锛</span>
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

      <el-divider content-position="left">閫夋嫨瑕佸垎閰嶇殑瑙掕壊</el-divider>
      <el-checkbox-group v-model="assignForm.roleIds">
        <el-checkbox v-for="r in roles" :key="r.id" :label="r.id" style="display: block; margin-bottom: 8px;">
          {{ r.display_name }} ({{ r.code || r.name }})
          <span class="role-desc">{{ r.description }}</span>
        </el-checkbox>
      </el-checkbox-group>

      <template #footer>
        <el-button @click="assignDialogVisible = false">鍙栨秷</el-button>
        <el-button type="primary" :loading="assignLoading" @click="submitAssign">淇濆瓨鍒嗛厤</el-button>
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

// 鐢ㄦ埛瑙掕壊鍒嗛厤瀵硅瘽妗?const assignDialogVisible = ref(false)
const assignForm = ref({ userId: '', roleIds: [] })
const userCurrentRoles = ref([])

const treeProps = { label: 'name', children: 'children' }

/** 鏄惁鍙紪杈戣鑹叉潈闄愶紙闇€ role:update 鏉冮檺锛?*/
const canEditRole = computed(() => permissionStore.hasPermission('role:update'))

/** 灏嗘潈闄愬垪琛ㄦ寜妯″潡缁勭粐鎴愭爲褰㈢粨鏋?*/
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
    modules[p.module].children.push({ code: p.code, name: `${p.action || ''} 路 ${p.name}` })
  }
  return Object.values(modules).sort((a, b) => a.name.localeCompare(b.name))
})

function moduleLabel(module) {
  const labels = {
    case: '鎺ュ彛鐢ㄤ緥',
    scenario: '娴嬭瘯鍦烘櫙',
    suite: '鍥炲綊濂椾欢',
    environment: '鐜閰嶇疆',
    variable: '鍏ㄥ眬鍙橀噺',
    mock: 'Mock 鏈嶅姟',
    schedule: '瀹氭椂浠诲姟',
    audit: '瀹¤鏃ュ織',
    user: '鐢ㄦ埛绠＄悊',
    role: '瑙掕壊绠＄悊',
  }
  return labels[module] || module
}

/** 鍔犺浇瑙掕壊鍒楄〃 */
async function loadRoles() {
  roleLoading.value = true
  try {
    const res = await request.get('/admin/rbac/roles')
    roles.value = res || []
  } catch (e) {
    // 非管理员用户可能收到 403，保持空列表即可。
    roles.value = []
  } finally {
    roleLoading.value = false
  }
}

/** 鍔犺浇鎵€鏈夋潈闄?*/
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

/** 閫変腑瑙掕壊鏃跺姞杞藉叾鏉冮檺 */
async function onRoleSelect(row) {
  if (!row) return
  selectedRole.value = row
  checkedKeys.value = []
  if (row.is_system && row.code === 'ADMIN') return
  try {
    const res = await request.get(`/admin/rbac/roles/${row.id}/permissions`)
    checkedKeys.value = (res || []).map((p) => p.code)
    // el-tree 需要在渲染后设置勾选状态。
    setTimeout(() => {
      permTreeRef.value && permTreeRef.value.setCheckedKeys(checkedKeys.value)
    }, 50)
  } catch (e) {
    ElMessage.warning('鍔犺浇瑙掕壊鏉冮檺澶辫触')
  }
}

/** 淇濆瓨瑙掕壊鏉冮檺 */
async function savePermissions() {
  if (!selectedRole.value || !permTreeRef.value) return
  const checked = permTreeRef.value.getCheckedKeys()
  const halfChecked = permTreeRef.value.getHalfCheckedKeys()
  // 杩囨护鎺夋ā鍧楅€氶厤鑺傜偣锛堜互 :* 缁撳熬锛夛紝鍙彁浜ゅ叿浣撴潈闄愮爜
  const codes = [...checked, ...halfChecked].filter((c) => !c.endsWith(':*'))
  saveLoading.value = true
  try {
    await request.put(`/admin/rbac/roles/${selectedRole.value.id}/permissions`, {
      permission_codes: codes,
    })
    ElMessage.success('鏉冮檺淇濆瓨鎴愬姛')
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

/** 鏌ヨ鐢ㄦ埛褰撳墠瑙掕壊 */
async function loadUserRoles() {
  if (!assignForm.value.userId) {
    ElMessage.warning('请输入用户 ID')
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

/** 鎻愪氦鐢ㄦ埛瑙掕壊鍒嗛厤 */
async function submitAssign() {
  if (!assignForm.value.userId) {
    ElMessage.warning('请输入用户 ID')
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

/** 绉婚櫎鍗曚釜鐢ㄦ埛瑙掕壊 */
async function removeUserRole(roleId) {
  try {
    await ElMessageBox.confirm('确认移除该用户的此角色吗？', '提示', { type: 'warning' })
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
  // 确保权限已加载，用于按钮权限控制。
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

