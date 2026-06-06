# Phase 1 — Core: schools, profiles, user_roles, parents, parent_students
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str | None] = mapped_column(String)
    board: Mapped[str | None] = mapped_column(String)
    logo_url: Mapped[str | None] = mapped_column(Text)
    theme_palette: Mapped[str] = mapped_column(
        String, default="campos-blue",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    students: Mapped[list["Student"]] = relationship(back_populates="school")
    classes: Mapped[list["Class"]] = relationship(back_populates="school")
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="school")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)  # = auth.uid()
    full_name: Mapped[str | None] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="profile")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    school_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    profile: Mapped["Profile"] = relationship(back_populates="user_roles")
    school: Mapped["School | None"] = relationship(back_populates="user_roles")


class Parent(Base):
    __tablename__ = "parents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    profile_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    parent_students: Mapped[list["ParentStudent"]] = relationship(back_populates="parent")


class ParentStudent(Base):
    __tablename__ = "parent_students"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("parents.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    relation: Mapped[str | None] = mapped_column(String)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    parent: Mapped["Parent"] = relationship(back_populates="parent_students")
