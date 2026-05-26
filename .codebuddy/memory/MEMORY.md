# TestMaster 项目记忆

## 项目信息
- 项目名：TestMaster - 智能测试管理平台
- GitHub：https://github.com/pengzeya68-collab/test
- 服务器：34.150.26.84 (root, Debian)
- 部署方式：Docker Compose (nginx + FastAPI + Celery + Redis)

## 管理员账号
- 用户名：admin
- 密码：admin123456

## 访问地址
- 前台：http://34.150.26.84
- 后台：http://34.150.26.84/admin/login
- API文档：http://34.150.26.84:5001/api/docs

## 部署关键修复
- auth_service.py → authenticate_user 需要 selectinload(User.role_obj)，否则登录报 DetachedInstanceError
- requirements.txt 需要完整依赖列表
- Dockerfile 用 root 运行避免权限问题
- docker-compose.yml 不含 version 属性
- nginx.conf 提供前端托管 + API 代理

## 用户偏好
- 用户在中国，GitHub 需要代理 127.0.0.1:10808
- 使用 CodeBuddy（不是 VS Code）
- 使用 FinalShell 连接服务器
- 偏好 CI/CD 自动化部署
