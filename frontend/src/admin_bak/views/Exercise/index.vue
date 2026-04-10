<template>
  <div class="exercise-manage-page">
    <el-page-header content="习题管理" />
    
    <!-- 操作栏 -->
    <div class="action-bar">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索习题标题/ID"
            prefix-icon="Search"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-select v-model="difficultyFilter" placeholder="难度筛选" clearable>
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-select v-model="categoryFilter" placeholder="分类筛选" clearable>
            <el-option label="JavaScript" value="javascript" />
            <el-option label="Vue" value="vue" />
            <el-option label="React" value="react" />
            <el-option label="算法" value="algorithm" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="4">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增习题
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- 表格 -->
    <el-card shadow="hover">
      <el-table
        :data="tableData"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="习题标题" min-width="200" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="difficulty" label="难度" width="100">
          <template #default="scope">
            <el-tag :type="getDifficultyTag(scope.row.difficulty)">
              {{ scope.row.difficulty }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="分值" width="80" />
        <el-table-column prop="passRate" label="通过率" width="100">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.passRate"
              :stroke-width="8"
              :show-text="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column prop="updateTime" label="更新时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="warning"
              @click="handlePreview(scope.row)"
            >
              预览
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
    
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
        <el-form-item label="习题标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入习题标题" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="formData.category" placeholder="请选择分类">
            <el-option label="JavaScript" value="javascript" />
            <el-option label="Vue" value="vue" />
            <el-option label="React" value="react" />
            <el-option label="算法" value="algorithm" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-radio-group v-model="formData.difficulty">
            <el-radio value="简单" label="简单">简单</el-radio>
            <el-radio value="中等" label="中等">中等</el-radio>
            <el-radio value="困难" label="困难">困难</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="分值" prop="score">
          <el-input-number v-model="formData.score" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="习题内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="8"
            placeholder="请输入习题内容，支持Markdown"
          />
        </el-form-item>
        <el-form-item label="参考答案" prop="answer">
          <el-input
            v-model="formData.answer"
            type="textarea"
            :rows="6"
            placeholder="请输入参考答案"
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
    
    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      title="习题预览"
      width="800px"
    >
      <div class="preview-content">
        <h3>{{ previewData.title }}</h3>
        <el-tag :type="getDifficultyTag(previewData.difficulty)" class="mb-2">
          {{ previewData.difficulty }}
        </el-tag>
        <el-tag type="info" class="mb-2 ml-2">{{ previewData.category }}</el-tag>
        <div class="content mt-4" v-html="previewData.content"></div>
        <el-divider />
        <h4>参考答案：</h4>
        <div class="answer" v-html="previewData.answer"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { exerciseApi } from '@/admin/api'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const previewVisible = ref(false)
const isEdit = ref(false)

const searchQuery = ref('')
const difficultyFilter = ref('')
const categoryFilter = ref('')

// 分页
const pagination = reactive({
  page: 1,
  size: 10,
  total: 42
})

// 表格数据
const tableData = ref([
  {
    id: 1,
    title: 'JavaScript基础语法',
    category: 'javascript',
    difficulty: '简单',
    score: 10,
    passRate: 85,
    createTime: '2026-03-10 10:00:00',
    updateTime: '2026-03-10 10:00:00',
    content: '请解释JavaScript中的变量提升是什么？',
    answer: '变量提升是JavaScript在执行前会先扫描代码，将变量和函数声明提升到作用域顶部的机制。'
  },
  {
    id: 2,
    title: 'Vue3组合式API',
    category: 'vue',
    difficulty: '中等',
    score: 20,
    passRate: 65,
    createTime: '2026-03-11 14:30:00',
    updateTime: '2026-03-12 09:15:00',
    content: '请说明Vue3中setup函数的作用和使用方式。',
    answer: 'setup是Vue3组合式API的入口，在组件创建之前执行，返回的内容会暴露给模板和组件实例。'
  },
  {
    id: 3,
    title: '两数之和算法题',
    category: 'algorithm',
    difficulty: '困难',
    score: 30,
    passRate: 42,
    createTime: '2026-03-12 11:20:00',
    updateTime: '2026-03-12 11:20:00',
    content: '给定一个整数数组nums和一个目标值target，请找出和为目标值的两个整数的下标。',
    answer: '可以使用哈希表来存储遍历过的元素，时间复杂度O(n)，空间复杂度O(n)。'
  }
])

// 表单数据
const formRef = ref()
const formData = reactive({
  title: '',
  category: '',
  difficulty: '简单',
  score: 10,
  content: '',
  answer: ''
})

const formRules = {
  title: [
    { required: true, message: '请输入习题标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在2到100个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  difficulty: [
    { required: true, message: '请选择难度', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入习题内容', trigger: 'blur' }
  ],
  answer: [
    { required: true, message: '请输入参考答案', trigger: 'blur' }
  ]
}

const previewData = ref({
  title: '',
  difficulty: '',
  category: '',
  content: '',
  answer: ''
})

const dialogTitle = computed(() => isEdit.value ? '编辑习题' : '新增习题')

const getDifficultyTag = (difficulty) => {
  const map = {
    '简单': 'success',
    '中等': 'warning',
    '困难': 'danger'
  }
  return map[difficulty] || 'info'
}

const handleSearch = async () => {
  loading.value = true
  try {
    // 调用搜索API
    // const res = await exerciseApi.list({
    //   page: pagination.page,
    //   size: pagination.size,
    //   keyword: searchQuery.value,
    //   difficulty: difficultyFilter.value,
    //   category: categoryFilter.value
    // })
    // tableData.value = res.data.list
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
    category: '',
    difficulty: '简单',
    score: 10,
    content: '',
    answer: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handlePreview = (row) => {
  Object.assign(previewData.value, row)
  previewVisible.value = true
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(
    `确定要删除习题「${row.title}」吗？删除后无法恢复！`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
  
  try {
    // 调用删除API
    // await exerciseApi.delete(row.id)
    
    const index = tableData.value.findIndex(item => item.id === row.id)
    if (index > -1) {
      tableData.value.splice(index, 1)
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
          // await exerciseApi.update(formData.id, formData)
          
          const index = tableData.value.findIndex(item => item.id === formData.id)
          if (index > -1) {
            tableData.value[index] = { ...tableData.value[index], ...formData, updateTime: new Date().toISOString().slice(0, 19).replace('T', ' ') }
          }
          ElMessage.success('编辑成功')
        } else {
          // 调用新增API
          // const res = await exerciseApi.create(formData)
          
          const newItem = {
            ...formData,
            id: tableData.value.length + 1,
            passRate: 0,
            createTime: new Date().toISOString().slice(0, 19).replace('T', ' '),
            updateTime: new Date().toISOString().slice(0, 19).replace('T', ' ')
          }
          tableData.value.unshift(newItem)
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
.exercise-manage-page {
  .action-bar {
    margin: 20px 0;
  }
  
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
  
  .preview-content {
    .content, .answer {
      white-space: pre-wrap;
      line-height: 1.8;
    }
  }
}
</style>
