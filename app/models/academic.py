# Phase 2 — Academic: students, classes, teachers, homework, homework_submissions
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from uuid import uuid4
from app.database import Base


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    grade: Mapped[str] = mapped_column(String, nullable=False)
    section: Mapped[str] = mapped_column(String, nullable=False)
    homeroom_teacher_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("teachers.id", ondelete="SET NULL"))
    room_number: Mapped[str | None] = mapped_column(String)
    capacity: Mapped[int | None] = mapped_column(Integer)
    academic_year: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    school: Mapped["School"] = relationship(back_populates="classes")
    students: Mapped[list["Student"]] = relationship(back_populates="class_")
    homeroom_teacher: Mapped["Teacher | None"] = relationship(foreign_keys=[homeroom_teacher_id])


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("classes.id", ondelete="SET NULL"))
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    admission_no: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String)
    blood_group: Mapped[str | None] = mapped_column(String)
    photo_url: Mapped[str | None] = mapped_column(Text)
    home_lat: Mapped[float | None] = mapped_column()
    home_lng: Mapped[float | None] = mapped_column()
    home_address: Mapped[str | None] = mapped_column(Text)
    aadhaar_no: Mapped[str | None] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String)
    emergency_contact: Mapped[str | None] = mapped_column(String)
    allergy_notes: Mapped[str | None] = mapped_column(Text)
    room_no: Mapped[str | None] = mapped_column(String)
    hostel_name: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    school: Mapped["School"] = relationship(back_populates="students")
    class_: Mapped["Class | None"] = relationship(back_populates="students")
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="student")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="SET NULL"))
    employee_code: Mapped[str | None] = mapped_column(String)
    department: Mapped[str | None] = mapped_column(String)
    qualification: Mapped[str | None] = mapped_column(String)
    blood_group: Mapped[str | None] = mapped_column(String)
    dob: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(Text)
    joining_date: Mapped[date | None] = mapped_column(Date)
    emergency_contact: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    profile: Mapped["Profile | None"] = relationship()
    teacher_attendance: Mapped[list["TeacherAttendance"]] = relationship(back_populates="teacher")


class Homework(Base):
    __tablename__ = "homework"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    homework_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("homework.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    file_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
