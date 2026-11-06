from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database import Base
from ..domain.model import DeliveryChannel, EngagementCategory, EngagementDay, NotificationIntent, NotificationPreferences


class EngagementPreferencesRow(Base):
    __tablename__ = "engagement_preferences"
    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    quiet_start_minute: Mapped[int] = mapped_column(Integer, default=1320)
    quiet_end_minute: Mapped[int] = mapped_column(Integer, default=420)
    max_daily_notifications: Mapped[int] = mapped_column(Integer, default=2)
    assessment_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    study_plan_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    flashcards_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    streak_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    content_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_study_minute: Mapped[int] = mapped_column(Integer, default=1140)
    timezone_offset_minutes: Mapped[int] = mapped_column(Integer, default=0)
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, default=30)


class NotificationIntentRow(Base):
    __tablename__ = "engagement_notification_intents"
    __table_args__ = (UniqueConstraint("account_id", "dedupe_key", name="uq_engagement_dedupe"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(180), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    channel: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(240))
    body: Mapped[str] = mapped_column(Text)
    deep_link: Mapped[str] = mapped_column(String(512), default="")
    fire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    priority: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[str] = mapped_column(String(24), default="planned", index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EngagementDayRow(Base):
    __tablename__ = "engagement_days"
    __table_args__ = (UniqueConstraint("account_id", "day_key", name="uq_engagement_day"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    day_key: Mapped[str] = mapped_column(String(10), index=True)
    active_minutes: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    quiz_questions: Mapped[int] = mapped_column(Integer, default=0)
    flashcards_reviewed: Mapped[int] = mapped_column(Integer, default=0)


class PushDeviceRow(Base):
    __tablename__ = "engagement_push_devices"
    __table_args__ = (UniqueConstraint("account_id", "device_id", name="uq_engagement_push_device"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[str] = mapped_column(String(80), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    token: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class SqlAlchemyEngagementRepository:
    def __init__(self, session_factory): self.session_factory = session_factory
    def get_preferences(self, account_id):
        with self.session_factory() as s:
            r=s.get(EngagementPreferencesRow, account_id)
            if r is None: return NotificationPreferences()
            return NotificationPreferences(r.quiet_start_minute,r.quiet_end_minute,r.max_daily_notifications,r.assessment_enabled,r.study_plan_enabled,r.flashcards_enabled,r.streak_enabled,r.content_enabled,r.push_enabled,r.preferred_study_minute,r.timezone_offset_minutes,r.daily_goal_minutes)
    def save_preferences(self, account_id, p):
        with self.session_factory() as s:
            s.merge(EngagementPreferencesRow(account_id=account_id,quiet_start_minute=p.quiet_start_minute,quiet_end_minute=p.quiet_end_minute,max_daily_notifications=p.max_daily_notifications,assessment_enabled=p.assessment_enabled,study_plan_enabled=p.study_plan_enabled,flashcards_enabled=p.flashcards_enabled,streak_enabled=p.streak_enabled,content_enabled=p.content_enabled,push_enabled=p.push_enabled,preferred_study_minute=p.preferred_study_minute,timezone_offset_minutes=p.timezone_offset_minutes,daily_goal_minutes=p.daily_goal_minutes)); s.commit()
    def list_scheduled_for_day(self, account_id, day_key):
        with self.session_factory() as s:
            start=datetime.fromisoformat(day_key).replace(tzinfo=UTC); end=start.replace(hour=23,minute=59,second=59,microsecond=999999)
            rows=s.scalars(select(NotificationIntentRow).where(NotificationIntentRow.account_id==account_id,NotificationIntentRow.status=="planned",NotificationIntentRow.fire_at>=start,NotificationIntentRow.fire_at<=end)).all()
            return tuple(_intent(r) for r in rows)
    def save_intent(self, intent):
        with self.session_factory() as s:
            found=s.scalar(select(NotificationIntentRow.id).where(NotificationIntentRow.account_id==intent.account_id,NotificationIntentRow.dedupe_key==intent.dedupe_key))
            if found: return False
            s.add(NotificationIntentRow(id=intent.id,account_id=intent.account_id,dedupe_key=intent.dedupe_key,category=intent.category.value,channel=intent.channel.value,title=intent.title,body=intent.body,deep_link=intent.deep_link,fire_at=intent.fire_at,expires_at=intent.expires_at,priority=intent.priority,status="planned",delivered_at=None,created_at=intent.created_at)); s.commit(); return True
    def cancel_intent(self, intent_id):
        with self.session_factory() as s:
            row=s.get(NotificationIntentRow,intent_id)
            if row is not None:
                s.delete(row); s.commit()
    def list_due_push(self, now, limit=100):
        with self.session_factory() as s:
            rows=s.scalars(select(NotificationIntentRow).where(NotificationIntentRow.channel==DeliveryChannel.PUSH.value,NotificationIntentRow.status=="planned",NotificationIntentRow.fire_at<=now).order_by(NotificationIntentRow.priority.desc(),NotificationIntentRow.fire_at.asc()).limit(max(1,min(limit,500)))).all()
            return tuple(_intent(r) for r in rows)
    def mark_delivered(self, intent_id, delivered_at):
        with self.session_factory() as s:
            row=s.get(NotificationIntentRow,intent_id)
            if row is not None:
                row.status="delivered"; row.delivered_at=delivered_at; s.commit()
    def upsert_day(self, account_id, day):
        with self.session_factory() as s:
            r=s.scalar(select(EngagementDayRow).where(EngagementDayRow.account_id==account_id,EngagementDayRow.day_key==day.day_key))
            if r is None:
                r=EngagementDayRow(account_id=account_id,day_key=day.day_key,active_minutes=0,completed_tasks=0,quiz_questions=0,flashcards_reviewed=0); s.add(r)
            r.active_minutes=max(r.active_minutes or 0,day.active_minutes); r.completed_tasks=max(r.completed_tasks or 0,day.completed_tasks); r.quiz_questions=max(r.quiz_questions or 0,day.quiz_questions); r.flashcards_reviewed=max(r.flashcards_reviewed or 0,day.flashcards_reviewed); s.commit()
    def recent_days(self, account_id, limit=60):
        with self.session_factory() as s:
            rows=s.scalars(select(EngagementDayRow).where(EngagementDayRow.account_id==account_id).order_by(EngagementDayRow.day_key.desc()).limit(limit)).all()
            return tuple(EngagementDay(r.day_key,r.active_minutes,r.completed_tasks,r.quiz_questions,r.flashcards_reviewed) for r in rows)


class SqlAlchemyPushRegistry:
    def __init__(self, session_factory): self.session_factory=session_factory
    def register(self, account_id, device_id, platform, token):
        with self.session_factory() as s:
            row=s.scalar(select(PushDeviceRow).where(PushDeviceRow.account_id==account_id,PushDeviceRow.device_id==device_id))
            if row is None: row=PushDeviceRow(account_id=account_id,device_id=device_id,platform=platform,token=token,active=True,updated_at=datetime.now(UTC)); s.add(row)
            else: row.platform=platform; row.token=token; row.active=True; row.updated_at=datetime.now(UTC)
            s.commit()
    def revoke(self, account_id, device_id):
        with self.session_factory() as s:
            row=s.scalar(select(PushDeviceRow).where(PushDeviceRow.account_id==account_id,PushDeviceRow.device_id==device_id))
            if row: row.active=False; row.updated_at=datetime.now(UTC); s.commit()
    def active_tokens(self, account_id):
        with self.session_factory() as s:
            return tuple(s.scalars(select(PushDeviceRow.token).where(PushDeviceRow.account_id==account_id,PushDeviceRow.active.is_(True))).all())
    def revoke_token(self, token):
        with self.session_factory() as s:
            rows=s.scalars(select(PushDeviceRow).where(PushDeviceRow.token==token)).all()
            for row in rows: row.active=False; row.updated_at=datetime.now(UTC)
            s.commit()


def _intent(r):
    return NotificationIntent(id=r.id,account_id=r.account_id,dedupe_key=r.dedupe_key,category=EngagementCategory(r.category),channel=DeliveryChannel(r.channel),title=r.title,body=r.body,deep_link=r.deep_link,fire_at=_utc(r.fire_at),expires_at=_utc(r.expires_at),priority=r.priority,created_at=_utc(r.created_at))
