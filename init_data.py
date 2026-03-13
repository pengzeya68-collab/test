# Initialize database with sample data
from app import create_app, db
from models import LearningPath, Exercise, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("🔄 Creating tables...")
    db.create_all()
    
    # Check if data already exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("👤 Creating admin user...")
        admin_user = User(
            username='admin',
            email='admin@testmaster.com',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        db.session.commit()
    
    # Check if learning paths exist
    existing_paths = LearningPath.query.count()
    if existing_paths > 0:
        print(f"✅ {existing_paths} learning paths already exist. Skipping initialization.")
    else:
        print("📚 Creating sample learning paths...")
        
        paths = [
            LearningPath(
                title='Python 入门到精通',
                description='从零基础开始学习Python编程，掌握核心语法、常用库和实战项目开发。适合完全没有编程经验的初学者。',
                language='Python',
                difficulty='beginner',
                estimated_hours=40,
                is_public=True,
                user_id=admin_user.id
            ),
            LearningPath(
                title='JavaScript 全栈开发',
                description='学习前端JavaScript基础、ES6+新特性、Node.js后端开发，打造全栈开发能力。',
                language='JavaScript',
                difficulty='intermediate',
                estimated_hours=60,
                is_public=True,
                user_id=admin_user.id
            ),
            LearningPath(
                title='Java 企业级开发',
                description='深入学习Java面向对象编程、Spring框架、微服务架构，成为企业级Java开发工程师。',
                language='Java',
                difficulty='advanced',
                estimated_hours=80,
                is_public=True,
                user_id=admin_user.id
            ),
            LearningPath(
                title='数据结构入门',
                description='学习基础数据结构：数组、链表、栈、队列、树、图，打下扎实的计算机基础。',
                language='Python',
                difficulty='beginner',
                estimated_hours=30,
                is_public=True,
                user_id=admin_user.id
            ),
            LearningPath(
                title='算法进阶训练',
                description='深入学习排序、查找、动态规划、贪心算法，提升算法思维，备战技术面试。',
                language='C++',
                difficulty='advanced',
                estimated_hours=50,
                is_public=True,
                user_id=admin_user.id
            ),
            LearningPath(
                title='前端框架实战',
                description='学习Vue3/React框架，掌握组件化开发、状态管理、路由配置，完成实战项目。',
                language='JavaScript',
                difficulty='intermediate',
                estimated_hours=45,
                is_public=True,
                user_id=admin_user.id
            )
        ]
        
        for path in paths:
            db.session.add(path)
        
        db.session.commit()
        print(f"✅ Created {len(paths)} learning paths!")
        
        # Create some exercises
        print("💪 Creating sample exercises...")
        exercises = [
            Exercise(
                title='Hello World',
                description='编写程序输出 "Hello World!"，这是编程的第一步。',
                difficulty='easy',
                language='Python',
                is_public=True,
                user_id=admin_user.id,
                learning_path_id=paths[0].id
            ),
            Exercise(
                title='变量与数据类型',
                description='学习Python中的变量定义、整数、浮点数、字符串、布尔值等基本数据类型。',
                difficulty='easy',
                language='Python',
                is_public=True,
                user_id=admin_user.id,
                learning_path_id=paths[0].id
            ),
            Exercise(
                title='两数之和',
                description='给定一个整数数组和一个目标值，找出数组中和为目标值的两个数并返回它们的索引。',
                difficulty='easy',
                language='Python',
                is_public=True,
                user_id=admin_user.id,
                learning_path_id=paths[0].id
            ),
            Exercise(
                title='数组操作基础',
                description='学习JavaScript数组的创建、访问、添加、删除、遍历等基本操作。',
                difficulty='easy',
                language='JavaScript',
                is_public=True,
                user_id=admin_user.id,
                learning_path_id=paths[1].id
            ),
            Exercise(
                title='类与对象基础',
                description='学习Java中的类定义、对象创建、属性和方法、构造器等面向对象基础概念。',
                difficulty='easy',
                language='Java',
                is_public=True,
                user_id=admin_user.id,
                learning_path_id=paths[2].id
            )
        ]
        
        for exercise in exercises:
            db.session.add(exercise)
        
        db.session.commit()
        print(f"✅ Created {len(exercises)} exercises!")
    
    print("\n🎉 Database initialization complete!")
