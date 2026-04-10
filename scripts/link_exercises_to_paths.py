# 将习题关联到学习路径
import sys
sys.path.insert(0, '.')

from backend.app import create_app
from backend.models.models import db, LearningPath, Exercise

app = create_app()

with app.app_context():
    # 获取所有学习路径
    paths = {lp.stage: lp for lp in LearningPath.query.all()}
    
    # 获取所有习题并按阶段分组
    exercises_by_stage = {}
    for exercise in Exercise.query.all():
        stage = exercise.stage
        if stage not in exercises_by_stage:
            exercises_by_stage[stage] = []
        exercises_by_stage[stage].append(exercise)
    
    # 将习题关联到对应的学习路径
    for stage, path in paths.items():
        if stage in exercises_by_stage:
            exercises = exercises_by_stage[stage]
            for exercise in exercises:
                exercise.learning_path_id = path.id
            path.exercise_count = len(exercises)
            print(f'阶段{stage}: 关联了 {len(exercises)} 道习题到 "{path.title}"')
        else:
            print(f'阶段{stage}: 没有习题')
    
    db.session.commit()
    
    # 验证结果
    print('\n=== 关联结果验证 ===')
    for stage in range(1, 6):
        path = paths.get(stage)
        if path:
            count = Exercise.query.filter_by(learning_path_id=path.id).count()
            print(f'阶段{stage}: {path.title} - 关联习题数: {count}')
    
    print('\n习题关联完成！')
