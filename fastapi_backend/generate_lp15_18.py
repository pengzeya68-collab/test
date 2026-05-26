"""
重新生成 LP15-LP18 高质量习题
注意：字符串内部不使用中文引号，使用英文单引号或不用引号
"""
import sqlite3
import os
from datetime import datetime

def get_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return sqlite3.connect(os.path.join(base_dir, 'instance', 'testmaster.db'))

def insert_exercise(cursor, title, description, solution, exercise_type, difficulty, learning_path_id, category, lang="中文"):
    cursor.execute("""
        INSERT INTO exercises
        (title, description, solution, exercise_type, difficulty,
         learning_path_id, category, is_public, language,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
    """, (title, description, solution, exercise_type, difficulty, learning_path_id, category, lang))

# ========== LP15: 持续集成与DevOps (50题) ==========
LP15_EXERCISES = [
    # CI/CD核心概念 (8题)
    ("CI/CD中的CI代表什么？",
     "CI/CD中的CI代表什么？\n\nA. Continuous Integration（持续集成）\nB. Continuous Inspection（持续检查）\nC. Code Integration（代码集成）\nD. Continuous Improvement（持续改进）",
     "A", "single_choice", "easy", "CI/CD概念"),
    ("以下哪个不是CI/CD的核心目标？",
     "以下哪个不是CI/CD的核心目标？\n\nA. 加快软件交付速度\nB. 提高代码质量\nC. 减少人工干预和重复工作\nD. 增加软件的功能数量",
     "D", "single_choice", "easy", "CI/CD概念"),
    ("CI/CD流水线中，以下哪个阶段通常在构建之后？",
     "CI/CD流水线中，以下哪个阶段通常在构建之后？\n\nA. 代码提交\nB. 自动化测试\nC. 需求分析\nD. 代码编写",
     "B", "single_choice", "easy", "CI/CD概念"),
    ("以下哪些工具可以用于CI/CD流水线？",
     "以下哪些工具可以用于CI/CD流水线？（多选）\n\nA. Jenkins\nB. GitLab CI\nC. GitHub Actions\nD. CircleCI",
     "A,B,C,D", "multiple_choice", "easy", "CI/CD概念"),
    ("持续部署和持续交付的主要区别是什么？",
     "持续部署（Continuous Deployment）和持续交付（Continuous Delivery）的主要区别是什么？\n\nA. 持续部署会自动将代码发布到生产环境，持续交付需要手动确认后发布\nB. 两者完全相同，没有区别\nC. 持续交付比持续部署更自动化\nD. 持续部署只用于测试环境，持续交付用于生产环境",
     "A", "single_choice", "medium", "CI/CD概念"),
    ("CI/CD中的构建阶段通常包含哪些操作？",
     "CI/CD中的构建（Build）阶段通常包含哪些操作？（多选）\n\nA. 代码编译\nB. 依赖安装\nC. 打包生成可部署的制品\nD. 代码格式化检查",
     "A,B,C", "multiple_choice", "easy", "CI/CD概念"),
    ("CI/CD流水线中，自动化测试通常包括哪些类型？",
     "CI/CD流水线中，自动化测试通常包括哪些类型？（多选）\n\nA. 单元测试\nB. 集成测试\nC. 端到端测试\nD. 代码规范检查",
     "A,B,C,D", "multiple_choice", "easy", "CI/CD概念"),
    ("DevOps是一种只适用于大型企业的实践，小型团队不需要。",
     "DevOps是一种只适用于大型企业的实践，小型团队不需要。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "CI/CD概念"),

    # Git工作流 (8题)
    ("GitFlow工作流中，feature分支的作用是什么？",
     "GitFlow工作流中，feature分支的作用是什么？\n\nA. 用于修复生产环境的紧急Bug\nB. 用于开发新功能，从develop分支创建，完成后合并回develop\nC. 用于发布版本\nD. 用于长期维护旧版本",
     "B", "single_choice", "easy", "Git工作流"),
    ("Trunk-Based Development与GitFlow的主要区别是什么？",
     "Trunk-Based Development（主干开发）与GitFlow的主要区别是什么？\n\nA. Trunk-Based Development所有开发都在主干上进行，分支生命周期很短\nB. Trunk-Based Development使用更多的长期分支\nC. 两者完全相同\nD. Trunk-Based Development不支持代码审查",
     "A", "single_choice", "medium", "Git工作流"),
    ("以下哪些是Git工作流中常见的分支类型？",
     "以下哪些是Git工作流中常见的分支类型？（多选）\n\nA. main/master\nB. develop\nC. feature/*\nD. hotfix/*",
     "A,B,C,D", "multiple_choice", "easy", "Git工作流"),
    ("GitFlow中的release分支主要用于什么？",
     "GitFlow中的release分支主要用于什么？\n\nA. 开发新功能\nB. 准备发布版本，进行最后的测试和版本号更新\nC. 修复生产环境的紧急Bug\nD. 长期维护旧版本",
     "B", "single_choice", "easy", "Git工作流"),
    ("在Git中，rebase和merge合并代码的主要区别是什么？",
     "在Git中，rebase和merge合并代码的主要区别是什么？\n\nA. rebase会创建新的提交历史，使历史更线性；merge会保留分支历史\nB. rebase和merge完全相同\nC. rebase只能用于本地分支，merge只能用于远程分支\nD. rebase会自动解决所有冲突，merge不会",
     "A", "single_choice", "medium", "Git工作流"),
    ("GitFlow中的hotfix分支应该从哪个分支创建？",
     "GitFlow中的hotfix分支应该从哪个分支创建？\n\nA. develop分支\nB. main/master分支\nC. feature分支\nD. release分支",
     "B", "single_choice", "easy", "Git工作流"),
    ("Git的cherry-pick命令的作用是什么？",
     "Git的cherry-pick命令的作用是什么？\n\nA. 将某个分支的所有提交合并到当前分支\nB. 将指定的提交应用到当前分支\nC. 删除指定的提交\nD. 创建一个新的分支",
     "B", "single_choice", "medium", "Git工作流"),
    ("GitFlow工作流适合所有类型的项目，包括快速迭代的小型项目。",
     "GitFlow工作流适合所有类型的项目，包括快速迭代的小型项目。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "Git工作流"),

    # Jenkins Pipeline (7题)
    ("Jenkins Pipeline中，声明式Pipeline和脚本式Pipeline的主要区别是什么？",
     "Jenkins Pipeline中，声明式Pipeline和脚本式Pipeline的主要区别是什么？\n\nA. 声明式Pipeline语法更结构化，脚本式Pipeline更灵活但学习曲线更高\nB. 声明式Pipeline只能用Java写，脚本式Pipeline只能用Groovy写\nC. 两者功能完全相同\nD. 声明式Pipeline不支持并行执行",
     "A", "single_choice", "medium", "Jenkins Pipeline"),
    ("Jenkins Pipeline中的stage代表什么？",
     "Jenkins Pipeline中的stage代表什么？\n\nA. 一个代码文件\nB. 流水线中的一个阶段，如Build、Test、Deploy\nC. 一个Git分支\nD. 一个环境变量",
     "B", "single_choice", "easy", "Jenkins Pipeline"),
    ("Jenkinsfile是什么？",
     "Jenkinsfile是什么？\n\nA. Jenkins的配置文件，用于定义Pipeline\nB. Jenkins的日志文件\nC. Jenkins的安装文件\nD. Jenkins的插件管理文件",
     "A", "single_choice", "easy", "Jenkins Pipeline"),
    ("Jenkins Pipeline中，如何实现并行执行多个任务？",
     "Jenkins Pipeline中，如何实现并行执行多个任务？\n\nA. 使用parallel关键字\nB. 使用串行执行，Jenkins会自动并行\nC. 使用for循环\nD. Jenkins不支持并行执行",
     "A", "single_choice", "medium", "Jenkins Pipeline"),
    ("Jenkins Pipeline中，agent关键字的作用是什么？",
     "Jenkins Pipeline中，agent关键字的作用是什么？\n\nA. 定义代码仓库地址\nB. 定义Pipeline在哪个节点（机器）上执行\nC. 定义环境变量\nD. 定义通知收件人",
     "B", "single_choice", "easy", "Jenkins Pipeline"),
    ("Jenkins Pipeline中，如何在不同stage之间传递数据？",
     "Jenkins Pipeline中，如何在不同stage之间传递数据？\n\nA. 使用全局变量或写入文件\nB. 数据不能在不同stage之间传递\nC. 使用Git分支\nD. 使用数据库",
     "A", "single_choice", "medium", "Jenkins Pipeline"),
    ("Jenkins Pipeline支持从版本控制中加载共享库（Shared Library）。",
     "Jenkins Pipeline支持从版本控制中加载共享库（Shared Library）。\n\nA. 正确\nB. 错误",
     "A", "true_false", "easy", "Jenkins Pipeline"),

    # Docker容器化 (7题)
    ("Docker容器与传统虚拟机的主要区别是什么？",
     "Docker容器与传统虚拟机的主要区别是什么？\n\nA. 容器共享主机操作系统内核，虚拟机需要完整的操作系统\nB. 容器比虚拟机更重量级\nC. 容器不能运行多个应用，虚拟机可以\nD. 容器只能运行在Linux上",
     "A", "single_choice", "easy", "Docker容器化"),
    ("Dockerfile中的FROM指令的作用是什么？",
     "Dockerfile中的FROM指令的作用是什么？\n\nA. 指定基础镜像\nB. 指定容器启动命令\nC. 指定端口映射\nD. 指定环境变量",
     "A", "single_choice", "easy", "Docker容器化"),
    ("Docker Compose的主要作用是什么？",
     "Docker Compose的主要作用是什么？\n\nA. 构建单个Docker镜像\nB. 定义和运行多容器Docker应用\nC. 管理Docker镜像仓库\nD. 监控容器性能",
     "B", "single_choice", "easy", "Docker容器化"),
    ("以下哪些是Dockerfile的常见指令？",
     "以下哪些是Dockerfile的常见指令？（多选）\n\nA. FROM\nB. RUN\nC. COPY\nD. EXPOSE",
     "A,B,C,D", "multiple_choice", "easy", "Docker容器化"),
    ("Docker容器的数据持久化通常如何实现？",
     "Docker容器的数据持久化通常如何实现？\n\nA. 使用Volume（数据卷）\nB. 直接写入容器文件系统\nC. 无法持久化，容器删除数据就丢失\nD. 使用环境变量存储",
     "A", "single_choice", "medium", "Docker容器化"),
    ("Docker镜像的分层存储有什么优势？",
     "Docker镜像的分层存储有什么优势？\n\nA. 节省存储空间，多个镜像可以共享基础层\nB. 加快容器启动速度\nC. 提高安全性\nD. 支持跨平台运行",
     "A", "single_choice", "medium", "Docker容器化"),
    ("Dockerfile中的ENTRYPOINT和CMD指令的主要区别是什么？",
     "Dockerfile中的ENTRYPOINT和CMD指令的主要区别是什么？\n\nA. ENTRYPOINT中的命令不会被docker run的命令行参数覆盖，CMD会被覆盖\nB. 两者完全相同\nC. ENTRYPOINT用于指定工作目录，CMD用于指定启动命令\nD. CMD只能用于测试环境，ENTRYPOINT用于生产环境",
     "A", "single_choice", "medium", "Docker容器化"),

    # GitLab CI/CD (6题)
    ("GitLab CI/CD的配置文件通常叫什么？",
     "GitLab CI/CD的配置文件通常叫什么？\n\nA. .gitlab-ci.yml\nB. jenkinsfile\nC. .github/workflows/*.yml\nD. Dockerfile",
     "A", "single_choice", "easy", "GitLab CI/CD"),
    ("GitLab CI/CD中，runner的作用是什么？",
     "GitLab CI/CD中，runner的作用是什么？\n\nA. 存储代码仓库\nB. 执行CI/CD流水线的任务\nC. 管理用户权限\nD. 托管Docker镜像",
     "B", "single_choice", "easy", "GitLab CI/CD"),
    ("GitLab CI/CD的流水线通常由什么触发？",
     "GitLab CI/CD的流水线通常由什么触发？\n\nA. 只有手动触发\nB. 代码推送、合并请求、定时任务等\nC. 只有定时任务触发\nD. 只有管理员可以触发",
     "B", "single_choice", "easy", "GitLab CI/CD"),
    ("GitLab CI/CD的artifact（制品）是什么？",
     "GitLab CI/CD的artifact（制品）是什么？\n\nA. 流水线执行过程中生成的文件，可以在不同阶段或流水线之间传递\nB. Docker镜像的别名\nC. 代码仓库的分支\nD. 测试报告的格式",
     "A", "single_choice", "medium", "GitLab CI/CD"),
    ("GitLab CI/CD中，environment（环境）的作用是什么？",
     "GitLab CI/CD中，environment（环境）的作用是什么？\n\nA. 定义部署目标（如staging、production）并跟踪部署历史\nB. 定义构建环境的基础镜像\nC. 定义环境变量\nD. 定义流水线执行的顺序",
     "A", "single_choice", "medium", "GitLab CI/CD"),
    ("GitLab CI/CD支持部署到Kubernetes集群。",
     "GitLab CI/CD支持部署到Kubernetes集群。\n\nA. 正确\nB. 错误",
     "A", "true_false", "easy", "GitLab CI/CD"),

    # 质量门禁 (6题)
    ("质量门禁（Quality Gate）的主要作用是什么？",
     "质量门禁（Quality Gate）的主要作用是什么？\n\nA. 限制代码提交速度\nB. 在CI/CD流水线中设置质量标准，未达标时阻断部署\nC. 管理开发团队的权限\nD. 自动生成测试报告",
     "B", "single_choice", "easy", "质量门禁"),
    ("SonarQube是什么？",
     "SonarQube是什么？\n\nA. 一个代码质量检查平台\nB. 一个CI/CD工具\nC. 一个容器编排平台\nD. 一个代码编辑器",
     "A", "single_choice", "easy", "质量门禁"),
    ("质量门禁通常检查哪些指标？",
     "质量门禁通常检查哪些指标？（多选）\n\nA. 代码覆盖率\nB. 代码重复率\nC. 代码复杂度\nD. 安全漏洞",
     "A,B,C,D", "multiple_choice", "easy", "质量门禁"),
    ("如果质量门禁未通过，CI/CD流水线通常会如何处理？",
     "如果质量门禁未通过，CI/CD流水线通常会如何处理？\n\nA. 继续部署，只是记录警告\nB. 阻断流水线，停止后续部署步骤\nC. 自动修复代码问题\nD. 发送邮件通知但不阻断流水线",
     "B", "single_choice", "easy", "质量门禁"),
    ("质量门禁只适用于大型项目，小型项目不需要。",
     "质量门禁只适用于大型项目，小型项目不需要。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "质量门禁"),
    ("在SonarQube中，Quality Gate的状态通常有哪些？",
     "在SonarQube中，Quality Gate的状态通常有哪些？\n\nA. PASS（通过）和FAIL（失败）\nB. OK和ERROR\nC. SUCCESS和FAILED\nD. 只有一种状态",
     "A", "single_choice", "easy", "质量门禁"),

    # 需求分析与技术选型 (8题)
    ("在测试平台开发中，需求分析的主要目标是什么？",
     "在测试平台开发中，需求分析的主要目标是什么？\n\nA. 确定项目的工期和预算\nB. 理解用户真实需求，明确系统功能和边界\nC. 选择开发语言和框架\nD. 编写详细的测试用例",
     "B", "single_choice", "easy", "需求分析与技术选型"),
    ("技术选型时，以下哪些因素需要考虑？",
     "技术选型时，以下哪些因素需要考虑？（多选）\n\nA. 团队技术栈熟悉度\nB. 社区活跃度和生态\nC. 性能和可扩展性\nD. 学习成本和开发效率",
     "A,B,C,D", "multiple_choice", "easy", "需求分析与技术选型"),
    ("在选择Web框架时，FastAPI相比于Flask的主要优势是什么？",
     "在选择Web框架时，FastAPI相比于Flask的主要优势是什么？\n\nA. 更快的性能、自动API文档、类型提示支持\nB. Flask比FastAPI功能更强大\nC. FastAPI不支持异步\nD. Flask有更好的社区支持",
     "A", "single_choice", "medium", "需求分析与技术选型"),
    ("前端技术选型时，Vue和React的主要区别有哪些？",
     "前端技术选型时，Vue和React的主要区别有哪些？（多选）\n\nA. Vue使用模板语法，React使用JSX\nB. Vue是MVVM架构，React是函数式组件\nC. Vue学习曲线更平缓\nD. React的生态系统更大",
     "A,B,C,D", "multiple_choice", "medium", "需求分析与技术选型"),
    ("数据库选型时，什么时候应该选择MongoDB等NoSQL数据库？",
     "数据库选型时，什么时候应该选择MongoDB等NoSQL数据库？\n\nA. 数据schema频繁变化，需要灵活的数据模型\nB. 只需要简单的CRUD操作\nC. 需要强事务支持\nD. 数据量很小，不需要扩展",
     "A", "single_choice", "medium", "需求分析与技术选型"),
    ("在微服务架构中，服务间通信通常使用什么协议？",
     "在微服务架构中，服务间通信通常使用什么协议？\n\nA. 只能用HTTP/REST\nB. HTTP/REST、gRPC、消息队列等多种协议\nC. 只能用gRPC\nD. 只能用共享数据库",
     "B", "single_choice", "medium", "需求分析与技术选型"),
    ("技术选型时，应该优先选择最新最热门的技术。",
     "技术选型时，应该优先选择最新最热门的技术。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "需求分析与技术选型"),
    ("在测试平台中，为什么需要Redis这样的缓存？",
     "在测试平台中，为什么需要Redis这样的缓存？\n\nA. 提高频繁访问数据的读取速度，减轻数据库压力\nB. 替代数据库存储所有数据\nC. 只是为了跟上技术潮流\nD. 缓存是必须的，所有系统都需要",
     "A", "single_choice", "medium", "需求分析与技术选型"),
]

# ========== LP16: 测试架构师 (50题) ==========
LP16_EXERCISES = [
    # 数据库设计与ORM (8题)
    ("ORM（对象关系映射）的主要作用是什么？",
     "ORM（对象关系映射）的主要作用是什么？\n\nA. 将数据库表映射为编程语言中的对象，简化数据库操作\nB. 优化数据库查询性能\nC. 自动备份数据库\nD. 将关系型数据库转换为非关系型数据库",
     "A", "single_choice", "easy", "数据库设计与ORM"),
    ("SQLAlchemy是哪种编程语言的ORM框架？",
     "SQLAlchemy是哪种编程语言的ORM框架？\n\nA. Java\nB. Python\nC. JavaScript\nD. Go",
     "B", "single_choice", "easy", "数据库设计与ORM"),
    ("数据库设计中，一对多关系通常如何表示？",
     "数据库设计中，一对多关系通常如何表示？\n\nA. 在两个表中各添加一个外键\nB. 在多的一方添加外键指向一的一方\nC. 创建一个新的关联表\nD. 将两个表合并为一个表",
     "B", "single_choice", "easy", "数据库设计与ORM"),
    ("以下哪些是数据库设计中的常见规范？",
     "以下哪些是数据库设计中的常见规范？（多选）\n\nA. 每个表应该有主键\nB. 避免数据冗余\nC. 使用合适的数据类型\nD. 添加必要的索引",
     "A,B,C,D", "multiple_choice", "easy", "数据库设计与ORM"),
    ("数据库的索引（Index）有什么作用？",
     "数据库的索引（Index）有什么作用？\n\nA. 加快数据的查询速度\nB. 减少数据存储空间\nC. 保证数据的唯一性\nD. 自动备份数据",
     "A", "single_choice", "easy", "数据库设计与ORM"),
    ("SQLAlchemy中，declarative_base的作用是什么？",
     "SQLAlchemy中，declarative_base的作用是什么？\n\nA. 定义数据库连接\nB. 创建ORM模型的基类\nC. 执行SQL查询\nD. 管理数据库事务",
     "B", "single_choice", "medium", "数据库设计与ORM"),
    ("数据库的事务（Transaction）具有哪些特性（ACID）？",
     "数据库的事务（Transaction）具有哪些特性（ACID）？\n\nA. Atomicity（原子性）、Consistency（一致性）、Isolation（隔离性）、Durability（持久性）\nB. Availability（可用性）、Consistency（一致性）、Isolation（隔离性）、Durability（持久性）\nC. Atomicity（原子性）、Completeness（完整性）、Isolation（隔离性）、Durability（持久性）\nD. Availability（可用性）、Completeness（完整性）、Isolation（隔离性）、Durability（持久性）",
     "A", "single_choice", "medium", "数据库设计与ORM"),
    ("在数据库设计中，第三范式（3NF）主要解决了什么问题？",
     "在数据库设计中，第三范式（3NF）主要解决了什么问题？\n\nA. 数据冗余和更新异常\nB. 查询性能问题\nC. 数据安全问题\nD. 并发访问问题",
     "A", "single_choice", "medium", "数据库设计与ORM"),

    # RESTful API开发 (8题)
    ("RESTful API中，HTTP方法GET通常用于什么操作？",
     "RESTful API中，HTTP方法GET通常用于什么操作？\n\nA. 创建资源\nB. 获取资源\nC. 更新资源\nD. 删除资源",
     "B", "single_choice", "easy", "RESTful API开发"),
    ("HTTP状态码404表示什么意思？",
     "HTTP状态码404表示什么意思？\n\nA. 服务器内部错误\nB. 请求的资源未找到\nC. 请求参数错误\nD. 未授权访问",
     "B", "single_choice", "easy", "RESTful API开发"),
    ("FastAPI框架的主要优势是什么？",
     "FastAPI框架的主要优势是什么？（多选）\n\nA. 高性能，基于Starlette和Pydantic\nB. 自动生成API文档（Swagger/ReDoc）\nC. 类型提示支持\nD. 异步支持",
     "A,B,C,D", "multiple_choice", "easy", "RESTful API开发"),
    ("RESTful API设计中，以下哪个URL设计更符合RESTful规范？",
     "RESTful API设计中，以下哪个URL设计更符合RESTful规范？\n\nA. GET /getUser?id=123\nB. GET /users/123\nC. GET /user/get/123\nD. POST /users/123/get",
     "B", "single_choice", "easy", "RESTful API开发"),
    ("API的版本控制通常有哪些策略？",
     "API的版本控制通常有哪些策略？（多选）\n\nA. URL路径中包含版本号（如/api/v1/users）\nB. 请求头中指定版本号\nC. 查询参数中指定版本号\nD. 不控制版本，随时修改API",
     "A,B,C", "multiple_choice", "easy", "RESTful API开发"),
    ("FastAPI中的依赖注入（Dependency Injection）有什么作用？",
     "FastAPI中的依赖注入（Dependency Injection）有什么作用？\n\nA. 增加代码复杂度\nB. 实现代码复用，如数据库连接、权限验证等\nC. 只能用于数据库操作\nD. 自动生成前端代码",
     "B", "single_choice", "medium", "RESTful API开发"),
    ("API的分页设计通常使用哪些参数？",
     "API的分页设计通常使用哪些参数？\n\nA. page和page_size\nB. offset和limit\nC. start和end\nD. A和B都是常见的分页参数",
     "D", "single_choice", "easy", "RESTful API开发"),
    ("RESTful API的幂等性是什么意思？",
     "RESTful API的幂等性是什么意思？\n\nA. 每次请求返回相同的结果\nB. 多次执行相同的操作，产生的效果与执行一次相同\nC. API响应速度非常快\nD. API不需要认证",
     "B", "single_choice", "medium", "RESTful API开发"),

    # 前端页面开发 (7题)
    ("Vue 3中的组合式API（Composition API）相比于选项式API（Options API）有什么优势？",
     "Vue 3中的组合式API（Composition API）相比于选项式API（Options API）有什么优势？\n\nA. 逻辑可以按功能组织，而不是按选项类型分散\nB. 更好的TypeScript支持\nC. 代码复用更方便（通过组合函数）\nD. 以上所有",
     "D", "single_choice", "medium", "前端页面开发"),
    ("Element Plus是什么？",
     "Element Plus是什么？\n\nA. Vue 3的组件库\nB. React的组件库\nC. Angular的组件库\nD. 一个CSS框架",
     "A", "single_choice", "easy", "前端页面开发"),
    ("Pinia在Vue 3中主要承担什么角色？",
     "Pinia在Vue 3中主要承担什么角色？\n\nA. 路由管理\nB. 状态管理（Store）\nC. HTTP请求库\nD. UI组件库",
     "B", "single_choice", "easy", "前端页面开发"),
    ("Vue 3中，v-model指令的作用是什么？",
     "Vue 3中，v-model指令的作用是什么？\n\nA. 绑定事件\nB. 实现双向数据绑定\nC. 条件渲染\nD. 列表渲染",
     "B", "single_choice", "easy", "前端页面开发"),
    ("前端开发中，Axios通常用于什么？",
     "前端开发中，Axios通常用于什么？\n\nA. 状态管理\nB. 发送HTTP请求\nC. 路由跳转\nD. 表单验证",
     "B", "single_choice", "easy", "前端页面开发"),
    ("Vue Router中的路由守卫（Navigation Guards）有什么作用？",
     "Vue Router中的路由守卫（Navigation Guards）有什么作用？\n\nA. 美化路由页面\nB. 在路由跳转前后执行逻辑，如权限验证、数据预加载\nC. 优化路由加载速度\nD. 管理路由缓存",
     "B", "single_choice", "medium", "前端页面开发"),
    ("前端项目的构建（Build）过程通常包括哪些操作？",
     "前端项目的构建（Build）过程通常包括哪些操作？（多选）\n\nA. 代码编译和转译\nB. 资源打包和压缩\nC. 代码分割和优化\nD. 生成静态文件",
     "A,B,C,D", "multiple_choice", "easy", "前端页面开发"),

    # 用例管理模块 (7题)
    ("测试用例通常包含哪些核心字段？",
     "测试用例通常包含哪些核心字段？（多选）\n\nA. 用例标题\nB. 前置条件\nC. 测试步骤\nD. 预期结果",
     "A,B,C,D", "multiple_choice", "easy", "用例管理模块"),
    ("用例管理模块中，测试套件（Test Suite）的作用是什么？",
     "用例管理模块中，测试套件（Test Suite）的作用是什么？\n\nA. 存放单个测试用例\nB. 将多个相关的测试用例组织在一起，便于批量执行\nC. 生成测试报告\nD. 管理测试环境",
     "B", "single_choice", "easy", "用例管理模块"),
    ("测试用例的优先级通常如何划分？",
     "测试用例的优先级通常如何划分？\n\nA. 只有高和低两个级别\nB. 通常分为P0（阻塞）、P1（高）、P2（中）、P3（低）等级别\nC. 没有优先级划分\nD. 只按创建时间排序",
     "B", "single_choice", "easy", "用例管理模块"),
    ("用例管理模块支持Excel导入的主要目的是什么？",
     "用例管理模块支持Excel导入的主要目的是什么？\n\nA. 增加系统复杂度\nB. 方便批量导入历史用例，减少手动录入工作\nC. 仅用于导出数据\nD. 替代数据库功能",
     "B", "single_choice", "easy", "用例管理模块"),
    ("测试用例的评审流程有什么作用？",
     "测试用例的评审流程有什么作用？\n\nA. 增加工作负担\nB. 确保用例覆盖度、准确性和可执行性\nC. 只是形式主义，没有实际作用\nD. 仅用于记录谁编写了用例",
     "B", "single_choice", "easy", "用例管理模块"),
    ("测试用例与需求之间的关联（追溯）有什么意义？",
     "测试用例与需求之间的关联（追溯）有什么意义？\n\nA. 只是形式上的关联\nB. 可以评估需求覆盖率，当需求变更时快速定位相关用例\nC. 增加了系统的复杂度\nD. 只对项目经理有用",
     "B", "single_choice", "medium", "用例管理模块"),
    ("用例管理模块中，步骤编辑功能通常支持哪些操作？",
     "用例管理模块中，步骤编辑功能通常支持哪些操作？（多选）\n\nA. 添加/删除步骤\nB. 调整步骤顺序\nC. 复制步骤\nD. 为步骤添加附件或截图",
     "A,B,C,D", "multiple_choice", "easy", "用例管理模块"),

    # 测试执行引擎与报表 (7题)
    ("测试执行引擎的主要作用是什么？",
     "测试执行引擎的主要作用是什么？\n\nA. 管理测试用例\nB. 调度和执行测试用例，收集执行结果\nC. 生成测试数据\nD. 管理测试环境",
     "B", "single_choice", "easy", "测试执行引擎"),
    ("测试报告中，通过率是如何计算的？",
     "测试报告中，通过率是如何计算的？\n\nA. 通过的用例数 / 总用例数 * 100%\nB. 失败的用例数 / 总用例数 * 100%\nC. 跳过的用例数 / 总用例数 * 100%\nD. 执行的用例数 / 总用例数 * 100%",
     "A", "single_choice", "easy", "测试执行引擎"),
    ("测试执行过程中，哪些因素可能导致测试结果不稳定（Flaky Test）？",
     "测试执行过程中，哪些因素可能导致测试结果不稳定（Flaky Test）？（多选）\n\nA. 测试依赖外部服务（网络、数据库）\nB. 测试数据未隔离，相互干扰\nC. 测试执行顺序影响结果\nD. 测试代码有Bug",
     "A,B,C,D", "multiple_choice", "medium", "测试执行引擎"),
    ("Allure框架主要用于什么？",
     "Allure框架主要用于什么？\n\nA. 测试执行引擎\nB. 测试报告生成框架，生成美观易读的测试报告\nC. 测试用例管理工具\nD. 性能测试工具",
     "B", "single_choice", "easy", "测试报表与可视化"),
    ("测试报表中，通常包含哪些关键信息？",
     "测试报表中，通常包含哪些关键信息？（多选）\n\nA. 测试用例通过率、失败率\nB. 失败的测试用例详情\nC. 测试执行时间\nD. 测试覆盖率",
     "A,B,C,D", "multiple_choice", "easy", "测试报表与可视化"),
    ("在测试执行引擎中，并发执行测试用例有什么优势？",
     "在测试执行引擎中，并发执行测试用例有什么优势？\n\nA. 缩短总体测试执行时间\nB. 提高测试覆盖率\nC. 减少测试数据准备时间\nD. 提高测试报告质量",
     "A", "single_choice", "easy", "测试执行引擎"),
    ("测试执行引擎应该支持哪些触发方式？",
     "测试执行引擎应该支持哪些触发方式？（多选）\n\nA. 手动触发\nB. 定时触发（Cron）\nC. 代码提交触发（Webhook）\nD. 流水线触发",
     "A,B,C,D", "multiple_choice", "easy", "测试执行引擎"),

    # 定时任务与通知 (7题)
    ("APScheduler是什么？",
     "APScheduler是什么？\n\nA. 一个Python定时任务框架\nB. 一个测试框架\nC. 一个Web框架\nD. 一个数据库ORM",
     "A", "single_choice", "easy", "定时任务与通知"),
    ("APScheduler支持哪些触发器类型？",
     "APScheduler支持哪些触发器类型？（多选）\n\nA. date（指定时间执行一次）\nB. interval（固定间隔执行）\nC. cron（类似Linux cron的表达式）\nD. random（随机时间执行）",
     "A,B,C", "multiple_choice", "medium", "定时任务与通知"),
    ("在测试平台中，定时任务通常用于什么场景？",
     "在测试平台中，定时任务通常用于什么场景？（多选）\n\nA. 每天定时执行回归测试\nB. 定时清理过期数据\nC. 定时检查测试环境状态\nD. 定时发送测试报告",
     "A,B,C,D", "multiple_choice", "easy", "定时任务与通知"),
    ("发送邮件通知时，通常需要配置哪些信息？",
     "发送邮件通知时，通常需要配置哪些信息？\n\nA. SMTP服务器地址和端口\nB. 发件人邮箱和密码/授权码\nC. 收件人列表\nD. 以上所有",
     "D", "single_choice", "easy", "定时任务与通知"),
    ("在测试平台中，邮件通知通常发送哪些内容？",
     "在测试平台中，邮件通知通常发送哪些内容？（多选）\n\nA. 测试执行完成通知\nB. 测试失败告警\nC. 每日测试报告\nD. 系统异常通知",
     "A,B,C,D", "multiple_choice", "easy", "定时任务与通知"),
    ("Celery和APScheduler的主要区别是什么？",
     "Celery和APScheduler的主要区别是什么？\n\nA. Celery是分布式任务队列，适合异步任务和定时任务；APScheduler是轻量级定时任务框架\nB. 两者完全相同\nC. Celery只能用于定时任务，APScheduler只能用于异步任务\nD. Celery比APScheduler更复杂，不适合生产环境",
     "A", "single_choice", "medium", "定时任务与通知"),
    ("定时任务执行失败时，应该如何处理？",
     "定时任务执行失败时，应该如何处理？\n\nA. 忽略错误，继续运行\nB. 记录日志，发送告警，并根据配置决定是否重试\nC. 立即停止所有任务\nD. 删除该任务",
     "B", "single_choice", "easy", "定时任务与通知"),

    # 平台部署 (6题)
    ("测试平台部署到生产环境时，以下哪些是必要的安全措施？",
     "测试平台部署到生产环境时，以下哪些是必要的安全措施？（多选）\n\nA. 使用HTTPS\nB. 配置防火墙，只开放必要端口\nC. 数据库使用强密码，禁止root远程登录\nD. 定期备份数据",
     "A,B,C,D", "multiple_choice", "easy", "平台部署"),
    ("使用Docker部署应用时，以下哪个是最佳实践？",
     "使用Docker部署应用时，以下哪个是最佳实践？\n\nA. 在容器内运行数据库\nB. 使用.dockerignore文件排除不必要的文件\nC. 将所有服务打包到一个容器中\nD. 使用latest标签拉取镜像",
     "B", "single_choice", "medium", "平台部署"),
    ("Nginx在测试平台部署中通常承担什么角色？",
     "Nginx在测试平台部署中通常承担什么角色？\n\nA. 反向代理和负载均衡\nB. 数据库\nC. 缓存服务\nD. 任务队列",
     "A", "single_choice", "easy", "平台部署"),
    ("在云平台（如阿里云、AWS）部署应用时，以下哪些服务通常会用到？",
     "在云平台（如阿里云、AWS）部署应用时，以下哪些服务通常会用到？（多选）\n\nA. 云服务器（ECS/EC2）\nB. 云数据库（RDS）\nC. 对象存储（OSS/S3）\nD. 负载均衡（SLB/ELB）",
     "A,B,C,D", "multiple_choice", "easy", "平台部署"),
    ("CI/CD流水线中，部署到生产环境前通常需要什么？",
     "CI/CD流水线中，部署到生产环境前通常需要什么？\n\nA. 直接部署，不需要审批\nB. 手动测试通过后部署\nC. 经过预发布环境验证，并获得批准\nD. 只需要自动化测试通过",
     "C", "single_choice", "medium", "平台部署"),
    ("监控和日志在平台部署中有什么作用？",
     "监控和日志在平台部署中有什么作用？（多选）\n\nA. 实时了解系统运行状态\nB. 快速发现和定位问题\nC. 分析系统性能瓶颈\nD. 审计用户操作",
     "A,B,C,D", "multiple_choice", "easy", "平台部署"),
]

# ========== LP17: 高级测试专题 (50题) ==========
LP17_EXERCISES = [
    # AI测试概述 (8题)
    ("AI在软件测试中的主要应用场景有哪些？",
     "AI在软件测试中的主要应用场景有哪些？（多选）\n\nA. 自动生成测试用例\nB. 智能缺陷预测\nC. 自动化测试执行\nD. 测试报告智能分析",
     "A,B,C,D", "multiple_choice", "easy", "AI测试概述"),
    ("传统自动化测试与AI驱动的测试主要区别是什么？",
     "传统自动化测试与AI驱动的测试主要区别是什么？\n\nA. 传统自动化测试需要手动编写脚本，AI驱动的测试可以自动生成和维护测试用例\nB. AI驱动的测试不需要测试数据\nC. 传统自动化测试比AI驱动的测试更准确\nD. 两者没有区别",
     "A", "single_choice", "easy", "AI测试概述"),
    ("机器学习在测试中的主要作用是什么？",
     "机器学习在测试中的主要作用是什么？\n\nA. 替代测试人员\nB. 通过分析历史数据，预测高风险区域、优化测试策略\nC. 自动修复Bug\nD. 生成测试数据",
     "B", "single_choice", "easy", "AI测试概述"),
    ("深度学习在图像界面测试中可以应用于什么场景？",
     "深度学习在图像界面测试中可以应用于什么场景？\n\nA. 界面布局对比\nB. 视觉回归测试\nC. OCR文字识别\nD. 以上所有",
     "D", "single_choice", "easy", "AI测试概述"),
    ("AI测试工具通常需要哪些数据作为训练数据？",
     "AI测试工具通常需要哪些数据作为训练数据？（多选）\n\nA. 历史测试用例\nB. 缺陷数据\nC. 代码变更记录\nD. 用户行为数据",
     "A,B,C,D", "multiple_choice", "easy", "AI测试概述"),
    ("使用AI生成测试用例时， prompt（提示词）的质量对结果有什么影响？",
     "使用AI生成测试用例时，prompt（提示词）的质量对结果有什么影响？\n\nA. 没有影响，AI会自动优化\nB. 高质量的prompt能生成更准确、更全面的测试用例\nC. prompt越长，生成的测试用例越好\nD. prompt不重要，AI可以猜出用户意图",
     "B", "single_choice", "medium", "AI测试概述"),
    ("以下哪些是AI测试面临的挑战？",
     "以下哪些是AI测试面临的挑战？（多选）\n\nA. 需要大量的训练数据\nB. AI模型的准确性和可解释性\nC. 测试环境的复杂性\nD. 成本较高",
     "A,B,C,D", "multiple_choice", "medium", "AI测试概述"),
    ("AI可以完全替代人工测试。",
     "AI可以完全替代人工测试。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "AI测试概述"),

    # 视觉回归测试 (8题)
    ("视觉回归测试（Visual Regression Testing）主要检测什么？",
     "视觉回归测试（Visual Regression Testing）主要检测什么？\n\nA. 代码逻辑错误\nB. 界面视觉效果的变化（如布局、颜色、字体）\nC. API接口变更\nD. 数据库结构变更",
     "B", "single_choice", "easy", "视觉回归测试"),
    ("视觉回归测试通常如何进行？",
     "视觉回归测试通常如何进行？（多选）\n\nA. 对页面进行截图\nB. 将新截图与基准截图进行像素对比\nC. 标记出视觉差异的区域\nD. 人工确认差异是否为预期的变更",
     "A,B,C,D", "multiple_choice", "easy", "视觉回归测试"),
    ("Percy和Applitools是什么类型的工具？",
     "Percy和Applitools是什么类型的工具？\n\nA. 单元测试框架\nB. 视觉回归测试工具\nC. 性能测试工具\nD. 安全测试工具",
     "B", "single_choice", "easy", "视觉回归测试"),
    ("视觉回归测试中，如何处理动态内容（如时间戳、广告）？",
     "视觉回归测试中，如何处理动态内容（如时间戳、广告）？\n\nA. 无法处理，只能忽略\nB. 使用遮罩（mask）或忽略区域功能\nC. 每次都人工确认\nD. 删除动态内容",
     "B", "single_choice", "medium", "视觉回归测试"),
    ("视觉快照（Snapshot）应该存储在什么地方？",
     "视觉快照（Snapshot）应该存储在什么地方？\n\nA. 本地临时目录\nB. 版本控制系统中（如Git）\nC. 数据库\nD. 云存储",
     "B", "single_choice", "easy", "视觉回归测试"),
    ("视觉回归测试与传统的UI自动化测试主要区别是什么？",
     "视觉回归测试与传统的UI自动化测试主要区别是什么？\n\nA. 视觉回归测试关注界面视觉效果，UI自动化测试关注功能逻辑\nB. 两者完全相同\nC. 视觉回归测试比UI自动化测试更简单\nD. UI自动化测试不需要维护，视觉回归测试需要",
     "A", "single_choice", "medium", "视觉回归测试"),
    ("在进行视觉回归测试时，不同浏览器或设备的渲染差异如何处理？",
     "在进行视觉回归测试时，不同浏览器或设备的渲染差异如何处理？\n\nA. 忽略所有差异\nB. 为每个浏览器/设备分别建立基准快照\nC. 只测试Chrome浏览器\nD. 使用AI自动修复差异",
     "B", "single_choice", "medium", "视觉回归测试"),
    ("视觉回归测试可以检测到所有类型的界面Bug。",
     "视觉回归测试可以检测到所有类型的界面Bug。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "视觉回归测试"),

    # AI用例生成 (8题)
    ("使用大语言模型（LLM）生成测试用例的优势是什么？",
     "使用大语言模型（LLM）生成测试用例的优势是什么？（多选）\n\nA. 可以快速生成大量测试用例\nB. 可以根据需求文档自动生成测试用例\nC. 可以覆盖边缘场景\nD. 可以减少测试人员的重复劳动",
     "A,B,C,D", "multiple_choice", "medium", "AI用例生成"),
    ("使用LLM生成测试用例时，以下哪种prompt方式效果最好？",
     "使用LLM生成测试用例时，以下哪种prompt方式效果最好？\n\nA. 简单描述：帮我生成登录功能的测试用例\nB. 详细描述：提供需求文档、API文档、数据库结构，明确测试重点和边界条件\nC. 只提供代码，让AI自己分析\nD. 不提供任何上下文，让AI自由发挥",
     "B", "single_choice", "easy", "AI用例生成"),
    ("LLM生成的测试用例可能需要哪些后续处理？",
     "LLM生成的测试用例可能需要哪些后续处理？（多选）\n\nA. 人工审核和修正\nB. 补充测试数据\nC. 转换为自动化测试脚本\nD. 通常不需要处理，可以直接使用",
     "A,B,C", "multiple_choice", "medium", "AI用例生成"),
    ("以下哪些信息应该提供给LLM以提高测试用例生成质量？",
     "以下哪些信息应该提供给LLM以提高测试用例生成质量？（多选）\n\nA. 需求文档或用户故事\nB. 接口文档（API）\nC. 数据库表结构\nD. 类似的 historical 测试用例",
     "A,B,C,D", "multiple_choice", "easy", "AI用例生成"),
    ("使用LangChain或类似框架可以如何增强测试用例生成？",
     "使用LangChain或类似框架可以如何增强测试用例生成？\n\nA. 支持从多个数据源（需求文档、代码、历史用例）提取信息\nB. 支持多轮对话优化生成的用例\nC. 支持将用例直接写入测试管理系统\nD. 以上所有",
     "D", "single_choice", "medium", "AI用例生成"),
    ("AI生成的测试用例可以保证100%的缺陷检出率。",
     "AI生成的测试用例可以保证100%的缺陷检出率。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "AI用例生成"),
    ("在TestMaster平台中，集成LLM生成测试用例需要哪些步骤？",
     "在TestMaster平台中，集成LLM生成测试用例需要哪些步骤？（多选）\n\nA. 配置LLM API密钥\nB. 设计prompt模板\nC. 实现用例生成接口\nD. 提供反馈机制以优化生成质量",
     "A,B,C,D", "multiple_choice", "medium", "AI用例生成"),

    # ML缺陷预测 (6题)
    ("机器学习缺陷预测的主要思路是什么？",
     "机器学习缺陷预测的主要思路是什么？\n\nA. 随机猜测哪些模块有缺陷\nB. 基于历史数据（代码复杂度、代码变更频率、历史缺陷等）训练模型，预测未来可能出现缺陷的模块\nC. 让开发人员手动标记缺陷模块\nD. 使用静态代码分析工具",
     "B", "single_choice", "easy", "ML缺陷预测"),
    ("以下哪些特征可以用于缺陷预测模型？",
     "以下哪些特征可以用于缺陷预测模型？（多选）\n\nA. 代码复杂度（圈复杂度、代码行数）\nB. 代码变更频率\nC. 历史缺陷密度\nD. 开发人员经验",
     "A,B,C,D", "multiple_choice", "medium", "ML缺陷预测"),
    ("缺陷预测模型通常使用什么算法？",
     "缺陷预测模型通常使用什么算法？（多选）\n\nA. 逻辑回归\nB. 随机森林\nC. 神经网络\nD. 以上都可以",
     "D", "single_choice", "medium", "ML缺陷预测"),
    ("缺陷预测模型的准确性如何评估？",
     "缺陷预测模型的准确性如何评估？\n\nA. 使用准确率（Accuracy）、精确率（Precision）、召回率（Recall）等指标\nB. 只能由开发人员主观判断\nC. 看模型是否复杂\nD. 看训练时间长短",
     "A", "single_choice", "medium", "ML缺陷预测"),
    ("缺陷预测在测试中的应用价值是什么？",
     "缺陷预测在测试中的应用价值是什么？（多选）\n\nA. 优化测试资源分配，重点测试高风险模块\nB. 减少测试时间\nC. 提高缺陷检出率\nD. 替代人工测试",
     "A,B,C", "multiple_choice", "medium", "ML缺陷预测"),
    ("缺陷预测模型训练完成后，就不需要再更新了。",
     "缺陷预测模型训练完成后，就不需要再更新了。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "ML缺陷预测"),

    # NLP测试应用 (6题)
    ("自然语言处理（NLP）在测试中可以应用于哪些场景？",
     "自然语言处理（NLP）在测试中可以应用于哪些场景？（多选）\n\nA. 从需求文档自动生成测试用例\nB. 分析缺陷报告，自动分类和优先级排序\nC. 智能搜索测试用例\nD. 测试报告自动生成和摘要",
     "A,B,C,D", "multiple_choice", "easy", "NLP测试应用"),
    ("使用NLP进行需求分析的挑战是什么？",
     "使用NLP进行需求分析的挑战是什么？（多选）\n\nA. 需求文档通常不规范，存在歧义\nB. 领域专业术语的处理\nC. 上下文理解\nD. 中英文混合的处理",
     "A,B,C,D", "multiple_choice", "medium", "NLP测试应用"),
    ("聊天机器人（Chatbot）的测试与传统软件测试主要区别是什么？",
     "聊天机器人（Chatbot）的测试与传统软件测试主要区别是什么？\n\nA. Chatbot需要测试对话流的合理性和意图识别准确性\nB. Chatbot不需要测试\nC. 传统软件测试更复杂\nD. 两者没有区别",
     "A", "single_choice", "medium", "NLP测试应用"),
    ("使用NLP技术可以如何实现智能测试用例搜索？",
     "使用NLP技术可以如何实现智能测试用例搜索？\n\nA. 基于关键词匹配\nB. 基于语义相似度匹配\nC. 只能按ID搜索\nD. 只能按创建者搜索",
     "B", "single_choice", "medium", "NLP测试应用"),
    ("在TestMaster平台中，集成NLP功能可以带来哪些改进？",
     "在TestMaster平台中，集成NLP功能可以带来哪些改进？（多选）\n\nA. 智能测试用例推荐\nB. 自动缺陷分类\nC. 自然语言查询测试数据\nD. 测试报告智能摘要",
     "A,B,C,D", "multiple_choice", "medium", "NLP测试应用"),
    ("NLP技术可以完全理解所有业务领域的需求文档。",
     "NLP技术可以完全理解所有业务领域的需求文档。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "NLP测试应用"),

    # 自愈自动化测试 (7题)
    ("自愈自动化测试（Self-Healing Test Automation）是什么？",
     "自愈自动化测试（Self-Healing Test Automation）是什么？\n\nA. 测试脚本可以自动修复Bug\nB. 当UI元素定位失败时，测试框架自动尝试替代定位策略\nC. 测试失败时自动重新执行\nD. 测试脚本可以自我编写",
     "B", "single_choice", "medium", "自愈自动化测试"),
    ("自愈测试通常如何实现？",
     "自愈测试通常如何实现？（多选）\n\nA. 为UI元素创建多个定位器（如ID、CSS、XPath）\nB. 当主要定位器失败时，自动尝试备用定位器\nC. 使用机器学习识别UI元素\nD. 记录每次成功的定位器，优化后续执行",
     "A,B,C,D", "multiple_choice", "medium", "自愈自动化测试"),
    ("自愈测试的主要优势是什么？",
     "自愈测试的主要优势是什么？\n\nA. 减少测试脚本维护成本\nB. 提高测试稳定性\nC. 降低因UI变更导致的测试失败\nD. 以上所有",
     "D", "single_choice", "easy", "自愈自动化测试"),
    ("在实现自愈测试时，以下哪些策略是常用的？",
     "在实现自愈测试时，以下哪些策略是常用的？（多选）\n\nA. 多定位器策略\nB. 动态等待和重试\nC. 基于图像识别的定位\nD. 基于AI的元素识别",
     "A,B,C,D", "multiple_choice", "medium", "自愈自动化测试"),
    ("自愈测试可以完全消除测试脚本的维护工作。",
     "自愈测试可以完全消除测试脚本的维护工作。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "自愈自动化测试"),
    ("TestCafe和Cypress等现代测试框架是否支持自愈测试？",
     "TestCafe和Cypress等现代测试框架是否支持自愈测试？\n\nA. 不支持，需要手动实现\nB. 部分支持，可以通过插件或自定义实现\nC. 完全支持，开箱即用\nD. 只有商业工具才支持",
     "B", "single_choice", "medium", "自愈自动化测试"),
    ("在TestMaster平台中，如何实现测试用例的自愈功能？",
     "在TestMaster平台中，如何实现测试用例的自愈功能？（多选）\n\nA. 记录多个元素定位器\nB. 实现定位器失败后的自动切换逻辑\nC. 提供UI元素变更的检测和提示\nD. 集成AI视觉识别作为备用定位方案",
     "A,B,C,D", "multiple_choice", "hard", "自愈自动化测试"),

    # LLM测试生成 (7题)
    ("大语言模型（LLM）如GPT-4、Claude在测试中的主要作用是什么？",
     "大语言模型（LLM）如GPT-4、Claude在测试中的主要作用是什么？（多选）\n\nA. 根据需求自动生成测试用例\nB. 生成自动化测试脚本\nC. 分析缺陷报告，提供修复建议\nD. 生成测试数据",
     "A,B,C,D", "multiple_choice", "easy", "LLM测试生成"),
    ("使用LLM生成测试脚本时，以下哪种方式效果最好？",
     "使用LLM生成测试脚本时，以下哪种方式效果最好？\n\nA. 只告诉LLM要测试什么功能\nB. 提供详细的上下文：页面结构、API文档、示例代码\nC. 让LLM自己猜测实现方式\nD. 使用通用的prompt模板",
     "B", "single_choice", "easy", "LLM测试生成"),
    ("LangChain框架在LLM测试生成中的应用是什么？",
     "LangChain框架在LLM测试生成中的应用是什么？（多选）\n\nA. 连接多个LLM调用，实现复杂任务\nB. 从外部数据源（如需求文档、代码仓库）提取信息\nC. 实现记忆功能，多轮优化生成的测试\nD. 自动化执行生成的测试",
     "A,B,C", "multiple_choice", "medium", "LLM测试生成"),
    ("使用LLM生成测试用例时，如何评估生成质量？",
     "使用LLM生成测试用例时，如何评估生成质量？\n\nA. 只能人工审查\nB. 使用BLEU、ROUGE等指标对比参考用例\nC. 执行生成的测试用例，看是否通过\nD. 以上都可以",
     "D", "single_choice", "medium", "LLM测试生成"),
    ("LLM可以生成任何类型的测试，包括性能测试和安全测试。",
     "LLM可以生成任何类型的测试，包括性能测试和安全测试。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "LLM测试生成"),
    ("在TestMaster平台中，集成LLM测试生成功能需要哪些组件？",
     "在TestMaster平台中，集成LLM测试生成功能需要哪些组件？（多选）\n\nA. LLM API集成（OpenAI、Anthropic等）\nB. Prompt模板管理\nC. 生成结果的审核和编辑界面\nD. 与现有测试用例库的关联",
     "A,B,C,D", "multiple_choice", "medium", "LLM测试生成"),
    ("使用LLM生成测试的主要成本是什么？",
     "使用LLM生成测试的主要成本是什么？（多选）\n\nA. API调用费用\nB. 生成结果的人工审核时间\nC. 计算资源成本\nD. 数据存储成本",
     "A,B", "multiple_choice", "easy", "LLM测试生成"),
]

# ========== LP18: 前沿与展望 (50题) ==========
LP18_EXERCISES = [
    # 测试架构师概述 (8题)
    ("测试架构师的主要职责是什么？",
     "测试架构师的主要职责是什么？（多选）\n\nA. 制定测试策略和测试架构\nB. 选择合适的技术栈和工具\nC. 指导测试团队的技术成长\nD. 设计测试平台和基础设施",
     "A,B,C,D", "multiple_choice", "easy", "测试架构师概述"),
    ("测试架构师与普通测试工程师的主要区别是什么？",
     "测试架构师与普通测试工程师的主要区别是什么？\n\nA. 测试架构师只做管理工作\nB. 测试架构师需要具备更广阔的技术视野和系统设计能力\nC. 测试工程师比测试架构师技术更强\nD. 两者没有区别",
     "B", "single_choice", "easy", "测试架构师概述"),
    ("以下哪些能力是测试架构师需要具备的？",
     "以下哪些能力是测试架构师需要具备的？（多选）\n\nA. 深入理解测试理论和方法论\nB. 熟悉各种测试工具和技术\nC. 系统架构设计能力\nD. 团队管理和沟通能力",
     "A,B,C,D", "multiple_choice", "easy", "测试架构师概述"),
    ("测试架构师在技术选型时，应该考虑哪些因素？",
     "测试架构师在技术选型时，应该考虑哪些因素？（多选）\n\nA. 团队技术栈和能力\nB. 工具的社区活跃度和可维护性\nC. 成本和 licensing\nD. 与现有系统的集成能力",
     "A,B,C,D", "multiple_choice", "medium", "测试架构师概述"),
    ("测试架构师需要编写代码吗？",
     "测试架构师需要编写代码吗？\n\nA. 不需要，只做架构设计\nB. 需要，测试架构师应该保持技术实践，理解一线问题\nC. 只需要写设计文档\nD. 只需要review别人的代码",
     "B", "single_choice", "easy", "测试架构师概述"),
    ("测试架构师如何推动测试自动化转型？",
     "测试架构师如何推动测试自动化转型？（多选）\n\nA. 制定自动化测试策略和路线图\nB. 选择合适的自动化测试工具\nC. 培训团队自动化测试技能\nD. 建立自动化测试最佳实践和规范",
     "A,B,C,D", "multiple_choice", "medium", "测试架构师概述"),
    ("测试架构师在敏捷/DevOps环境中的角色是什么？",
     "测试架构师在敏捷/DevOps环境中的角色是什么？\n\nA. 只需要关注测试执行\nB. 需要将测试左移，嵌入到开发和部署流程中\nC. 只需要编写测试计划\nD. 只需要管理测试团队",
     "B", "single_choice", "medium", "测试架构师概述"),
    ("测试架构师应该具备业务理解能力。",
     "测试架构师应该具备业务理解能力。\n\nA. 正确\nB. 错误",
     "A", "true_false", "easy", "测试架构师概述"),

    # 可测试性设计 (8题)
    ("可测试性设计（Design for Testability）是什么？",
     "可测试性设计（Design for Testability）是什么？\n\nA. 系统架构设计时，考虑如何更容易地对系统进行全面测试\nB. 只关注单元测试\nC. 使用特定的测试框架\nD. 编写大量的测试用例",
     "A", "single_choice", "easy", "可测试性设计"),
    ("以下哪些是可测试性设计的常见原则？",
     "以下哪些是可测试性设计的常见原则？（多选）\n\nA. 依赖注入，便于Mock\nB. 提供测试钩子（Test Hook）或测试接口\nC. 避免硬编码，使用配置\nD. 模块解耦，便于单独测试",
     "A,B,C,D", "multiple_choice", "easy", "可测试性设计"),
    ("在微服务架构中，如何提高可测试性？",
     "在微服务架构中，如何提高可测试性？（多选）\n\nA. 使用契约测试（Contract Testing）\nB. 提供Mock服务或测试环境\nC. 支持服务独立部署和测试\nD. 使用容器化技术隔离测试环境",
     "A,B,C,D", "multiple_choice", "medium", "可测试性设计"),
    ("测试驱动开发（TDD）与可测试性设计的关系是什么？",
     "测试驱动开发（TDD）与可测试性设计的关系是什么？\n\nA. TDD强制要求代码具有可测试性\nB. 两者没有关系\nC. TDD只适用于单元测试\nD. 可测试性设计只适用于系统测试",
     "A", "single_choice", "medium", "可测试性设计"),
    ("在前端开发中，如何提高可测试性？",
     "在前端开发中，如何提高可测试性？（多选）\n\nA. 组件化设计，每个组件职责单一\nB. 使用状态管理，便于测试和调试\nC. 避免直接操作DOM，使用数据驱动\nD. 提供Mock数据接口",
     "A,B,C,D", "multiple_choice", "medium", "可测试性设计"),
    ("可测试性设计会增加系统的复杂度。",
     "可测试性设计会增加系统的复杂度。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "可测试性设计"),
    ("在API设计中，如何提高可测试性？",
     "在API设计中，如何提高可测试性？（多选）\n\nA. 提供详细的API文档\nB. 支持测试环境/沙箱环境\nC. 提供测试用的API密钥\nD. 返回详细的错误信息和状态码",
     "A,B,C,D", "multiple_choice", "medium", "可测试性设计"),
    ("可测试性设计应该在哪个阶段考虑？",
     "可测试性设计应该在哪个阶段考虑？\n\nA. 编码完成后\nB. 测试阶段\nC. 架构设计和详细设计阶段\nD. 上线后",
     "C", "single_choice", "easy", "可测试性设计"),

    # 微服务测试 (7题)
    ("微服务架构中，契约测试（Contract Testing）的主要作用是什么？",
     "微服务架构中，契约测试（Contract Testing）的主要作用是什么？\n\nA. 测试微服务的功能逻辑\nB. 验证服务之间的接口约定是否满足\nC. 测试数据库性能\nD. 测试用户界面",
     "B", "single_choice", "medium", "微服务测试"),
    ("在微服务测试中，以下哪些是常用的测试策略？",
     "在微服务测试中，以下哪些是常用的测试策略？（多选）\n\nA. 单元测试\nB. 集成测试\nC. 契约测试\nD. 端到端测试",
     "A,B,C,D", "multiple_choice", "medium", "微服务测试"),
    ("服务虚拟化（Service Virtualization）在微服务测试中的作用是什么？",
     "服务虚拟化（Service Virtualization）在微服务测试中的作用是什么？\n\nA. 替代所有真实服务\nB. 模拟依赖服务的行为，使测试不依赖真实服务\nC. 提高服务性能\nD. 减少服务数量",
     "B", "single_choice", "medium", "微服务测试"),
    ("在微服务架构中，如何实现测试环境的隔离？",
     "在微服务架构中，如何实现测试环境的隔离？（多选）\n\nA. 使用Docker容器化每个服务\nB. 使用Kubernetes命名空间隔离\nC. 使用Mock服务替代依赖\nD. 每个测试使用独立的数据",
     "A,B,C,D", "multiple_choice", "medium", "微服务测试"),
    ("微服务中的雪崩测试（Chaos Testing）是什么？",
     "微服务中的雪崩测试（Chaos Testing）是什么？\n\nA. 测试系统在故障情况下的恢复能力\nB. 测试系统的性能极限\nC. 测试系统的安全漏洞\nD. 测试系统的兼容性",
     "A", "single_choice", "hard", "微服务测试"),
    ("在微服务测试中，如何管理测试数据？",
     "在微服务测试中，如何管理测试数据？（多选）\n\nA. 每个服务使用独立的测试数据库\nB. 使用测试数据工厂（Test Data Factory）\nC. 测试前准备数据，测试后清理数据\nD. 使用真实的生产数据副本",
     "A,B,C", "multiple_choice", "medium", "微服务测试"),
    ("微服务测试比单体应用测试更简单。",
     "微服务测试比单体应用测试更简单。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "微服务测试"),

    # 分层测试体系 (7题)
    ("测试金字塔（Test Pyramid）通常分为哪几层？",
     "测试金字塔（Test Pyramid）通常分为哪几层？\n\nA. 单元测试、集成测试、端到端测试\nB. 功能测试、性能测试、安全测试\nC. 手动测试、自动化测试、探索性测试\nD. 黑盒测试、白盒测试、灰盒测试",
     "A", "single_choice", "easy", "分层测试体系"),
    ("根据测试金字塔，哪种测试应该最多？",
     "根据测试金字塔，哪种测试应该最多？\n\nA. 端到端测试\nB. 集成测试\nC. 单元测试\nD. 手动测试",
     "C", "single_choice", "easy", "分层测试体系"),
    ("为什么端到端测试通常比单元测试更慢、更脆弱？",
     "为什么端到端测试通常比单元测试更慢、更脆弱？（多选）\n\nA. 需要启动整个应用和环境\nB. 涉及多个组件和网络调用\nC. 测试数据准备复杂\nD. 调试困难，错误定位慢",
     "A,B,C,D", "multiple_choice", "medium", "分层测试体系"),
    ("敏捷测试象限（Agile Testing Quadrants）是谁提出的？",
     "敏捷测试象限（Agile Testing Quadrants）是谁提出的？\n\nA. Mike Cohn\nB. Lisa Crispin和Janet Gregory\nC. Kent Beck\nD. Martin Fowler",
     "B", "single_choice", "medium", "分层测试体系"),
    ("测试冰淇淋筒（Test Ice Cream Cone）反模式是什么？",
     "测试冰淇淋筒（Test Ice Cream Cone）反模式是什么？\n\nA. 端到端测试最多，单元测试最少，维护成本高\nB. 单元测试最多，端到端测试最少\nC. 只有手动测试\nD. 没有测试",
     "A", "single_choice", "medium", "分层测试体系"),
    ("如何推动团队从冰淇淋筒模式转向金字塔模式？",
     "如何推动团队从冰淇淋筒模式转向金字塔模式？（多选）\n\nA. 增加单元测试覆盖率\nB. 将端到端测试替换为集成测试和单元测试\nC. 引入测试左移实践\nD. 培训团队测试技能",
     "A,B,C,D", "multiple_choice", "hard", "分层测试体系"),
    ("测试金字塔适用于所有类型的项目。",
     "测试金字塔适用于所有类型的项目。\n\nA. 正确\nB. 错误",
     "B", "true_false", "medium", "分层测试体系"),

    # 质量度量模型 (7题)
    ("软件质量度量通常包含哪些维度？",
     "软件质量度量通常包含哪些维度？（多选）\n\nA. 代码质量（覆盖率、复杂度、重复率）\nB. 测试质量（用例覆盖率、缺陷检出率）\nC. 过程质量（缺陷密度、修复周期）\nD. 用户满意度",
     "A,B,C,D", "multiple_choice", "easy", "质量度量模型"),
    ("缺陷密度通常如何计算？",
     "缺陷密度通常如何计算？\n\nA. 缺陷数量 / 代码行数（KLOC）\nB. 缺陷数量 / 测试用例数\nC. 缺陷数量 / 开发人员数\nD. 缺陷数量 / 项目周期",
     "A", "single_choice", "easy", "质量度量模型"),
    ("测试覆盖率100%意味着什么？",
     "测试覆盖率100%意味着什么？\n\nA. 系统没有Bug了\nB. 所有代码都被测试到了，但不代表所有场景都测试到了\nC. 不需要再测试了\nD. 可以立即发布",
     "B", "single_choice", "easy", "质量度量模型"),
    ("以下哪些是常用的质量度量指标？",
     "以下哪些是常用的质量度量指标？（多选）\n\nA. 缺陷逃逸率（生产环境发现的缺陷比例）\nB. 缺陷修复周期\nC. 测试自动化率\nD. 代码覆盖率",
     "A,B,C,D", "multiple_choice", "easy", "质量度量模型"),
    ("质量度量模型应该如何使用？",
     "质量度量模型应该如何使用？\n\nA. 作为团队考核的唯一标准\nB. 作为改进测试过程和产品质量的参考\nC. 只关注数字，不关注实际质量\nD. 只用于向上级汇报",
     "B", "single_choice", "medium", "质量度量模型"),
    ("在TestMaster平台中，如何实现质量度量功能？",
     "在TestMaster平台中，如何实现质量度量功能？（多选）\n\nA. 自动收集测试执行数据\nB. 计算各类质量指标\nC. 生成质量趋势图表\nD. 提供质量报告导出",
     "A,B,C,D", "multiple_choice", "medium", "质量度量模型"),
    ("质量度量指标越多越好。",
     "质量度量指标越多越好。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "质量度量模型"),

    # 缺陷分析与RCA (7题)
    ("根本原因分析（RCA，Root Cause Analysis）的主要目标是什么？",
     "根本原因分析（RCA，Root Cause Analysis）的主要目标是什么？\n\nA. 找到缺陷的根本原因，防止类似问题再次发生\nB. 找到导致缺陷的开发人员\nC. 快速修复缺陷\nD. 记录缺陷的详细信息",
     "A", "single_choice", "easy", "缺陷分析与RCA"),
    ("5 Whys（五个为什么）分析方法的主要思路是什么？",
     "5 Whys（五个为什么）分析方法的主要思路是什么？\n\nA. 问五次为什么，层层深入，找到根本原因\nB. 问为什么五次，然后放弃\nC. 只问表面原因\nD. 让开发人员自己解释",
     "A", "single_choice", "easy", "缺陷分析与RCA"),
    ("鱼骨图（Fishbone Diagram）在缺陷分析中的作用是什么？",
     "鱼骨图（Fishbone Diagram）在缺陷分析中的作用是什么？\n\nA. 美化缺陷报告\nB. 系统化地分析导致缺陷的各类原因（人、流程、工具、环境等）\nC. 记录缺陷的修复过程\nD. 跟踪缺陷状态",
     "B", "single_choice", "medium", "缺陷分析与RCA"),
    ("缺陷分析通常包含哪些内容？",
     "缺陷分析通常包含哪些内容？（多选）\n\nA. 缺陷的分布（模块、严重程度、类型）\nB. 缺陷的根本原因\nC. 缺陷的修复周期和成本\nD. 缺陷的趋势分析",
     "A,B,C,D", "multiple_choice", "easy", "缺陷分析与RCA"),
    ("预防性措施（Preventive Action）与纠正措施（Corrective Action）的区别是什么？",
     "预防性措施（Preventive Action）与纠正措施（Corrective Action）的区别是什么？\n\nA. 预防性措施防止未来类似问题发生，纠正措施修复当前问题\nB. 两者完全相同\nC. 纠正措施更重要\nD. 预防性措施不重要",
     "A", "single_choice", "medium", "缺陷分析与RCA"),
    ("在TestMaster平台中，如何支持缺陷分析功能？",
     "在TestMaster平台中，如何支持缺陷分析功能？（多选）\n\nA. 提供缺陷统计图表\nB. 支持缺陷分类和标签\nC. 记录缺陷的RCA和预防措施\nD. 提供缺陷趋势分析",
     "A,B,C,D", "multiple_choice", "medium", "缺陷分析与RCA"),
    ("所有缺陷都需要进行RCA分析。",
     "所有缺陷都需要进行RCA分析。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "缺陷分析与RCA"),

    # TMMi成熟度模型 (6题)
    ("TMMi（Test Maturity Model integration）是什么？",
     "TMMi（Test Maturity Model integration）是什么？\n\nA. 一个测试成熟度模型，用于评估和改进测试过程\nB. 一个测试工具\nC. 一个测试框架\nD. 一个测试标准",
     "A", "single_choice", "easy", "TMMi成熟度模型"),
    ("TMMi成熟度级别分为哪几个等级？",
     "TMMi成熟度级别分为哪几个等级？\n\nA. 1-5级，从初始级到优化级\nB. A-D级\nC. 初级、中级、高级\nD. 只有两个级别：成熟和不成熟",
     "A", "single_choice", "easy", "TMMi成熟度模型"),
    ("TMMi 3级（已定义级）的主要特征是什么？",
     "TMMi 3级（已定义级）的主要特征是什么？\n\nA. 测试过程已标准化，有组织的测试策略和标准\nB. 没有测试过程\nC. 只有临时测试\nD. 测试完全自动化",
     "A", "single_choice", "medium", "TMMi成熟度模型"),
    ("以下哪些是TMMi评估的常见领域？",
     "以下哪些是TMMi评估的常见领域？（多选）\n\nA. 测试策略和标准\nB. 测试环境和工具\nC. 测试组织和人员\nD. 测试度量和质量控制",
     "A,B,C,D", "multiple_choice", "medium", "TMMi成熟度模型"),
    ("如何提高组织的TMMi成熟度？",
     "如何提高组织的TMMi成熟度？（多选）\n\nA. 进行TMMi评估，了解当前成熟度水平\nB. 制定改进计划，针对性地提升测试过程\nC. 培训团队，建立测试标准\nD. 引入合适的测试工具和支持",
     "A,B,C,D", "multiple_choice", "medium", "TMMi成熟度模型"),
    ("TMMi成熟度越高，测试成本越低。",
     "TMMi成熟度越高，测试成本越低。\n\nA. 正确\nB. 错误",
     "A", "true_false", "easy", "TMMi成熟度模型"),

    # 测试团队与工具链 (7题)
    ("一个高效的测试团队通常包含哪些角色？",
     "一个高效的测试团队通常包含哪些角色？（多选）\n\nA. 测试经理/ leader\nB. 测试开发工程师\nC. 自动化测试工程师\nD. 性能/安全测试专家",
     "A,B,C,D", "multiple_choice", "easy", "测试团队与工具链"),
    ("测试工具链通常包含哪些组成部分？",
     "测试工具链通常包含哪些组成部分？（多选）\n\nA. 测试用例管理工具\nB. 缺陷管理工具\nC. 自动化测试框架\nD. 持续集成工具",
     "A,B,C,D", "multiple_choice", "easy", "测试团队与工具链"),
    ("如何选择合适的测试工具？",
     "如何选择合适的测试工具？（多选）\n\nA. 评估工具的功能是否满足需求\nB. 考虑工具的学习成本和团队技能\nC. 评估工具的社区支持和可维护性\nD. 考虑工具的成本和ROI",
     "A,B,C,D", "multiple_choice", "medium", "测试团队与工具链"),
    ("测试团队的绩效考核应该关注哪些指标？",
     "测试团队的绩效考核应该关注哪些指标？（多选）\n\nA. 缺陷发现和预防能力\nB. 测试覆盖率和质量\nC. 测试效率和自动化程度\nD. 团队协作和成长",
     "A,B,C,D", "multiple_choice", "medium", "测试团队与工具链"),
    ("如何培养测试团队的技术能力？",
     "如何培养测试团队的技术能力？（多选）\n\nA. 定期技术分享和培训\nB. 鼓励参与开源项目\nC. 提供实践机会和挑战性任务\nD. 建立技术晋升通道",
     "A,B,C,D", "multiple_choice", "easy", "测试团队与工具链"),
    ("测试团队应该完全独立，还是与开发团队紧密协作？",
     "测试团队应该完全独立，还是与开发团队紧密协作？\n\nA. 应该完全独立，保持客观\nB. 应该与开发团队紧密协作，实现质量内建\nC. 只负责测试执行\nD. 只负责测试计划",
     "B", "single_choice", "medium", "测试团队与工具链"),
    ("测试工具越多，测试效果越好。",
     "测试工具越多，测试效果越好。\n\nA. 正确\nB. 错误",
     "B", "true_false", "easy", "测试团队与工具链"),
]


def main():
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查LP15-LP18是否存在
    for lp_id in [15, 16, 17, 18]:
        cursor.execute("SELECT id FROM learning_paths WHERE id = ?", (lp_id,))
        if not cursor.fetchone():
            print(f"警告: LP{lp_id} 不存在，跳过")
    
    # 插入LP15习题
    print("开始插入 LP15 习题...")
    count = 0
    for ex in LP15_EXERCISES:
        try:
            # ex结构: (title, description, solution, exercise_type, difficulty, category, lang)
            title, description, solution, exercise_type, difficulty, category = ex[:6]
            lang = ex[6] if len(ex) > 6 else "中文"
            insert_exercise(cursor, title, description, solution, exercise_type, difficulty, 15, category, lang)
            count += 1
        except Exception as e:
            print(f"插入失败: {ex[0][:30]}... 错误: {e}")
    print(f"LP15 插入了 {count} 道习题")
    
    # 插入LP16习题
    print("开始插入 LP16 习题...")
    count = 0
    for ex in LP16_EXERCISES:
        try:
            # ex结构: (title, description, solution, exercise_type, difficulty, category)
            title, description, solution, exercise_type, difficulty, category = ex[:6]
            lang = ex[6] if len(ex) > 6 else "中文"
            insert_exercise(cursor, title, description, solution, exercise_type, difficulty, 16, category, lang)
            count += 1
        except Exception as e:
            print(f"插入失败: {ex[0][:30]}... 错误: {e}")
    print(f"LP16 插入了 {count} 道习题")
    
    # 插入LP17习题
    print("开始插入 LP17 习题...")
    count = 0
    for ex in LP17_EXERCISES:
        try:
            # ex结构: (title, description, solution, exercise_type, difficulty, category)
            title, description, solution, exercise_type, difficulty, category = ex[:6]
            lang = ex[6] if len(ex) > 6 else "中文"
            insert_exercise(cursor, title, description, solution, exercise_type, difficulty, 17, category, lang)
            count += 1
        except Exception as e:
            print(f"插入失败: {ex[0][:30]}... 错误: {e}")
    print(f"LP17 插入了 {count} 道习题")
    
    # 插入LP18习题
    print("开始插入 LP18 习题...")
    count = 0
    for ex in LP18_EXERCISES:
        try:
            # ex结构: (title, description, solution, exercise_type, difficulty, category)
            title, description, solution, exercise_type, difficulty, category = ex[:6]
            lang = ex[6] if len(ex) > 6 else "中文"
            insert_exercise(cursor, title, description, solution, exercise_type, difficulty, 18, category, lang)
            count += 1
        except Exception as e:
            print(f"插入失败: {ex[0][:30]}... 错误: {e}")
    print(f"LP18 插入了 {count} 道习题")
    
    conn.commit()
    
    # 验证总数
    cursor.execute("SELECT learning_path_id, COUNT(*) FROM exercises WHERE learning_path_id IN (15,16,17,18) GROUP BY learning_path_id")
    results = cursor.fetchall()
    print("\n验证插入结果:")
    for lp_id, count in results:
        print(f"  LP{lp_id}: {count} 道习题")
    
    conn.close()
    print("\n完成！")


if __name__ == "__main__":
    main()
