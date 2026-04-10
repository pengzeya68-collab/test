<template>
  <div class="learning-path-page">
    <el-page-header content="学习路径管理" />
    
    <!-- 操作栏 -->
    <div class="action-bar">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="10">
          <el-input
            v-model="searchQuery"
            placeholder="搜索路径名称/描述"
            prefix-icon="Search"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-select v-model="levelFilter" placeholder="难度等级筛选" clearable>
            <el-option label="入门" value="beginner" />
            <el-option label="进阶" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增路径
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- 路径卡片列表 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" v-for="item in pathList" :key="item.id">
        <el-card shadow="hover" class="path-card">
          <template #header>
            <div class="card-header">
              <span>{{ item.title }}</span>
              <el-tag :type="getLevelTag(item.level)" size="small">
                {{ item.levelText }}
              </el-tag>
            </div>
          </template>
          
          <div class="path-desc">{{ item.description }}</div>
          
          <el-divider />
          
          <div class="path-stats">
            <div class="stat-item">
              <span class="label">习题数：</span>
              <span class="value">{{ item.exerciseCount }}</span>
            </div>
            <div class="stat-item">
              <span class="label">学习人数：</span>
              <span class="value">{{ item.learnCount }}</span>
            </div>
            <div class="stat-item">
              <span class="label">完成率：</span>
              <span class="value">{{ item.completionRate }}%</span>
            </div>
          </div>
          
          <div class="progress-bar">
            <el-progress
              :percentage="item.completionRate"
              :stroke-width="6"
              :show-text="false"
            />
          </div>
          
          <template #footer>
            <div class="card-footer">
              <span class="create-time">创建于 {{ item.createTime }}</span>
              <div class="actions">
                <el-button
                  size="small"
                  type="primary"
                  @click="handleEdit(item)"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDelete(item)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[9, 18, 36]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="路径名称" prop="title">
          <el-input v-model="formData.title" placeholder="请输入路径名称" />
        </el-form-item>
        <el-form-item label="难度等级" prop="level">
          <el-radio-group v-model="formData.level">
            <el-radio value="beginner" label="beginner">入门</el-radio>
            <el-radio value="intermediate" label="intermediate">进阶</el-radio>
            <el-radio value="advanced" label="advanced">高级</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="路径描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入路径描述"
          />
        </el-form-item>
        <el-form-item label="封面图片" prop="cover">
          <el-input v-model="formData.cover" placeholder="请输入封面图片URL" />
        </el-form-item>
        <el-form-item label="选择习题">
          <el-transfer
            v-model="selectedExercises"
            :data="exerciseOptions"
            :titles="['可选习题', '已选习题']"
            :filterable="true"
            filter-placeholder="搜索习题"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { learningPathApi } from '@/admin/api'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const searchQuery = ref('')
const levelFilter = ref('')

// 分页
const pagination = reactive({
  page: 1,
  size: 9,
  total: 45
})

// 学习路径数据
const pathList = ref([
  {
    id: 1,
    title: 'JavaScript前端工程师入门',
    level: 'beginner',
    levelText: '入门',
    description: '从零基础开始学习JavaScript前端开发，掌握核心语法和常用API',
    cover: '',
    exerciseCount: 42,
    learnCount: 1234,
    completionRate: 78,
    createTime: '2026-03-01'
  },
  {
    id: 2,
    title: 'Vue3全栈开发进阶',
    level: 'intermediate',
    levelText: '进阶',
    description: '深入学习Vue3组合式API、Pinia状态管理和服务端渲染技术',
    cover: '',
    exerciseCount: 68,
    learnCount: 856,
    completionRate: 62,
    createTime: '2026-03-05'
  },
  {
    id: 3,
    title: '前端算法进阶指南',
    level: 'advanced',
    levelText: '高级',
    description: '系统学习前端常用算法，提升代码质量和性能优化能力',
    cover: '',
    exerciseCount: 56,
    learnCount: 423,
    completionRate: 35,
    createTime: '2026-03-10'
  }
])

