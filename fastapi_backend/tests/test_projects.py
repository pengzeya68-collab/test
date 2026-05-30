"""
测试项目实战空间API集成测试
"""

import pytest_asyncio

from fastapi_backend.models.models import (
    User,
    LearningPath,
    Exercise,
    ProjectSpace,
    ProjectTask,
    ProjectResource,
)


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        is_active=True,
        is_admin=False,
        score=0,
        level=1,
        study_time=0,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_path(db_session):
    path = LearningPath(
        id=1,
        title="测试学习路径",
        description="用于测试的学习路径",
        difficulty="medium",
        language="zh",
        is_public=True,
    )
    db_session.add(path)
    await db_session.flush()

    exercise = Exercise(
        id=1,
        learning_path_id=path.id,
        title="测试习题",
        description="习题描述",
        exercise_type="coding",
        difficulty="easy",
        language="zh",
    )
    db_session.add(exercise)
    await db_session.commit()
    await db_session.refresh(path)
    return path


@pytest_asyncio.fixture
async def test_project(db_session, test_path, test_user):
    project = ProjectSpace(
        learning_path_id=test_path.id,
        title="测试项目",
        description="用于测试的项目",
        overview="项目概述",
        difficulty="medium",
        status="published",
        estimated_hours=4,
        sort_order=0,
    )
    db_session.add(project)
    await db_session.flush()

    tasks_data = [
        ("测试点设计", "test_point_design", 10),
        ("测试用例设计", "test_case_design", 15),
        ("接口调试", "api_debug", 10),
        ("自动化执行", "auto_execution", 20),
        ("缺陷分析", "defect_analysis", 15),
        ("项目总结", "project_summary", 30),
    ]
    for idx, (title, ttype, score) in enumerate(tasks_data):
        task = ProjectTask(
            project_id=project.id,
            title=title,
            description=f"{title}任务描述",
            task_type=ttype,
            requirements=f"{title}要求",
            hints="提示内容",
            score=score,
            sort_order=idx,
        )
        db_session.add(task)

    res = ProjectResource(
        project_id=project.id,
        title="项目文档",
        resource_type="document",
        content="这是项目文档内容",
        sort_order=0,
    )
    db_session.add(res)

    await db_session.commit()
    await db_session.refresh(project)
    return project


def make_auth_override(user):
    async def override():
        return user

    return override


