from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Root(Base):
    __tablename__ = "roots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    path: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    instances: Mapped[list["Instance"]] = relationship(back_populates="root")

class Instance(Base):
    __tablename__ = "instances"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    root_id: Mapped[int] = mapped_column(ForeignKey("roots.id"), index=True)
    rel_path: Mapped[str] = mapped_column(String(2048))

    name: Mapped[str] = mapped_column(String(512), index=True)
    ext: Mapped[str] = mapped_column(String(32), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, index=True)
    mtime_utc: Mapped[datetime] = mapped_column(DateTime, index=True)

    kind: Mapped[str] = mapped_column(String(32), index=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    skip_processing: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # UI-editable metadata (v1)
    display_title: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    first_seen_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    root: Mapped["Root"] = relationship(back_populates="instances")
    people_links: Mapped[list["InstancePerson"]] = relationship(back_populates="instance", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("root_id", "rel_path", name="uq_instance_root_relpath"),
        Index("ix_instances_name_ext", "name", "ext"),
    )

class Person(Base):
    __tablename__ = "people"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)

    instance_links: Mapped[list["InstancePerson"]] = relationship(back_populates="person", cascade="all, delete-orphan")

class InstancePerson(Base):
    __tablename__ = "instance_people"
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id"), primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), primary_key=True)

    source: Mapped[str] = mapped_column(String(32), default="manual")  # manual|llm|path|ocr|transcript
    created_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    instance: Mapped["Instance"] = relationship(back_populates="people_links")
    person: Mapped["Person"] = relationship(back_populates="instance_links")
