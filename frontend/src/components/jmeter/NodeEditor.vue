<template>
  <div class="panel editor-panel" style="flex:1;min-width:0">
    <div class="panel-title">
      <span>✏️ {{ selectedNode ? selectedNode.name : '元素编辑器' }}</span>
      <el-tag v-if="selectedNode" size="small">{{ NODE_TYPES[selectedNode.type]?.label || selectedNode.type }}</el-tag>
    </div>
    <div class="editor-body" v-if="selectedNode">
      <!-- 测试计划 -->
      <template v-if="selectedNode.type === 'TestPlan'">
        <div class="form-section">
          <div class="form-group"><label>测试计划名称</label><el-input v-model="selectedNode.name" /></div>
          <div class="form-group"><label>用户定义变量</label>
            <div v-for="(v, vi) in (selectedNode.props.variables || [])" :key="vi" class="kv-row">
              <el-input v-model="v.name" placeholder="变量名" size="small" style="width:42%" />
              <el-input v-model="v.value" placeholder="值" size="small" style="width:42%" />
              <el-button link size="small" type="danger" @click="selectedNode.props.variables.splice(vi,1)">×</el-button>
            </div>
            <el-button size="small" @click="$emit('addVar')">+ 添加变量</el-button>
          </div>
        </div>
      </template>

      <!-- 线程组 -->
      <template v-if="selectedNode.type === 'ThreadGroup'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 虚拟用户数 = 模拟多少人同时访问；Ramp-Up = 多少秒内逐步启动完；持续时间 = 总共跑多久</div>
          <div class="form-group"><label>线程组名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-row">
            <div class="form-group"><label>并发线程数</label><el-tooltip content="模拟多少个用户同时访问系统，50 = 50个虚拟用户" placement="top"><el-input-number v-model="selectedNode.props.threads" :min="1" :max="10000" size="small" /></el-tooltip></div>
            <div class="form-group"><label>Ramp-Up (秒)</label><el-tooltip content="多少秒内逐步启动完所有用户。5秒=5秒内逐步启动50个用户" placement="top"><el-input-number v-model="selectedNode.props.rampUp" :min="0" :max="3600" size="small" /></el-tooltip></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>循环次数</label><el-tooltip content="每个用户跑完一遍后重复跑的次数。1=每人只跑1遍" placement="top"><el-input-number v-model="selectedNode.props.loops" :min="1" :max="99999" size="small" /></el-tooltip></div>
            <div class="form-group"><label>持续时间 (秒)</label><el-tooltip content="设置后循环次数不生效，到时间自动停止。60=跑60秒" placement="top"><el-input-number v-model="selectedNode.props.duration" :min="0" :max="86400" size="small" /></el-tooltip></div>
          </div>
          <el-alert v-if="selectedNode.props.loops >= 99999 && !selectedNode.props.duration"
            title="⚠️ 此脚本将永久循环运行！请设置持续时间" type="error" :closable="false" show-icon />
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><Monitor /></el-icon> 监听器用于查看测试结果，建议添加「查看结果树」和「聚合报告」</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <el-button size="small" @click="$emit('addChildToCurrent', 'HttpSampler')">🌐 HTTP 请求</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'ViewResultsTree')">👁️ 查看结果树</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'SummaryReport')">📈 聚合报告</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'AggregateReport')">📊 聚合报告(高级)</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'ResponseTimeGraph')">📉 响应时间图</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'CSVDataSet')">📄 CSV 数据源</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'JDBCSampler')">🗄️ JDBC 请求</el-button>
          </div>
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><Lollipop /></el-icon> 逻辑控制器：控制请求的执行顺序和条件</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <el-button size="small" @click="$emit('addChildToCurrent', 'IfController')">🔀 如果控制器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'LoopController')">🔄 循环控制器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'WhileController')">🔁 While 控制器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'TransactionController')">📦 事务控制器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'ThroughputController')">⏱️ 吞吐量控制器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'OnceOnlyController')">1️⃣ 仅一次控制器</el-button>
          </div>
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><Setting /></el-icon> 配置元件：全局设置 HTTP 默认值、请求头、Cookie 等</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <el-button size="small" @click="$emit('addChildToCurrent', 'HTTPRequestDefaults')">🎯 HTTP 请求默认值</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'HTTPHeaderManager')">📨 HTTP 信息头管理器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'HTTPCookieManager')">🍪 HTTP Cookie 管理器</el-button>
          </div>
        </div>
      </template>

      <!-- HTTP 请求 -->
      <template v-if="selectedNode.type === 'HttpSampler'">
        <div class="form-section">
          <div class="section-hint"><el-icon><Connection /></el-icon> 配置要压测的接口：选择方法、填写地址、添加请求头和请求体</div>
          <div class="form-group"><label>请求名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-row">
            <div class="form-group" style="flex:0 0 120px"><label>方法</label>
              <el-select v-model="selectedNode.props.method" size="small">
                <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" />
              </el-select>
            </div>
            <div class="form-group" style="flex:1"><label>URL</label><el-input v-model="selectedNode.props.url" size="small" placeholder="https://api.example.com/users" /></div>
          </div>
          <el-collapse>
            <el-collapse-item title="请求头 (Headers)" name="headers">
              <div class="section-hint" style="margin-bottom:6px">添加请求头，如 Content-Type: application/json、Authorization: Bearer xxx</div>
              <div v-for="(h, hi) in (selectedNode.props.headers || [])" :key="hi" class="kv-row">
                <el-input v-model="h.key" placeholder="Header名" size="small" style="width:40%" />
                <el-input v-model="h.value" placeholder="值" size="small" style="width:50%" />
                <el-button link size="small" type="danger" @click="selectedNode.props.headers.splice(hi,1)">×</el-button>
              </div>
              <el-button size="small" @click="$emit('addHeader')">+ 添加请求头</el-button>
            </el-collapse-item>
            <el-collapse-item v-if="selectedNode.props.method !== 'GET'" title="请求体 (Body)" name="body">
              <div class="form-group"><label>Body 类型</label>
                <el-select v-model="selectedNode.props.bodyType" size="small">
                  <el-option v-for="b in ['none','json','form-data','x-www-form-urlencoded']" :key="b" :label="b" :value="b" />
                </el-select>
              </div>
              <el-input v-model="selectedNode.props.body" type="textarea" :rows="4" size="small" placeholder='{"key":"value"}' />
            </el-collapse-item>
          </el-collapse>
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><Coin /></el-icon> 断言：验证返回结果是否正确（点击展开更多类型）</div>
          <div style="display:flex;gap:4px;flex-wrap:wrap">
            <el-button size="small" @click="$emit('addChildToCurrent', 'ResponseAssertion')">✅ 响应断言</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'JsonAssertion')">📋 JSON 断言</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'DurationAssertion')">⏱️ 持续时间</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'BeanShellAssertion')">💻 BeanShell</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'JSR223Assertion')">🔥 JSR223</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'SizeAssertion')">📏 大小</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'XPathAssertion')">🗂️ XPath</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'CompareAssertion')">⚖️ 比较</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'XMLAssertion')">📜 XML</el-button>
          </div>
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><Coin /></el-icon> 提取器：从响应中提取数据传给下一个请求</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <el-button size="small" @click="$emit('addChildToCurrent', 'JsonExtractor')">📤 JSON 提取器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'RegexExtractor')">🔍 正则提取器</el-button>
          </div>
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><Coin /></el-icon> 定时器与处理器</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <el-button size="small" @click="$emit('addChildToCurrent', 'ConstantTimer')">⏰ 固定定时器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'UniformRandomTimer')">🎲 随机定时器</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'BeanShellPreProcessor')">⚙️ BeanShell前置</el-button>
            <el-button size="small" @click="$emit('addChildToCurrent', 'JSR223PreProcessor')">🔥 JSR223前置</el-button>
          </div>
        </div>
        <div class="form-section">
          <el-button type="primary" size="small" @click="$emit('debugRequest', selectedNode)" :loading="debugLoading">
            <el-icon><VideoPlay /></el-icon> 🐛 调试此请求
          </el-button>
          <el-button size="small" @click="$emit('saveSamplerToCase', selectedNode)" :loading="savingToCase">
            💾 保存到接口库
          </el-button>
        </div>
      </template>

      <!-- ===== 断言编辑器（支持7种断言类型+AI辅助） ===== -->
      <template v-if="selectedNode.type === 'ResponseAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>断言类型</label>
            <el-select v-model="selectedNode.props.assertType" size="small">
              <el-option label="状态码" value="status_code" />
              <el-option label="响应包含" value="contains" />
              <el-option label="响应匹配(正则)" value="matches" />
              <el-option label="JSON Path" value="jsonpath" />
              <el-option label="持续时间" value="duration" />
            </el-select>
          </div>
          <div class="form-group" v-if="selectedNode.props.assertType === 'status_code'"><label>期望状态码</label><el-input-number v-model="selectedNode.props.expected" :min="100" :max="599" size="small" /></div>
          <div class="form-group" v-if="selectedNode.props.assertType === 'contains' || selectedNode.props.assertType === 'matches'"><label>期望值</label><el-input v-model="selectedNode.props.expected" size="small" placeholder="200或success" /></div>
          <div class="form-group" v-if="selectedNode.props.assertType === 'jsonpath'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /><label style="margin-top:4px">期望值</label><el-input v-model="selectedNode.props.expected" size="small" /></div>
          <div class="form-group" v-if="selectedNode.props.assertType === 'duration'"><label>最大响应时间 (ms)</label><el-input-number v-model="selectedNode.props.maxDuration" :min="1" :max="60000" size="small" /></div>
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：状态码断言最常用，只需填期望的状态码如200。响应包含用于检查返回内容中是否有特定文字</div>
        </div>
      </template>

      <template v-if="selectedNode.type === 'JsonAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /></div>
          <div class="form-group"><label>期望值</label><el-input v-model="selectedNode.props.expected" placeholder="12345" size="small" /></div>
          <div class="form-row">
            <div class="form-group"><label>期望为null</label><el-switch v-model="selectedNode.props.expectNull" size="small" /></div>
            <div class="form-group"><label>取反</label><el-switch v-model="selectedNode.props.invert" size="small" /></div>
          </div>
        </div>
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：用于断言JSON响应中的某个字段值。例：$.data.status 期望值 "ok"</div>
          <el-button size="small" @click="$emit('aiGenerateAssert', 'Json')" :loading="aiGenerating" style="margin-top:4px">
            🤖 AI 帮写
          </el-button>
        </div>
      </template>

      <template v-if="selectedNode.type === 'DurationAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>最大响应时间 (ms)</label><el-input-number v-model="selectedNode.props.maxDuration" :min="1" :max="60000" size="small" /></div>
        </div>
        <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：如果接口响应太慢就报错。如设置1000ms=超过1秒就失败</div>
      </template>

      <!-- ===== BeanShell 断言（核心！） ===== -->
      <template v-if="selectedNode.type === 'BeanShellAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
        </div>
        <div class="section-hint assertion-teaching">
          <div class="teaching-title">📖 BeanShell 断言教学 — 小白也能写</div>
          <div class="teaching-body">
            <p><strong>什么是 BeanShell 断言？</strong> 用 Java 代码自定义判断规则，只要你会写 if/else 就能用</p>
            <p><strong>📌 核心变量速查：</strong></p>
            <table class="teaching-table">
              <tr><td><code>ResponseCode</code></td><td>HTTP 状态码（字符串），如 "200"</td></tr>
              <tr><td><code>ResponseMessage</code></td><td>HTTP 消息，如 "OK"</td></tr>
              <tr><td><code>ResponseData</code></td><td>响应体（字节数组），转字符串用 <code>new String(ResponseData)</code></td></tr>
              <tr><td><code>SampleResult</code></td><td>采样结果对象</td></tr>
              <tr><td><code>Failure</code></td><td>设为 <code>true</code> 表示断言失败</td></tr>
              <tr><td><code>FailureMessage</code></td><td>失败时的错误描述</td></tr>
              <tr><td><code>prev</code></td><td>等同于 SampleResult（类型: SampleResult）</td></tr>
            </table>
            <p><strong>📌 常用示例：</strong></p>
            <table class="teaching-table">
              <tr><td>状态码断言</td><td><code>if (!ResponseCode.equals("200")) { Failure=true; FailureMessage="状态码不是200"; }</code></td></tr>
              <tr><td>响应包含</td><td><code>if (!new String(ResponseData).contains("success")) { Failure=true; FailureMessage="响应无success"; }</code></td></tr>
              <tr><td>响应时间</td><td><code>if (prev.getTime() > 3000) { Failure=true; FailureMessage="超过3秒"; }</code></td></tr>
              <tr><td>JSON断言</td><td><code>import org.json.*; JSONObject j=new JSONObject(new String(ResponseData)); if (!j.has("token")) { Failure=true; FailureMessage="缺少token"; }</code></td></tr>
            </table>
          </div>
        </div>
        <div class="form-section">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
            <label>BeanShell 脚本</label>
            <div style="display:flex;gap:6px">
              <el-button size="small" type="warning" @click="$emit('aiValidateScript', 'BeanShell')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
              <el-button size="small" type="primary" @click="$emit('aiGenerateAssert', 'BeanShell')" :loading="aiGenerating" plain>
                🤖 AI 帮写断言
              </el-button>
            </div>
          </div>
          <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder="// 写你的断言逻辑..." size="small" style="font-family:Consolas,monospace;font-size:12px" />
        </div>
        <div class="form-row">
          <div class="form-group"><label>外部BeanShell文件</label><el-input v-model="selectedNode.props.filename" placeholder="可选" size="small" /></div>
          <div class="form-group"><label>参数</label><el-input v-model="selectedNode.props.parameters" placeholder="可选" size="small" /></div>
        </div>
        <div class="form-group"><label>每次重置解释器</label><el-switch v-model="selectedNode.props.resetInterpreter" size="small" /></div>
        <div class="form-section" v-if="projectVariables.length > 0">
          <div class="vars-panel">
            <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
            <div class="vars-chips">
              <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="$emit('insertVariable', v.name)" :title="v.source">{{ v.name }}</span>
            </div>
          </div>
        </div>
        <div class="form-section" v-if="aiValidationResult">
          <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
            <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
            <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
          </div>
        </div>
      </template>

      <!-- ===== JSR223 断言 ===== -->
      <template v-if="selectedNode.type === 'JSR223Assertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>脚本语言</label>
            <el-select v-model="selectedNode.props.language" size="small">
              <el-option label="Groovy（推荐，性能最好）" value="groovy" />
              <el-option label="JavaScript" value="javascript" />
              <el-option label="Python (Jython)" value="python" />
              <el-option label="BeanShell" value="beanshell" />
            </el-select>
          </div>
        </div>
        <div class="section-hint assertion-teaching">
          <div class="teaching-title">📖 JSR223 断言教学</div>
          <div class="teaching-body">
            <p><strong>推荐用 Groovy</strong>，比 BeanShell 快 10 倍。核心变量：</p>
            <table class="teaching-table">
              <tr><td><code>prev</code></td><td>SampleResult，可调用 getResponseDataAsString()、getTime()等</td></tr>
              <tr><td><code>log</code></td><td>日志对象，log.info("xxx") 打印日志</td></tr>
              <tr><td><code>AssertionResult</code></td><td>断言结果，.setFailure(true) 标记失败</td></tr>
            </table>
          </div>
        </div>
        <div class="form-section">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
            <label>脚本代码</label>
            <div style="display:flex;gap:6px">
              <el-button size="small" type="warning" @click="$emit('aiValidateScript', 'JSR223')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
              <el-button size="small" type="primary" @click="$emit('aiGenerateAssert', 'JSR223')" :loading="aiGenerating" plain>
                🤖 AI 帮写断言
              </el-button>
            </div>
          </div>
          <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder='// Groovy脚本...' size="small" style="font-family:Consolas,monospace;font-size:12px" />
        </div>
        <div class="form-section" v-if="projectVariables.length > 0">
          <div class="vars-panel">
            <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
            <div class="vars-chips">
              <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="$emit('insertVariable', v.name)" :title="v.source">{{ v.name }}</span>
            </div>
          </div>
        </div>
        <div class="form-section" v-if="aiValidationResult">
          <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
            <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
            <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
          </div>
        </div>
      </template>

      <!-- ===== 响应大小断言 ===== -->
      <template v-if="selectedNode.type === 'SizeAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-row">
            <div class="form-group">
              <label>比较方式</label>
              <el-select v-model="selectedNode.props.operator" size="small">
                <el-option label="响应大小 &gt; 指定值" value=">" />
                <el-option label="响应大小 &lt; 指定值" value="<" />
                <el-option label="响应大小 = 指定值" value="=" />
                <el-option label="响应大小 ≠ 指定值" value="≠" />
              </el-select>
            </div>
            <div class="form-group"><label>大小 (字节)</label><el-input-number v-model="selectedNode.props.size" :min="1" :max="99999999" size="small" /></div>
          </div>
        </div>
        <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：检查响应体大小。如 &gt; 5000 字节 → 确保接口返回了足够的数据</div>
      </template>

      <!-- ===== XPath 断言 ===== -->
      <template v-if="selectedNode.type === 'XPathAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>XPath 表达式</label><el-input v-model="selectedNode.props.xpath" placeholder="/html/body/h1 或 //result[@status='ok']" size="small" /></div>
          <div class="form-group"><label>取反（不存在才通过）</label><el-switch v-model="selectedNode.props.negate" size="small" /></div>
        </div>
        <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：用于断言XML/HTML响应中某个节点存在。如 //result[@status='ok'] 表示检查是否存在status为ok的result节点</div>
      </template>

      <!-- ===== 比较断言 ===== -->
      <template v-if="selectedNode.type === 'CompareAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>检查范围</label>
            <el-select v-model="selectedNode.props.testField" size="small">
              <el-option label="响应数据" value="Assertion.response_data" />
              <el-option label="响应代码" value="Assertion.response_code" />
              <el-option label="响应消息" value="Assertion.response_message" />
              <el-option label="请求头" value="Assertion.response_headers" />
              <el-option label="URL" value="Assertion.sample_label" />
            </el-select>
          </div>
          <div class="form-group"><label>比较规则</label>
            <el-select v-model="selectedNode.props.compareType" size="small">
              <el-option label="包含" value="contains" />
              <el-option label="等于" value="==" />
              <el-option label="匹配(正则)" value="matches" />
              <el-option label="不等于" value="≠" />
              <el-option label="子串" value="substring" />
            </el-select>
          </div>
          <div class="form-group"><label>期望值</label><el-input v-model="selectedNode.props.expected" placeholder="要匹配的值" size="small" /></div>
        </div>
        <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：灵活的比较断言，可以选择检查响应体/状态码/请求头等不同部位</div>
      </template>

      <!-- ===== XML 断言 ===== -->
      <template v-if="selectedNode.type === 'XMLAssertion'">
        <div class="form-section">
          <div class="form-group"><label>断言名称</label><el-input v-model="selectedNode.name" size="small" /></div>
        </div>
        <div class="section-hint"><el-icon><InfoFilled /></el-icon> 💡 小白提示：自动验证响应体是否为合法XML。如果接口返回XML格式数据，加上这个断言确保格式正确</div>
      </template>
      <template v-if="selectedNode.type === 'RegexExtractor' || selectedNode.type === 'JsonExtractor'">
        <div class="form-section">
          <div class="form-group"><label>提取器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>变量名</label><el-input v-model="selectedNode.props.varName" placeholder="token" size="small" /></div>
          <div class="form-hint">后续请求中用 <code>{'{'+'$'+'{'+'}'+'}变量名'}</code> 引用</div>
          <div class="form-group" v-if="selectedNode.type === 'RegexExtractor'"><label>正则表达式</label><el-input v-model="selectedNode.props.regex" placeholder='"token":"(.*?)"' size="small" /></div>
          <div class="form-group" v-if="selectedNode.type === 'JsonExtractor'"><label>JSON Path</label><el-input v-model="selectedNode.props.jsonPath" placeholder="$.data.token" size="small" /></div>
          <div class="form-group"><label>默认值</label><el-input v-model="selectedNode.props.defaultValue" placeholder="NOT_FOUND" size="small" /></div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'ConstantTimer'">
        <div class="form-section"><div class="form-group"><label>延迟 (毫秒)</label><el-input-number v-model="selectedNode.props.delay" :min="0" :max="60000" size="small" /></div></div>
      </template>
      <template v-if="selectedNode.type === 'UniformRandomTimer'">
        <div class="form-section"><div class="form-row"><div class="form-group"><label>最小延迟 (ms)</label><el-input-number v-model="selectedNode.props.minDelay" :min="0" size="small" /></div><div class="form-group"><label>最大延迟 (ms)</label><el-input-number v-model="selectedNode.props.maxDelay" :min="1" size="small" /></div></div></div>
      </template>
      <template v-if="selectedNode.type === 'GaussianRandomTimer'">
        <div class="form-section"><div class="form-row"><div class="form-group"><label>偏差 (ms)</label><el-input-number v-model="selectedNode.props.deviation" :min="0" :max="60000" size="small" /></div><div class="form-group"><label>偏移 (ms)</label><el-input-number v-model="selectedNode.props.offset" :min="0" :max="60000" size="small" /></div></div></div>
      </template>
      <template v-if="selectedNode.type === 'SyncTimer'">
        <div class="form-section"><div class="form-group"><label>集合点并发数</label><el-input-number v-model="selectedNode.props.groupSize" :min="2" :max="10000" size="small" /></div></div>
      </template>
      <template v-if="selectedNode.type === 'CSVDataSet'">
        <div class="form-section">
          <div class="form-group"><label>CSV 文件名</label><el-input v-model="selectedNode.props.filename" placeholder="users.csv" size="small" /></div>
          <div class="form-group"><label>变量名 (逗号分隔)</label><el-input v-model="selectedNode.props.variableNames" placeholder="username,password" size="small" /></div>
          <div class="form-row"><div class="form-group"><label>分隔符</label><el-input v-model="selectedNode.props.delimiter" size="small" style="width:60px" /></div><div class="form-group"><label>循环</label><el-switch v-model="selectedNode.props.recycle" size="small" /></div></div>
          <div class="form-group"><label>CSV 内容 (随 .jmx 导出)</label><el-input v-model="selectedNode.props.csvContent" type="textarea" :rows="4" placeholder="username,password&#10;user1,pass1" size="small" /></div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'JDBCConnection'">
        <div class="form-section">
          <div class="form-group"><label>连接名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>数据库 URL</label><el-input v-model="selectedNode.props.dbUrl" placeholder="jdbc:mysql://host:port/db" size="small" /></div>
          <div class="form-row"><div class="form-group"><label>驱动类</label><el-input v-model="selectedNode.props.driver" placeholder="com.mysql.cj.jdbc.Driver" size="small" /></div><div class="form-group"><label>用户名</label><el-input v-model="selectedNode.props.dbUser" size="small" /></div></div>
          <div class="form-group"><label>密码</label><el-input v-model="selectedNode.props.dbPass" type="password" size="small" show-password /></div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'JDBCSampler'">
        <div class="form-section"><div class="form-group"><label>SQL 查询</label><el-input v-model="selectedNode.props.sql" type="textarea" :rows="3" placeholder="SELECT * FROM users WHERE status = 'active'" size="small" /></div></div>
      </template>
      <template v-if="selectedNode.type === 'BeanShellPreProcessor' || selectedNode.type === 'BeanShellPostProcessor'">
        <div class="form-section">
          <div class="form-group"><label>脚本名称</label><el-input v-model="selectedNode.name" size="small" /></div>
        </div>
        <div class="section-hint assertion-teaching">
          <div class="teaching-title">📖 BeanShell {{ selectedNode.type === 'BeanShellPreProcessor' ? '前置' : '后置' }}处理器教学</div>
          <div class="teaching-body">
            <p><strong>{{ selectedNode.type === 'BeanShellPreProcessor' ? '前置处理器' : '后置处理器' }}是什么？</strong> {{ selectedNode.type === 'BeanShellPreProcessor' ? '在请求发送前执行，用于修改请求参数、添加签名等' : '在请求返回后执行，用于提取数据、修改变量等' }}</p>
            <p><strong>📌 核心变量速查：</strong></p>
            <table class="teaching-table">
              <tr><td><code>vars</code></td><td>JMeter变量字典，vars.put("k","v") 存 / vars.get("k") 取</td></tr>
              <tr><td><code>prev</code></td><td>上一个采样结果（后置可用），prev.getResponseDataAsString()</td></tr>
              <tr><td><code>log</code></td><td>日志对象，log.info("xxx") 打印日志</td></tr>
              <tr><td><code>ctx</code></td><td>JMeter上下文，ctx.getCurrentSampler() 获取当前采样器</td></tr>
              <tr v-if="selectedNode.type === 'BeanShellPostProcessor'"><td><code>ResponseData</code></td><td>响应体字节数组，new String(ResponseData) 转字符串</td></tr>
              <tr v-if="selectedNode.type === 'BeanShellPostProcessor'"><td><code>ResponseCode</code></td><td>HTTP状态码，如 "200"</td></tr>
            </table>
          </div>
        </div>
        <div class="form-section">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
            <label>BeanShell 脚本</label>
            <div style="display:flex;gap:6px">
              <el-button size="small" type="warning" @click="$emit('aiValidateScript', 'BeanShell')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
              <el-button size="small" type="primary" @click="$emit('aiGenerateAssert', 'BeanShellProcessor')" :loading="aiGenerating" plain>🤖 AI 帮写</el-button>
            </div>
          </div>
          <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder='long ts = System.currentTimeMillis(); vars.put("ts",String.valueOf(ts));' size="small" style="font-family:Consolas,monospace;font-size:12px" />
        </div>
        <div class="form-section" v-if="projectVariables.length > 0">
          <div class="vars-panel">
            <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
            <div class="vars-chips">
              <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="$emit('insertVariable', v.name)" :title="v.source">{{ v.name }}</span>
            </div>
          </div>
        </div>
        <div class="form-section" v-if="aiValidationResult">
          <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
            <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
            <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'JSR223PreProcessor' || selectedNode.type === 'JSR223PostProcessor'">
        <div class="form-section">
          <div class="form-group"><label>脚本名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>脚本语言</label>
            <el-select v-model="selectedNode.props.language" size="small">
              <el-option label="Groovy（推荐，性能最好）" value="groovy" />
              <el-option label="JavaScript" value="javascript" />
              <el-option label="Python (Jython)" value="python" />
              <el-option label="BeanShell" value="beanshell" />
            </el-select>
          </div>
        </div>
        <div class="section-hint assertion-teaching">
          <div class="teaching-title">📖 JSR223 {{ selectedNode.type === 'JSR223PreProcessor' ? '前置' : '后置' }}处理器教学</div>
          <div class="teaching-body">
            <p><strong>推荐用 Groovy</strong>，比 BeanShell 快 10 倍。核心变量：</p>
            <table class="teaching-table">
              <tr><td><code>vars</code></td><td>JMeter变量字典，vars.put("k","v") / vars.get("k")</td></tr>
              <tr><td><code>prev</code></td><td>SampleResult，可调用 getResponseDataAsString()、getTime()</td></tr>
              <tr><td><code>log</code></td><td>日志对象，log.info("xxx")</td></tr>
              <tr><td><code>ctx</code></td><td>JMeter上下文</td></tr>
              <tr><td><code>out</code></td><td>System.out，调试用</td></tr>
            </table>
          </div>
        </div>
        <div class="form-section">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
            <label>脚本代码</label>
            <div style="display:flex;gap:6px">
              <el-button size="small" type="warning" @click="$emit('aiValidateScript', 'JSR223')" :loading="aiValidating" plain>🔍 AI 校验</el-button>
              <el-button size="small" type="primary" @click="$emit('aiGenerateAssert', 'JSR223Processor')" :loading="aiGenerating" plain>🤖 AI 帮写</el-button>
            </div>
          </div>
          <el-input v-model="selectedNode.props.script" type="textarea" :rows="8" placeholder='def ts = System.currentTimeMillis(); vars.put("ts", ts.toString())' size="small" style="font-family:Consolas,monospace;font-size:12px" />
        </div>
        <div class="form-section" v-if="projectVariables.length > 0">
          <div class="vars-panel">
            <div class="vars-panel-title">🔗 项目可用变量（点击插入）</div>
            <div class="vars-chips">
              <span v-for="v in projectVariables" :key="v.name" class="var-chip" @click="$emit('insertVariable', v.name)" :title="v.source">{{ v.name }}</span>
            </div>
          </div>
        </div>
        <div class="form-section" v-if="aiValidationResult">
          <div class="ai-validation" :class="aiValidationResult.ok ? 'ai-validation-ok' : 'ai-validation-err'">
            <div class="ai-validation-header">{{ aiValidationResult.ok ? '✅ 校验通过' : '⚠️ 发现问题' }}</div>
            <div class="ai-validation-body">{{ aiValidationResult.message }}</div>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'IfController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 条件成立时才执行子元素。如 <code>${JMeterThread.last_sample_ok}</code> 表示上一个请求成功才执行</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>条件表达式</label><el-input v-model="selectedNode.props.condition" size="small" placeholder="${JMeterThread.last_sample_ok}" /></div>
          <div class="form-row">
            <div class="form-group"><label>解释为变量表达式</label><el-switch v-model="selectedNode.props.useExpression" size="small" /></div>
            <div class="form-group"><label>对所有子级求值</label><el-switch v-model="selectedNode.props.evaluateAll" size="small" /></div>
          </div>
          <div class="form-group"><label>添加子元素到控制器中</label>
            <div style="display:flex;gap:4px;flex-wrap:wrap">
              <el-button size="small" @click="$emit('addChildToCurrent', 'HttpSampler')">🌐 HTTP 请求</el-button>
              <el-button size="small" @click="$emit('addChildToCurrent', 'LoopController')">🔄 循环</el-button>
              <el-button size="small" @click="$emit('addChildToCurrent', 'IfController')">🔀 如果</el-button>
            </div>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'LoopController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 将子元素重复执行指定次数。如循环 3 次 = 子元素执行 3 遍</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-row">
            <div class="form-group"><label>循环次数</label><el-input-number v-model="selectedNode.props.loops" :min="1" :max="99999" size="small" /></div>
            <div class="form-group"><label>永久循环</label><el-switch v-model="selectedNode.props.forever" size="small" /></div>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'WhileController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 条件为真时不断循环子元素。如 <code>${__javaScript(${counter} < 5)}</code></div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>条件</label><el-input v-model="selectedNode.props.condition" size="small" placeholder="${__javaScript(vars.get('counter') < 5)}" /></div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'TransactionController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 将子元素视为一个事务，统计总耗时作为该事务的响应时间</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-row">
            <div class="form-group"><label>包含定时器时间</label><el-switch v-model="selectedNode.props.includeTimers" size="small" /></div>
            <div class="form-group"><label>生成父样本</label><el-switch v-model="selectedNode.props.parent" size="small" /></div>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'ThroughputController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 控制子元素执行的频率/比例。如 50% = 一半线程执行、一半跳过</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>控制方式</label>
            <el-select v-model="selectedNode.props.style" size="small">
              <el-option label="按百分比" value="percent" />
              <el-option label="按总执行次数" value="total" />
              <el-option label="按每分钟执行次数" value="perMinute" />
            </el-select>
          </div>
          <div class="form-group" v-if="selectedNode.props.style === 'percent'"><label>百分比 (%)</label><el-input-number v-model="selectedNode.props.percent" :min="0" :max="100" size="small" /></div>
          <div class="form-group" v-else><label>最大吞吐量</label><el-input-number v-model="selectedNode.props.maxThroughput" :min="1" :max="99999" size="small" /></div>
          <div class="form-group"><label>按用户独立计算</label><el-switch v-model="selectedNode.props.perThread" size="small" /></div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'OnceOnlyController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 不管循环多少次，子元素只执行一次。常用于登录等只需执行一次的场景</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>添加子元素到控制器中</label>
            <div style="display:flex;gap:4px;flex-wrap:wrap">
              <el-button size="small" @click="$emit('addChildToCurrent', 'HttpSampler')">🌐 HTTP 请求</el-button>
            </div>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'HTTPHeaderManager'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 为所有 HTTP 请求统一添加请求头，自动继承到子元素</div>
          <div class="form-group"><label>管理器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>请求头</label>
            <div v-for="(h, hi) in (selectedNode.props.headers || [])" :key="hi" class="kv-row">
              <el-input v-model="h.key" placeholder="Header名" size="small" style="width:40%" />
              <el-input v-model="h.value" placeholder="值" size="small" style="width:50%" />
              <el-button link size="small" type="danger" @click="selectedNode.props.headers.splice(hi,1)">×</el-button>
            </div>
            <el-button size="small" @click="selectedNode.props.headers.push({key:'',value:''})">+ 添加请求头</el-button>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'HTTPCookieManager'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 自动管理 HTTP Cookie，模拟真实浏览器行为</div>
          <div class="form-group"><label>管理器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>每次循环清空</label><el-switch v-model="selectedNode.props.clearEachIteration" size="small" /></div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'HTTPRequestDefaults'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 设置默认的协议、域名、端口和请求头，子元素可继承或覆盖这些配置</div>
          <div class="form-group"><label>默认值名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>默认 URL 前缀</label><el-input v-model="selectedNode.props.url" size="small" placeholder="https://api.example.com" /></div>
          <div class="form-group"><label>默认方法</label>
            <el-select v-model="selectedNode.props.method" size="small">
              <el-option v-for="m in ['GET','POST']" :key="m" :label="m" :value="m" />
            </el-select>
          </div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'ViewResultsTree'">
        <div class="form-section">
          <div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
        </div>
        <div v-if="benchResult && benchResult.samples && benchResult.samples.length > 0" class="form-section vrt-inline-section">
          <div class="section-hint" style="margin-bottom:8px"><el-icon><InfoFilled /></el-icon> 以下是最近一次运行的结果数据</div>
          <div class="vrt-container">
            <div class="vrt-left-col">
              <div class="vrt-toolbar">
                <span class="vrt-toolbar-label">查找:</span>
                <el-input :model-value="sampleSearchQuery" @update:model-value="$emit('update:sampleSearchQuery', $event)" size="small" clearable style="width:150px" @keyup.enter="doVrtSearch" />
                <el-checkbox :model-value="searchCaseSensitive" @update:model-value="$emit('update:searchCaseSensitive', $event)" size="small">区分大小写</el-checkbox>
                <el-checkbox :model-value="searchRegex" @update:model-value="$emit('update:searchRegex', $event)" size="small">正则表达式</el-checkbox>
                <el-button size="small" type="primary" plain @click="doVrtSearch">查找</el-button>
                <el-button size="small" @click="resetVrtSearch">重置</el-button>
                <el-select :model-value="sampleStatusFilter" @update:model-value="$emit('update:sampleStatusFilter', $event)" size="small" clearable placeholder="全部" style="width:85px;margin-left:auto">
                  <el-option label="成功" value="success" />
                  <el-option label="失败" value="error" />
                  <el-option label="异常" value="exception" />
                </el-select>
              </div>
              <div class="vrt-sample-list">
                <div v-for="(s, si) in filteredSamples" :key="si"
                  class="vrt-sample-item" :class="{ active: selectedSampleIdx === si }" @click="selectSample(si)">
                  <el-tag :type="s.status >= 200 && s.status < 400 ? 'success' : s.status === 0 ? 'danger' : 'warning'" size="small">{{ s.status || 'ERR' }}</el-tag>
                  <span class="vrt-time">{{ s.elapsed_ms }}ms</span>
                  <span class="vrt-name" :title="s.name || s.url">{{ s.name || shortUrl(s.url) }}</span>
                  <span v-if="s.error" class="vrt-err" title="有错误">⚠</span>
                </div>
                <div v-if="filteredSamples.length === 0" style="padding:12px;text-align:center;color:#94a3b8;font-size:12px">无匹配结果</div>
              </div>
            </div>
            <div v-if="selectedSample" class="vrt-detail-panel">
              <el-tabs :model-value="selectedSampleTab" @update:model-value="$emit('update:selectedSampleTab', $event)" size="small" class="vrt-tabs">
                <el-tab-pane label="采样器结果" name="sampler">
                  <table class="vrt-table">
                    <tr><td class="vrt-label">Thread Name</td><td>{{ selectedSample.thread_name || '线程组 1-' + (selectedSampleIdx + 1) }}</td></tr>
                    <tr><td class="vrt-label">Sample Start</td><td>{{ selectedSample.start_time || '-' }}</td></tr>
                    <tr><td class="vrt-label">Load time</td><td><b>{{ selectedSample.elapsed_ms || 0 }}</b> ms</td></tr>
                    <tr><td class="vrt-label">Connect Time</td><td>{{ selectedSample.connect_time_ms ?? '-' }} ms</td></tr>
                    <tr><td class="vrt-label">Latency</td><td>{{ (selectedSample.latency_ms ?? selectedSample.elapsed_ms) }} ms</td></tr>
                    <tr><td class="vrt-label">Size in bytes</td><td>{{ selectedSample.body_size || 0 }}</td></tr>
                    <tr><td class="vrt-label">Sent bytes</td><td>{{ selectedSample.sent_bytes || 0 }}</td></tr>
                    <tr><td class="vrt-label">Headers size in bytes</td><td>{{ selectedSample.headers_size || 0 }}</td></tr>
                    <tr><td class="vrt-label">Error Count</td><td :style="{ color: selectedSample.error ? 'var(--el-color-danger)' : 'var(--el-color-success)' }">{{ selectedSample.error ? '1' : '0' }}</td></tr>
                    <tr><td class="vrt-label">Data type</td><td>{{ selectedSample.data_type || 'text' }}</td></tr>
                    <tr><td class="vrt-label">Response code</td><td><el-tag :type="selectedSample.status >= 200 && selectedSample.status < 400 ? 'success' : 'danger'" size="small">{{ selectedSample.status || 'ERR' }}</el-tag></td></tr>
                    <tr><td class="vrt-label">Response message</td><td>{{ selectedSample.response_message || (selectedSample.status >= 200 && selectedSample.status < 400 ? 'OK' : 'Error') }}</td></tr>
                  </table>
                </el-tab-pane>
                <el-tab-pane label="请求" name="request">
                  <div v-if="selectedSample.method || selectedSample.url" class="vrt-http-line">
                    <code>{{ selectedSample.method || '?' }} {{ selectedSample.url || '' }}</code>
                  </div>
                  <el-tabs :model-value="selectedRequestTab" @update:model-value="$emit('update:selectedRequestTab', $event)" size="small" class="vrt-inner-tabs">
                    <el-tab-pane label="Request Body" name="rbody">
                      <pre class="vrt-code">{{ selectedSample.request_body || '(无请求体)' }}</pre>
                    </el-tab-pane>
                    <el-tab-pane label="Request Headers" name="rheaders">
                      <pre class="vrt-code"><template v-if="selectedSample.request_headers">{{ formatHeaders(selectedSample.request_headers) }}</template><template v-else>(无请求头信息)</template></pre>
                    </el-tab-pane>
                  </el-tabs>
                </el-tab-pane>
                <el-tab-pane label="响应数据" name="response">
                  <el-tabs :model-value="selectedResponseTab" @update:model-value="$emit('update:selectedResponseTab', $event)" size="small" class="vrt-inner-tabs">
                    <el-tab-pane label="Response Body" name="resbody">
                      <pre class="vrt-code" :class="{ 'vrt-error-body': selectedSample.error }">{{ selectedSample.response_body || selectedSample.error || '(空响应)' }}</pre>
                    </el-tab-pane>
                    <el-tab-pane label="Response Headers" name="resheaders">
                      <pre class="vrt-code"><template v-if="selectedSample.response_headers">{{ formatHeaders(selectedSample.response_headers) }}</template><template v-else>(无响应头信息)</template></pre>
                    </el-tab-pane>
                  </el-tabs>
                </el-tab-pane>
              </el-tabs>
            </div>
            <div v-else class="vrt-empty-detail">👆 点击上方样本查看详情</div>
          </div>
        </div>
        <div v-else class="form-section">
          <div class="empty-state" style="padding:24px 0">尚未运行测试<br/><small style="color:#94a3b8">点击上方「启动」运行测试后，结果将在此处显示</small></div>
        </div>
      </template>
      <template v-if="selectedNode.type === 'SummaryReport' || selectedNode.type === 'AggregateGraph' || selectedNode.type === 'AggregateReport' || selectedNode.type === 'ResponseTimeGraph'">
        <div class="form-section">
          <div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div v-if="benchResult && benchResult.per_url && benchResult.per_url.length > 0" style="margin-top:12px">
            <div class="section-hint" style="margin-bottom:8px"><el-icon><InfoFilled /></el-icon> 以下是最近一次运行的聚合数据</div>
            <table class="per-url-table" style="width:100%;font-size:12px;border-collapse:collapse">
              <thead><tr style="background:#f1f5f9"><th style="padding:4px 8px;text-align:left">URL</th><th style="padding:4px 8px">次数</th><th style="padding:4px 8px">成功</th><th style="padding:4px 8px">失败</th><th style="padding:4px 8px">平均(ms)</th><th style="padding:4px 8px">P95(ms)</th></tr></thead>
              <tbody><tr v-for="pu in benchResult.per_url" :key="pu.url" style="border-bottom:1px solid #e2e8f0"><td style="padding:4px 8px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ pu.url }}</td><td style="padding:4px 8px;text-align:center">{{ pu.count }}</td><td style="padding:4px 8px;text-align:center;color:#10b981">{{ pu.success }}</td><td style="padding:4px 8px;text-align:center" :style="{ color: pu.failed > 0 ? '#ef4444' : '#10b981' }">{{ pu.failed }}</td><td style="padding:4px 8px;text-align:center">{{ pu.avg_ms }}</td><td style="padding:4px 8px;text-align:center">{{ pu.p95_ms }}</td></tr></tbody>
            </table>
          </div>
          <div v-else class="empty-state" style="padding:24px 0">尚未运行测试<br/><small style="color:#94a3b8">运行测试后，聚合数据将在此处显示</small></div>
        </div>
      </template>

      <template v-if="selectedNode.type === 'InfluxDBBackendListener'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 将 JMeter 测试指标实时推送到 InfluxDB 时序数据库，配合 Grafana 做可视化监控大屏。真实压测必备！</div>
          <div class="form-group"><label>监听器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>InfluxDB URL</label><el-input v-model="selectedNode.props.influxdbUrl" placeholder="http://localhost:8086/write?db=jmeter" size="small" /></div>
          <div class="form-row">
            <div class="form-group"><label>应用名</label><el-input v-model="selectedNode.props.application" placeholder="test" size="small" /></div>
            <div class="form-group"><label>测量名称</label><el-input v-model="selectedNode.props.measurement" placeholder="jmeter" size="small" /></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>仅汇总结果</label><el-switch v-model="selectedNode.props.summaryOnly" size="small" /></div>
            <div class="form-group"><label>采样器正则过滤</label><el-input v-model="selectedNode.props.samplersRegex" placeholder="留空=全部" size="small" /></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>百分位(分号分隔)</label><el-input v-model="selectedNode.props.percentiles" placeholder="50;90;95;99" size="small" /></div>
            <div class="form-group"><label>测试标题</label><el-input v-model="selectedNode.props.testTitle" placeholder="" size="small" /></div>
          </div>
          <div class="form-group"><label>事件标签</label><el-input v-model="selectedNode.props.eventTags" placeholder="TAG_Random=${__Random(0,999999999)}" size="small" /></div>
        </div>
      </template>

      <template v-if="selectedNode.type === 'UserParameters'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 真实场景：多账号并发测试。每个线程使用不同的用户凭证，模拟真实多用户访问。比 CSV 数据源更直观地管理账号</div>
          <div class="form-group"><label>参数名称（每行一个）</label>
            <div style="display:flex;flex-direction:column;gap:4px">
              <div v-for="(name, ni) in selectedNode.props.names" :key="ni" style="display:flex;gap:4px">
                <el-input v-model="selectedNode.props.names[ni]" placeholder="如 sid, password" size="small" />
                <el-button link size="small" type="danger" @click="selectedNode.props.names.splice(ni,1); selectedNode.props.users.forEach(u=>u.splice(ni,1))">×</el-button>
              </div>
              <el-button size="small" @click="selectedNode.props.names.push(''); selectedNode.props.users.forEach(u=>u.push(''))">+ 添加参数列</el-button>
            </div>
          </div>
          <div class="form-group"><label>用户数据（每行一个用户）</label>
            <div style="max-height:200px;overflow-y:auto;border:1px solid rgba(148,163,184,0.2);border-radius:8px;padding:8px;background:rgba(248,250,252,0.5)">
              <table style="width:100%;font-size:11.5px;border-collapse:collapse">
                <tr style="background:rgba(99,102,241,0.06)">
                  <th style="padding:3px 6px;text-align:left;font-size:10px;color:#6366f1">用户#</th>
                  <th v-for="(n, ni) in selectedNode.props.names" :key="'h'+ni" style="padding:3px 6px;text-align:left;font-size:10px;color:#6366f1">{{ n || '参数'+(ni+1) }}</th>
                </tr>
                <tr v-for="(user, ui) in selectedNode.props.users" :key="ui" style="border-top:1px solid rgba(148,163,184,0.1)">
                  <td style="padding:3px 6px;font-weight:700;color:#94a3b8;font-size:10px">{{ ui+1 }}</td>
                  <td v-for="(val, vi) in user" :key="vi" style="padding:2px">
                    <el-input v-model="selectedNode.props.users[ui][vi]" size="small" style="width:100%" />
                  </td>
                  <td style="padding:2px">
                    <el-button link size="small" type="danger" @click="selectedNode.props.users.splice(ui,1)" style="font-size:11px">×</el-button>
                  </td>
                </tr>
              </table>
              <el-button size="small" @click="selectedNode.props.users.push(selectedNode.props.names.map(()=>''))" style="margin-top:6px;width:100%">+ 添加用户</el-button>
              <el-button size="small" @click="selectedNode.props.users = []" type="danger" plain style="margin-top:4px;width:100%">清空全部</el-button>
            </div>
          </div>
          <div class="form-group"><label>每次迭代取下一个</label><el-switch v-model="selectedNode.props.perIteration" size="small" /></div>
        </div>
      </template>

      <template v-if="selectedNode.type === 'DebugSampler'">
        <div class="form-section">
          <div class="form-group"><label>采样器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
        </div>
        <div class="section-hint"><el-icon><InfoFilled /></el-icon> 调试神器！运行时输出所有 JMeter 变量值到「查看结果树」中。排查变量是否正确设置时必用</div>
      </template>

      <template v-if="selectedNode.type === 'ForEachController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 遍历一组变量。如变量前缀为 item_ 则遍历 item_1, item_2, item_3... 常用于批量处理提取的数据</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>输入变量前缀</label><el-input v-model="selectedNode.props.inputVar" placeholder="item_" size="small" /><span class="form-hint">会遍历 item_1, item_2, ...</span></div>
          <div class="form-group"><label>输出变量名</label><el-input v-model="selectedNode.props.outputVar" placeholder="currentItem" size="small" /><span class="form-hint">循环体内用 ${currentItem} 引用当前值</span></div>
          <div class="form-row">
            <div class="form-group"><label>使用分隔符 "_"</label><el-switch v-model="selectedNode.props.useSeparator" size="small" /></div>
            <div class="form-group"><label>分隔符</label><el-input v-model="selectedNode.props.separator" placeholder="_" size="small" style="width:60px" /></div>
          </div>
        </div>
      </template>

      <template v-if="selectedNode.type === 'SwitchController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> 根据表达式值选择执行哪个子元素。类似 Java switch-case，支持默认分支</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>Switch 值（表达式或数字）</label><el-input v-model="selectedNode.props.switchValue" placeholder="${status}" size="small" /></div>
          <div class="form-group"><label>添加子元素</label>
            <div style="display:flex;gap:4px;flex-wrap:wrap">
              <el-button size="small" @click="$emit('addChildToCurrent', 'HttpSampler')">🌐 HTTP 请求</el-button>
              <el-button size="small" @click="$emit('addChildToCurrent', 'IfController')">🔀 如果控制器</el-button>
            </div>
          </div>
        </div>
      </template>

      <template v-if="selectedNode.type === 'RandomController' || selectedNode.type === 'InterleaveController'">
        <div class="form-section">
          <div class="section-hint"><el-icon><InfoFilled /></el-icon> {{ selectedNode.type === 'RandomController' ? '每次随机选择一个子元素执行，模拟用户随机行为' : '按顺序轮换子元素执行，每个子元素轮流被选中一次' }}</div>
          <div class="form-group"><label>控制器名称</label><el-input v-model="selectedNode.name" size="small" /></div>
          <div class="form-group"><label>添加子元素</label>
            <div style="display:flex;gap:4px;flex-wrap:wrap">
              <el-button size="small" @click="$emit('addChildToCurrent', 'HttpSampler')">🌐 HTTP 请求</el-button>
              <el-button size="small" @click="$emit('addChildToCurrent', 'IfController')">🔀 如果控制器</el-button>
            </div>
          </div>
        </div>
      </template>
    </div>
    <div class="editor-empty" v-else>
      <el-icon size="36"><EditPen /></el-icon>
      <p>选择左侧树中的元素<br/>开始编辑属性</p>
      <div class="editor-empty-tips">
        <div class="empty-tip" @click="$emit('addRootElement')">➕ 添加线程组</div>
        <div class="empty-tip" @click="$emit('gotoStep1')">📥 导入接口用例</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { InfoFilled, Monitor, Connection, Coin, Lollipop, Setting, VideoPlay, EditPen } from '@element-plus/icons-vue'

