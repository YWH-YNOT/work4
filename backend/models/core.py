"""
扩展后的数据库模型 - 支持完整 LMS 功能
包含: User, Course, TimetableEntry, ChatLog, Resource,
     Assignment, Submission, Quiz, QuizQuestion, QuizAttempt,
     Announcement, Attendance, Grade, Discussion, Comment
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime,
    Text, Float, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")   # student | teacher | admin
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    taught_courses = relationship("Course", back_populates="teacher")
    timetable_entries = relationship("TimetableEntry", back_populates="student")
    chat_logs = relationship("ChatLog", back_populates="user")
    submissions = relationship("Submission", back_populates="student")
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    discussions = relationship("Discussion", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    announcements = relationship("Announcement", back_populates="author")
    uploaded_resources = relationship("Resource", back_populates="uploader")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher = relationship("User", back_populates="taught_courses")
    timetable_entries = relationship("TimetableEntry", back_populates="course")
    chat_logs = relationship("ChatLog", back_populates="course")
    resources = relationship("Resource", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")
    quizzes = relationship("Quiz", back_populates="course")
    announcements = relationship("Announcement", back_populates="course")
    attendances = relationship("Attendance", back_populates="course")
    grades = relationship("Grade", back_populates="course")
    discussions = relationship("Discussion", back_populates="course")


class TimetableEntry(Base):
    __tablename__ = "timetable_entries"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    day_of_week = Column(Integer)       # 1-7
    start_session = Column(Integer)
    end_session = Column(Integer)
    weeks = Column(String)
    location = Column(String)

    student = relationship("User", back_populates="timetable_entries")
    course = relationship("Course", back_populates="timetable_entries")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    role = Column(String)               # user | assistant
    content = Column(Text)
    conversation_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_logs")
    course = relationship("Course", back_populates="chat_logs")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    uploader_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_size = Column(Integer)         # bytes
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="resources")
    uploader = relationship("User", back_populates="uploaded_resources")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, default="homework")   # homework | report
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    title = Column(String, nullable=False)
    time_limit = Column(Integer, nullable=True)     # minutes
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), index=True)
    question = Column(Text, nullable=False)
    options = Column(JSON)              # ["A. ...", "B. ...", ...]
    correct_option = Column(Integer)    # 0-based index

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)
    answers = Column(JSON)              # {question_id: selected_option}
    score = Column(Float, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User", back_populates="quiz_attempts")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    content = Column(Text)
    priority = Column(Integer, default=0)   # 0 normal, 1 important, 2 urgent
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="announcements")
    author = relationship("User", back_populates="announcements")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=True)
    date = Column(String, index=True)   # YYYY-MM-DD
    status = Column(String, default="present")  # present | absent | late

    student = relationship("User", back_populates="attendances")
    course = relationship("Course", back_populates="attendances")


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="课堂签到")
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course")
    teacher = relationship("User")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    score = Column(Float)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="grades")
    course = relationship("Course", back_populates="grades")


class Discussion(Base):
    __tablename__ = "discussions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    content = Column(Text)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="discussions")
    author = relationship("User", back_populates="discussions")
    comments = relationship("Comment", back_populates="discussion")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    discussion_id = Column(Integer, ForeignKey("discussions.id"), index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    discussion = relationship("Discussion", back_populates="comments")
    author = relationship("User", back_populates="comments")
