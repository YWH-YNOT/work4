"""
用于初始化各模块的测试数据 (Seed Data)，
测试数据应该在数据库建表完成后执行，仅执行一次。
"""
import sys
import os
import shutil
from datetime import datetime, timedelta

sys.path.append(os.path.abspath('.'))

from core.database import SessionLocal
from models import core as models
from core.auth import hash_password

def seed_demo_data():
    db = SessionLocal()
    try:
        # 获取基础用户
        teacher = db.query(models.User).filter(models.User.username == "teacher").first()
        student = db.query(models.User).filter(models.User.username == "student").first()

        if not teacher or not student:
            print("❌ 未找到 teacher 或 student 账号，请先完成基础用户创建。")
            return

        # -----------------------------
        # 1. 创建一门核心测试课程
        # -----------------------------
        course = db.query(models.Course).filter(models.Course.name == "Python 智能开发基础").first()
        if not course:
            course = models.Course(
                name="Python 智能开发基础",
                course_code="CS-PY-101",
                description="这门课程你将学习如何通过 Python 结合大模型构建 AI 应用。",
                teacher_id=teacher.id
            )
            db.add(course)
            db.commit()
            db.refresh(course)
            print(f"✅ 课程 '{course.name}' 创建成功")
        else:
            print(f"ℹ️ 课程 '{course.name}' 已存在")

        # -----------------------------
        # 2. 为 student 将这门课加入课表 (自动实现选课关系)
        # -----------------------------
        entry = db.query(models.TimetableEntry).filter(
            models.TimetableEntry.student_id == student.id,
            models.TimetableEntry.course_id == course.id
        ).first()

        if not entry:
            entry = models.TimetableEntry(
                student_id=student.id,
                course_id=course.id,
                day_of_week=1,          # 周一
                start_session=1,        # 1-2 节
                end_session=2,
                weeks="1-16",
                location="启真楼 A301"
            )
            db.add(entry)
            db.commit()
            print("✅ 课表排课记录创建成功")

        # -----------------------------
        # 3. 创建作业及提交记录
        # -----------------------------
        assignment1 = db.query(models.Assignment).filter(models.Assignment.title == "Week 1: 开发环境配置").first()
        if not assignment1:
            assignment1 = models.Assignment(
                course_id=course.id,
                title="Week 1: 开发环境配置",
                description="请完成 Python 和 FastAPI 环境的安装配置，并提交你的 'Hello World' 截图。",
                type="homework",
                due_date=datetime.utcnow() + timedelta(days=7)
            )
            db.add(assignment1)
            db.commit()

            # 模拟学生提交
            sub = models.Submission(
                assignment_id=assignment1.id,
                student_id=student.id,
                content="老师好，我已经完成了 FastAPI 的 Hello World 搭建，接口返回正常。"
            )
            db.add(sub)
            db.commit()
            print("✅ 作业与提交记录创建成功")

        assignment2 = db.query(models.Assignment).filter(models.Assignment.title == "Week 2: 简易路由实现").first()
        if not assignment2:
            assignment2 = models.Assignment(
                course_id=course.id,
                title="Week 2: 简易路由实现",
                description="请手写一个基础的 FastAPI 用户登录验证路由，必须包含用户名存在检查。",
                type="homework",
                due_date=datetime.utcnow() + timedelta(days=14)
            )
            db.add(assignment2)
            db.commit()
            print("✅ 未提交的待办作业记录创建成功")

        # -----------------------------
        # 4. 创建模拟资源文件
        # -----------------------------
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        test_file_path = os.path.join(upload_dir, f"{teacher.id}_Python_CheatSheet.pdf")
        if not os.path.exists(test_file_path):
            with open(test_file_path, "wb") as f:
                f.write(b"%PDF-1.4 Fake PDF Content used for testing LMS resource download functionality.")

        resource = db.query(models.Resource).filter(models.Resource.filename == "Python_CheatSheet.pdf").first()
        if not resource:
            resource = models.Resource(
                course_id=course.id,
                uploader_id=teacher.id,
                filename="Python_CheatSheet.pdf",
                filepath=test_file_path,
                file_size=88    # bytes
            )
            db.add(resource)
            db.commit()
            print("✅ 课件资源记录创建成功")

        # -----------------------------
        # 5. 创建课后讨论帖及回复
        # -----------------------------
        discussion = db.query(models.Discussion).filter(models.Discussion.title == "关于 async/await 的理解求助").first()
        if not discussion:
            discussion = models.Discussion(
                course_id=course.id,
                author_id=student.id,
                title="关于 async/await 的理解求助",
                content="请问在 FastAPI 里，如果我的数据库查询不支持异步（如使用标准 SQLAlchemy 时），路由函数前还要加 async 吗？"
            )
            db.add(discussion)
            db.commit()
            db.refresh(discussion)

            comment = models.Comment(
                discussion_id=discussion.id,
                author_id=teacher.id,
                content="好问题。如果你的内部 I/O 处理（如数据库、文件读取）完全是同步且阻塞的，直接定义为普通 `def` 更好，FastAPI 会把它们丢在线程池里执行，避免阻塞主事件循环。"
            )
            db.add(comment)
            db.commit()
            print("✅ 讨论区主题及回复创建成功")

        # -----------------------------
        # 6. 创建一条正在进行中的签到任务
        # -----------------------------
        attendance = db.query(models.AttendanceSession).filter(models.AttendanceSession.course_id == course.id).first()
        if not attendance:
            # 一个还有 15 分钟才过期的签到任务
            attendance = models.AttendanceSession(
                course_id=course.id,
                teacher_id=teacher.id,
                title="第1周第1节课堂签到",
                deadline=datetime.utcnow() + timedelta(minutes=15)
            )
            db.add(attendance)
            db.commit()
            print("✅ 活跃签到任务创建成功")

        print("🎉 测试数据全部种子化成功！请登录应用进行体验。")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