class TestProjectList:
    def test_list_projects_empty(self, client, test_user, test_path):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get(f"/api/v1/learning-paths/{test_path.id}/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["path_id"] == test_path.id
        assert data["projects"] == []

    def test_list_projects_with_data(self, client, test_user, test_path, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get(f"/api/v1/learning-paths/{test_path.id}/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 1
        assert data["projects"][0]["title"] == "测试项目"
        assert data["projects"][0]["task_count"] == 6

    def test_list_projects_path_not_found(self, client, test_user):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get("/api/v1/learning-paths/9999/projects")
        assert response.status_code == 404


class TestProjectDetail:
    def test_get_project(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试项目"
        assert len(data["tasks"]) == 6
        assert len(data["resources"]) == 1
        assert data["progress"]["total_tasks"] == 6
        assert data["progress"]["completed_tasks"] == 0

    def test_get_project_not_found(self, client, test_user):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get("/api/v1/projects/9999")
        assert response.status_code == 404


class TestProjectTasks:
    def test_get_tasks(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get(f"/api/v1/projects/{test_project.id}/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 6
        assert data["tasks"][0]["submission"] is None

    def test_get_resources(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get(f"/api/v1/projects/{test_project.id}/resources")
        assert response.status_code == 200
        data = response.json()
        assert len(data["resources"]) == 1
        assert data["resources"][0]["title"] == "项目文档"


class TestProjectProgress:
    def test_get_progress(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get(f"/api/v1/projects/{test_project.id}/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["progress"]["total_tasks"] == 6
        assert data["progress"]["completed_tasks"] == 0
        assert data["progress"]["percent"] == 0


class TestTaskSubmission:
    def test_submit_task(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        tasks_resp = client.get(f"/api/v1/projects/{test_project.id}/tasks")
        first_task = tasks_resp.json()["tasks"][0]

        response = client.post(
            f"/api/v1/projects/{test_project.id}/tasks/{first_task['id']}/submit",
            json={"content": "提交内容：测试点设计成果"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "任务提交成功"
        assert data["all_submitted"] is False

        progress_resp = client.get(f"/api/v1/projects/{test_project.id}/progress")
        progress = progress_resp.json()["progress"]
        assert progress["completed_tasks"] == 1

    def test_submit_task_reupdate(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        tasks_resp = client.get(f"/api/v1/projects/{test_project.id}/tasks")
        first_task = tasks_resp.json()["tasks"][0]

        client.post(
            f"/api/v1/projects/{test_project.id}/tasks/{first_task['id']}/submit",
            json={"content": "first"},
        )
        response = client.post(
            f"/api/v1/projects/{test_project.id}/tasks/{first_task['id']}/submit",
            json={"content": "updated"},
        )
        assert response.status_code == 200

    def test_submit_all_tasks_completes_path(self, client, test_user, test_path, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        tasks_resp = client.get(f"/api/v1/projects/{test_project.id}/tasks")
        tasks = tasks_resp.json()["tasks"]

        for t in tasks:
            resp = client.post(
                f"/api/v1/projects/{test_project.id}/tasks/{t['id']}/submit",
                json={"content": f"提交内容: {t['title']}"},
            )
            assert resp.status_code == 200

        last_resp = client.post(
            f"/api/v1/projects/{test_project.id}/tasks/{tasks[-1]['id']}/submit",
            json={"content": "final"},
        )
        assert last_resp.json()["all_submitted"] is True

        eval_resp = client.get(f"/api/v1/projects/{test_project.id}/evaluation")
        eval_data = eval_resp.json()
        assert eval_data["evaluation"] is not None
        assert eval_data["evaluation"]["is_passed"] is True


class TestProjectStart:
    def test_start_project(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.post(f"/api/v1/projects/{test_project.id}/start")
        assert response.status_code == 200
        data = response.json()
        assert "项目已开始" in data["message"]


class TestProjectEvaluation:
    def test_evaluation_empty(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.get(f"/api/v1/projects/{test_project.id}/evaluation")
        assert response.status_code == 200
        data = response.json()
        assert data["evaluation"] is None


class TestProjectExam:
    def test_exam_start_no_exam_id(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.post(f"/api/v1/projects/{test_project.id}/exam/start", json={})
        assert response.status_code == 200
        data = response.json()
        assert "请指定 exam_id" in data["message"]

    def test_exam_start_with_id(self, client, test_user, test_project):
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.post(f"/api/v1/projects/{test_project.id}/exam/start", json={"exam_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["exam_id"] == 1


class TestRegression:
    def test_resubmit_does_not_double_score(self, client, test_user, test_project):
        """重复提交不会重复加分"""
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        tasks_resp = client.get(f"/api/v1/projects/{test_project.id}/tasks")
        tasks = tasks_resp.json()["tasks"]

        for t in tasks:
            client.post(
                f"/api/v1/projects/{test_project.id}/tasks/{t['id']}/submit",
                json={"content": f"提交: {t['title']}"},
            )

        eval_resp = client.get(f"/api/v1/projects/{test_project.id}/evaluation")
        first_eval = eval_resp.json()["evaluation"]
        assert first_eval is not None
        assert first_eval["is_passed"] is True
        first_score = first_eval["total_score"]

        client.post(
            f"/api/v1/projects/{test_project.id}/tasks/{tasks[0]['id']}/submit",
            json={"content": "修改后的提交"},
        )

        eval_resp2 = client.get(f"/api/v1/projects/{test_project.id}/evaluation")
        second_eval = eval_resp2.json()["evaluation"]
        assert second_eval["total_score"] == first_score

    def test_last_task_submission_generates_evaluation(self, client, test_user, test_project):
        """提交最后一个任务后立即生成评价"""
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        tasks_resp = client.get(f"/api/v1/projects/{test_project.id}/tasks")
        tasks = tasks_resp.json()["tasks"]

        for t in tasks[:-1]:
            client.post(
                f"/api/v1/projects/{test_project.id}/tasks/{t['id']}/submit",
                json={"content": f"提交: {t['title']}"},
            )

        eval_before = client.get(f"/api/v1/projects/{test_project.id}/evaluation")
        assert eval_before.json()["evaluation"] is None

        last_resp = client.post(
            f"/api/v1/projects/{test_project.id}/tasks/{tasks[-1]['id']}/submit",
            json={"content": "最终提交"},
        )
        assert last_resp.json()["all_submitted"] is True

        eval_after = client.get(f"/api/v1/projects/{test_project.id}/evaluation")
        assert eval_after.json()["evaluation"] is not None
        assert eval_after.json()["evaluation"]["is_passed"] is True

    def test_scenario_ownership_validation_in_autotest_run(self, client, test_user, test_project):
        """非项目场景不能冒充项目执行"""
        from fastapi_backend.deps.auth import get_current_user

        client.app.dependency_overrides[get_current_user] = make_auth_override(test_user)

        response = client.post(
            f"/api/v1/projects/{test_project.id}/autotest/run",
            json={"scenario_id": 99999},
        )
        assert response.status_code == 400
        assert "不存在" in response.json()["detail"]
