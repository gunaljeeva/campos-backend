# Phase 7b — Meetings & Teacher Attendance
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Date, Time, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date, time
from uuid import uuid4
from app.database import Base


class TeacherAttendance(Base):
    __tablename__ = "teacher_attendance"
    __table_args__ = (
        CheckConstraint(
            "status IN ('present','absent','late','half_day','on_leave')",
            name="teacher_att_status_check",
        ),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    marked_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    teacher: Mapped["Teacher"] = relationship(back_populates="teacher_attendance")


class ParentMeeting(Base):
    __tablename__ = "parent_meetings"
    __table_args__ = (
        CheckConstraint("status IN ('scheduled','completed','cancelled')", name="pm_status_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    agenda: Mapped[str | None] = mapped_column(Text)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_time: Mapped[time] = mapped_column(Time, nullable=False)
    venue: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    responses: Mapped[list["ParentMeetingResponse"]] = relationship(back_populates="meeting")


class ParentMeetingResponse(Base):
    __tablename__ = "parent_meeting_responses"
    __table_args__ = (
        CheckConstraint("response IN ('accepted','rejected')", name="pmr_response_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    meeting_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("parent_meetings.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    parent_profile_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    response: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    meeting: Mapped["ParentMeeting"] = relationship(back_populates="responses")
