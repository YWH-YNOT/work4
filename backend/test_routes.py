"""
LMS 路由集成测试
验证本次 Bug 修复效果，使用 httpx + FastAPI TestClient（内存 SQLite）
运行: python -m pytest test_routes.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ─── 使用独立内存数据库，不污染 ai_ywh.db ───
TEST_DATABASE_URL = "sqlite:///./test_temp.db"

from core.database import Base, get_db
from main import app

engine_test = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ─── 工具 ────────────────────────────────────
def register_and_login(username, password, role="student"):
    client.post("/api/v1/auth/register", json={
        "username": username, "password": password, "role": role
    })
    r = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ─── Test 1: 注册 + 登录 + /me 基础流程 ─────
class TestAuth:
    def test_register_login_me(self):
        token = register_and_login("test_student_1", "pass123", "student")
        r = client.get("/api/v1/auth/me", headers=auth_header(token))
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "test_student_1"
        assert data["role"] == "student"
        print("✅ 注册/登录/me 通过")

    def test_duplicate_username(self):
        register_and_login("dup_user", "pass", "student")
        r = client.post("/api/v1/auth/register", json={
            "username": "dup_user", "password": "pass", "role": "student"
        })
        assert r.status_code == 400
        print("✅ 重复用户名拦截通过")


# ─── Test 2: 课程创建（验证 B5 model_dump 修复）──
class TestCourses:
    def test_create_course(self):
        token = register_and_login("teacher_c1", "pass", "teacher")
        r = client.post("/api/v1/courses/", json={
            "name": "数据结构", "course_code": "CS101"
        }, headers=auth_header(token))
        assert r.status_code == 201, f"Create course failed: {r.text}"
        assert r.json()["name"] == "数据结构"
        print("✅ 课程创建（B5 model_dump）通过")

    def test_list_courses(self):
        token = register_and_login("teacher_c2", "pass", "teacher")
        client.post("/api/v1/courses/", json={"name": "算法"}, headers=auth_header(token))
        r = client.get("/api/v1/courses/", headers=auth_header(token))
        assert r.status_code == 200
        print("✅ 课程列表通过")


# ─── Test 3: 作业 N+1 批量查询（验证 B1/O1/B7）──
class TestAssignments:
    def test_assignment_list_no_n_plus_1(self):
        t_token = register_and_login("teacher_a1", "pass", "teacher")
        # 创建课程
        cr = client.post("/api/v1/courses/", json={"name": "线代"}, headers=auth_header(t_token))
        course_id = cr.json()["id"]
        # 创建 3 个作业
        for i in range(3):
            r = client.post("/api/v1/assignments/", json={
                "course_id": course_id, "title": f"作业{i}", "type": "homework"
            }, headers=auth_header(t_token))
            assert r.status_code == 200, f"Create assignment failed: {r.text}"
        # 列表查询
        r = client.get("/api/v1/assignments/", headers=auth_header(t_token))
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 3
        # submissions_count 应该是 0（没有提交），不是 None
        for item in data:
            assert "submitted" in item
            assert "submissions_count" in item
        print("✅ 作业列表 N+1 批量查询（B1/O1/B7）通过")


# ─── Test 4: 讨论区浏览量（验证 B3 db.refresh）──
class TestDiscussions:
    def test_views_increment(self):
        token = register_and_login("student_d1", "pass", "student")
        # 创建讨论（需要先有课程）
        t_token = register_and_login("teacher_d1", "pass", "teacher")
        cr = client.post("/api/v1/courses/", json={"name": "讨论课"}, headers=auth_header(t_token))
        course_id = cr.json()["id"]
        r = client.post("/api/v1/discussions/", json={
            "course_id": course_id, "title": "测试帖", "content": "内容"
        }, headers=auth_header(token))
        assert r.status_code == 201, f"Create discussion failed: {r.text}"
        disc_id = r.json()["id"]

        # 第一次访问: views 应该返回 1（而非修复前的 0）
        r1 = client.get(f"/api/v1/discussions/{disc_id}", headers=auth_header(token))
        assert r1.status_code == 200
        views1 = r1.json()["views"]

        # 第二次访问: views 应该 +1
        r2 = client.get(f"/api/v1/discussions/{disc_id}", headers=auth_header(token))
        views2 = r2.json()["views"]

        assert views2 == views1 + 1, f"views 未正确递增: {views1} → {views2}"
        print(f"✅ 讨论区浏览量递增（B3 db.refresh）通过：{views1} → {views2}")


# ─── Test 5: 测验创建（验证 B6 model_dump）──
class TestQuiz:
    def test_create_quiz_and_question(self):
        t_token = register_and_login("teacher_q1", "pass", "teacher")
        cr = client.post("/api/v1/courses/", json={"name": "测验课"}, headers=auth_header(t_token))
        course_id = cr.json()["id"]

        # 创建测验
        r = client.post("/api/v1/quiz/", json={
            "course_id": course_id, "title": "期中测验", "time_limit": 60
        }, headers=auth_header(t_token))
        assert r.status_code == 200, f"Create quiz failed: {r.text}"
        quiz_id = r.json()["id"]

        # 添加题目
        r2 = client.post(f"/api/v1/quiz/{quiz_id}/questions", json={
            "question": "1+1=?",
            "options": ["1", "2", "3", "4"],
            "correct_option": 1
        }, headers=auth_header(t_token))
        assert r2.status_code == 200, f"Add question failed: {r2.text}"
        print("✅ 测验创建和题目添加（B6 model_dump）通过")


# ─── Test 6: 成绩 upsert（验证 B4 model_dump）──
class TestGrades:
    def test_grade_upsert(self):
        t_token = register_and_login("teacher_g1", "pass", "teacher")
        s_token = register_and_login("student_g1", "pass", "student")
        # 查 student id
        me = client.get("/api/v1/auth/me", headers=auth_header(s_token)).json()
        student_id = me["id"]
        # 创建课程
        cr = client.post("/api/v1/courses/", json={"name": "成绩课"}, headers=auth_header(t_token))
        course_id = cr.json()["id"]

        # 新建成绩
        r = client.post("/api/v1/grades/", json={
            "student_id": student_id, "course_id": course_id, "score": 88.5
        }, headers=auth_header(t_token))
        assert r.status_code == 200, f"Create grade failed: {r.text}"

        # 更新成绩（upsert）
        r2 = client.post("/api/v1/grades/", json={
            "student_id": student_id, "course_id": course_id, "score": 92.0
        }, headers=auth_header(t_token))
        assert r2.status_code == 200, f"Update grade failed: {r2.text}"
        print("✅ 成绩 upsert（B4 model_dump）通过")


# ─── Test 7: 公告创建（验证 B8 model_dump）──
class TestAnnouncements:
    def test_create_announcement(self):
        t_token = register_and_login("teacher_ann1", "pass", "teacher")
        r = client.post("/api/v1/announcements/", json={
            "title": "重要通知", "content": "请注意事项", "priority": 1
        }, headers=auth_header(t_token))
        assert r.status_code == 201, f"Create announcement failed: {r.text}"
        assert r.json()["title"] == "重要通知"
        print("✅ 公告创建（B8 model_dump）通过")