const props = defineProps({
  selectedNode: { type: Object, default: null },
  NODE_TYPES: { type: Object, default: () => ({}) },
  benchResult: { type: Object, default: null },
  projectVariables: { type: Array, default: () => [] },
  aiValidationResult: { type: Object, default: null },
  aiValidating: { type: Boolean, default: false },
  aiGenerating: { type: Boolean, default: false },
  debugLoading: { type: Boolean, default: false },
  savingToCase: { type: Boolean, default: false },
  sampleSearchQuery: { type: String, default: '' },
  searchCaseSensitive: { type: Boolean, default: false },
  searchRegex: { type: Boolean, default: false },
  sampleStatusFilter: { type: String, default: '' },
  selectedSampleIdx: { type: Number, default: -1 },
  selectedSampleTab: { type: String, default: 'sampler' },
  selectedRequestTab: { type: String, default: 'rbody' },
  selectedResponseTab: { type: String, default: 'resbody' },
})

const emit = defineEmits([
  'addVar',
  'addHeader',
  'addChildToCurrent',
  'addChildNode',
  'debugRequest',
  'saveSamplerToCase',
  'aiGenerateAssert',
  'aiValidateScript',
  'insertVariable',
  'addRootElement',
  'gotoStep1',
  'selectSample',
  'doVrtSearch',
  'resetVrtSearch',
  'update:sampleSearchQuery',
  'update:searchCaseSensitive',
  'update:searchRegex',
  'update:sampleStatusFilter',
  'update:selectedSampleTab',
  'update:selectedRequestTab',
  'update:selectedResponseTab',
  'update:selectedSampleIdx',
])