// 习题选项（穿梭框数据）
const exerciseOptions = ref([
  { key: 1, label: 'JavaScript基础语法' },
  { key: 2, label: 'Vue3组合式API' },
  { key: 3, label: '两数之和算法题' },
  { key: 4, label: 'CSS布局技巧' },
  { key: 5, label: 'React状态管理' },
  { key: 6, label: 'TypeScript类型系统' },
  { key: 7, label: 'Node.js后端开发' },
  { key: 8, label: 'Webpack构建优化' }
])

const selectedExercises = ref([])

// 表单数据
const formRef = ref()
const formData = reactive({
  title: '',
  level: 'beginner',
  description: '',
  cover: ''
})

const formRules = {
  title: [
    { required: true, message: '请输入路径名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在2到50个字符', trigger: 'blur' }
  ],
  level: [
    { required: true, message: '请选择难度等级', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入路径描述', trigger: 'blur' },
    { max: 200, message: '描述不能超过200个字符', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑学习路径' : '新增学习路径')

const getLevelTag = (level) => {
  const map = {
    'beginner': 'success',
    'intermediate': 'warning',
    'advanced': 'danger'
  }
  return map[level] || 'info'
}

const handleSearch = async () => {
  loading.value = true
  try {
    // 调用搜索API
    // const res = await learningPathApi.list({
    //   page: pagination.page,
    //   size: pagination.size,
    //   keyword: searchQuery.value,
    //   level: levelFilter.value
    // })
    // pathList.value = res.data.list
    // pagination.total = res.data.total
    
    ElMessage.success('搜索完成')
  } catch (error) {
    ElMessage.error('搜索失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    title: '',
    level: 'beginner',
    description: '',
    cover: ''
  })
  selectedExercises.value = []
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  // 加载已选习题
  selectedExercises.value = [1, 2, 4]
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(
    `确定要删除学习路径「${row.title}」吗？删除后无法恢复！`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
  
  try {
    // 调用删除API
    // await learningPathApi.delete(row.id)
    
    const index = pathList.value.findIndex(item => item.id === row.id)
    if (index > -1) {
      pathList.value.splice(index, 1)
    }
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败，请稍后重试')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      
      try {
        if (isEdit.value) {
          // 调用编辑API
          // await learningPathApi.update(formData.id, {
          //   ...formData,
          //   exerciseIds: selectedExercises.value
          // })
          
          const index = pathList.value.findIndex(item => item.id === formData.id)
          if (index > -1) {
            pathList.value[index] = { 
              ...pathList.value[index], 
              ...formData, 
              exerciseCount: selectedExercises.value.length 
            }
          }
          ElMessage.success('编辑成功')
        } else {
          // 调用新增API
          // const res = await learningPathApi.create({
          //   ...formData,
          //   exerciseIds: selectedExercises.value
          // })
          
          const levelMap = {
            'beginner': '入门',
            'intermediate': '进阶',
            'advanced': '高级'
          }
          
          const newItem = {
            ...formData,
            id: pathList.value.length + 1,
            levelText: levelMap[formData.level],
            exerciseCount: selectedExercises.value.length,
            learnCount: 0,
            completionRate: 0,
            createTime: new Date().toISOString().slice(0, 10)
          }
          pathList.value.unshift(newItem)
          ElMessage.success('新增成功')
        }
        
        dialogVisible.value = false
      } catch (error) {
        ElMessage.error('操作失败，请稍后重试')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleSizeChange = (size) => {
  pagination.size = size
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.page = page
  handleSearch()
}
</script>

<style scoped lang="scss">
.learning-path-page {
  .action-bar {
    margin: 20px 0;
  }
  
  .path-card {
    margin-bottom: 20px;
    height: 320px;
    display: flex;
    flex-direction: column;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      font-size: 16px;
    }
    
    .path-desc {
      color: #606266;
      line-height: 1.6;
      height: 60px;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
    }
    
    .path-stats {
      margin: 10px 0;
      
      .stat-item {
        margin-bottom: 8px;
        font-size: 14px;
        
        .label {
          color: #909399;
        }
        
        .value {
          color: #303133;
          font-weight: 500;
        }
      }
    }
    
    .progress-bar {
      margin: 10px 0;
    }
    
    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 10px;
      border-top: 1px solid #ebeef5;
      
      .create-time {
        color: #909399;
        font-size: 12px;
      }
    }
  }
  
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