const selectedSample = computed(() => {
  if (!props.benchResult?.samples) return null
  return props.benchResult.samples[props.selectedSampleIdx] ?? null
})

const filteredSamples = computed(() => {
  if (!props.benchResult?.samples) return []
  const samples = props.benchResult.samples
  let result = samples
  if (props.sampleStatusFilter) {
    result = result.filter(s => {
      const ok = s.status >= 200 && s.status < 400
      if (props.sampleStatusFilter === 'success') return ok
      if (props.sampleStatusFilter === 'error') return !ok && s.status !== 0
      if (props.sampleStatusFilter === 'exception') return s.status === 0
      return true
    })
  }
  if (props.sampleSearchQuery) {
    const q = props.sampleSearchQuery
    const caseSensitive = props.searchCaseSensitive
    const isRegex = props.searchRegex
    result = result.filter(s => {
      const text = [s.name, s.url, s.response_body, s.request_body, s.error].filter(Boolean).join(' ')
      const haystack = caseSensitive ? text : text.toLowerCase()
      const needle = caseSensitive ? q : q.toLowerCase()
      if (isRegex) {
        try { return new RegExp(q, caseSensitive ? '' : 'i').test(text) } catch { return false }
      }
      return haystack.includes(needle)
    })
  }
  return result
})

const shortUrl = (url) => {
  if (!url) return ''
  try {
    const u = new URL(url)
    return u.pathname + (u.search || '')
  } catch {
    return url.length > 60 ? url.slice(0, 60) + '...' : url
  }
}

const formatHeaders = (headers) => {
  if (!headers) return ''
  if (typeof headers === 'string') return headers
  if (Array.isArray(headers)) return headers.map(h => `${h.key || h.name || ''}: ${h.value || ''}`).join('\n')
  if (typeof headers === 'object') return Object.entries(headers).map(([k, v]) => `${k}: ${v}`).join('\n')
  return String(headers)
}

const selectSample = (idx) => {
  emit('selectSample', idx)
}

const doVrtSearch = () => {
  emit('doVrtSearch')
}

const resetVrtSearch = () => {
  emit('resetVrtSearch')
}
</script>

<style scoped>
</style>
