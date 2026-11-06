from datetime import UTC, datetime, timedelta

from app.modules.engagement.domain.model import NotificationPreferences, next_allowed_time, is_quiet
from app.modules.engagement.application.service import EngagementService
from app.modules.engagement.domain.model import EngagementDay, NotificationIntent, EngagementCategory, DeliveryChannel


class Repo:
    def __init__(self): self.prefs={}; self.intents=[]; self.days={}
    def get_preferences(self,a): return self.prefs.get(a,NotificationPreferences())
    def save_preferences(self,a,p): self.prefs[a]=p
    def list_scheduled_for_day(self,a,d): return tuple(x for x in self.intents if x.account_id==a and x.fire_at.date().isoformat()==d)
    def save_intent(self,i):
        if any(x.account_id==i.account_id and x.dedupe_key==i.dedupe_key for x in self.intents): return False
        self.intents.append(i); return True
    def cancel_intent(self,intent_id): self.intents=[x for x in self.intents if x.id!=intent_id]
    def upsert_day(self,a,d): self.days[(a,d.day_key)]=d
    def recent_days(self,a,limit=60): return tuple(d for (acc,_),d in self.days.items() if acc==a)
class Push:
    def register(self,*a): pass
    def revoke(self,*a): pass

def test_quiet_hours_wrap_midnight_and_shift_to_morning():
    p=NotificationPreferences(quiet_start_minute=22*60,quiet_end_minute=7*60)
    assert is_quiet(23*60,p) and is_quiet(6*60,p) and not is_quiet(12*60,p)
    c=datetime(2026,9,21,23,30,tzinfo=UTC)
    assert next_allowed_time(c,p)==datetime(2026,9,22,7,0,tzinfo=UTC)

def test_dedupe_and_daily_cap_protect_against_notification_spam():
    r=Repo(); s=EngagementService(r,Push(),now=lambda:datetime(2026,9,21,8,tzinfo=UTC))
    r.prefs['a']=NotificationPreferences(max_daily_notifications=1,quiet_start_minute=23*60,quiet_end_minute=6*60)
    base=datetime(2026,9,21,12,tzinfo=UTC)
    i=lambda key,prio: NotificationIntent(key,'a',key,EngagementCategory.STUDY_PLAN,DeliveryChannel.LOCAL,'t','b','/revision',base,base+timedelta(hours=1),prio)
    assert s.schedule(i('one',50)) is True
    assert s.schedule(i('one',90)) is False
    assert s.schedule(i('two',40)) is False

def test_assessment_reminders_skip_j3_when_already_well_prepared():
    now=datetime(2026,9,21,8,tzinfo=UTC); s=EngagementService(Repo(),Push(),now=lambda:now)
    starts=now+timedelta(days=5)
    intents=s.assessment_reminders(account_id='a',event_id='e1',course_title='Anatomie',starts_at=starts,readiness=90)
    assert {x.dedupe_key.rsplit(':',1)[-1] for x in intents}=={'j1','h3'}

def test_streak_allows_today_or_yesterday_as_current_anchor():
    now=datetime(2026,9,21,8,tzinfo=UTC); r=Repo(); s=EngagementService(r,Push(),now=lambda:now)
    for d in ('2026-09-18','2026-09-19','2026-09-20'):
        s.record_activity('a',EngagementDay(d,active_minutes=20))
    st=s.streak('a')
    assert st.current_days==3 and st.best_days==3 and st.weekly_minutes>=20


def test_higher_priority_replaces_lower_when_daily_cap_is_full():
    r=Repo(); s=EngagementService(r,Push(),now=lambda:datetime(2026,9,21,8,tzinfo=UTC))
    r.prefs['a']=NotificationPreferences(max_daily_notifications=1,quiet_start_minute=23*60,quiet_end_minute=6*60)
    base=datetime(2026,9,21,12,tzinfo=UTC)
    low=NotificationIntent('low','a','low',EngagementCategory.STUDY_PLAN,DeliveryChannel.LOCAL,'t','b','/',base,base+timedelta(hours=1),30)
    high=NotificationIntent('high','a','high',EngagementCategory.ASSESSMENT,DeliveryChannel.LOCAL,'t','b','/',base+timedelta(minutes=1),base+timedelta(hours=2),90)
    assert s.schedule(low)
    assert s.schedule(high)
    assert [x.id for x in r.intents]==['high']

def test_quiet_hours_apply_in_user_timezone_not_utc():
    r=Repo(); s=EngagementService(r,Push(),now=lambda:datetime(2026,9,21,8,tzinfo=UTC))
    r.prefs['a']=NotificationPreferences(quiet_start_minute=22*60,quiet_end_minute=7*60,timezone_offset_minutes=120)
    # 21:30 UTC = 23:30 local, therefore shifted to 07:00 local = 05:00 UTC next day.
    fire=datetime(2026,9,21,21,30,tzinfo=UTC)
    i=NotificationIntent('tz','a','tz',EngagementCategory.STUDY_PLAN,DeliveryChannel.LOCAL,'t','b','/',fire,fire+timedelta(hours=12),50)
    assert s.schedule(i)
    assert r.intents[0].fire_at==datetime(2026,9,22,5,0,tzinfo=UTC)

class FakePushSender:
    def __init__(self, invalid=()): self.calls=[]; self.invalid=tuple(invalid)
    def send(self, **kwargs): self.calls.append(kwargs); return self.invalid

class PushWithTokens(Push):
    def __init__(self): self.tokens=('token-1234567890123456',); self.revoked=[]
    def active_tokens(self,account_id): return self.tokens
    def revoke_token(self,token): self.revoked.append(token)


def test_push_dispatch_is_disabled_without_sender_and_does_not_consume_intents():
    r=Repo(); p=PushWithTokens(); s=EngagementService(r,p,now=lambda:datetime(2026,9,21,12,tzinfo=UTC),push_sender=None)
    result=s.dispatch_due_push()
    assert result=={'sent':0,'invalid_tokens':0,'skipped':0}


def test_push_dispatch_revokes_invalid_token_and_marks_delivery():
    class PushRepo(Repo):
        def __init__(self): super().__init__(); self.delivered=[]
        def list_due_push(self,now,limit=100): return tuple(x for x in self.intents if x.channel==DeliveryChannel.PUSH and x.fire_at<=now)
        def mark_delivered(self,intent_id,delivered_at): self.delivered.append(intent_id)
    r=PushRepo(); p=PushWithTokens(); sender=FakePushSender(invalid=p.tokens)
    now=datetime(2026,9,21,12,tzinfo=UTC)
    s=EngagementService(r,p,now=lambda:now,push_sender=sender)
    r.intents.append(NotificationIntent('push1','a','p1',EngagementCategory.CONTENT,DeliveryChannel.PUSH,'Nouveau cours','Disponible','/courses',now-timedelta(minutes=1),now+timedelta(hours=1),70))
    out=s.dispatch_due_push()
    assert out['sent']==1 and out['invalid_tokens']==1
    assert p.revoked==list(p.tokens) and r.delivered==['push1']


def test_zero_daily_cap_disables_all_scheduled_notifications():
    r=Repo(); s=EngagementService(r,Push(),now=lambda:datetime(2026,9,21,8,tzinfo=UTC))
    r.prefs['a']=NotificationPreferences(max_daily_notifications=0)
    base=datetime(2026,9,21,12,tzinfo=UTC)
    i=NotificationIntent('off','a','off',EngagementCategory.STUDY_PLAN,DeliveryChannel.LOCAL,'t','b','/',base,base+timedelta(hours=1),90)
    assert s.schedule(i) is False and r.intents==[]


def test_expired_push_is_skipped_without_sending():
    class PushRepo(Repo):
        def __init__(self): super().__init__(); self.delivered=[]
        def list_due_push(self,now,limit=100): return tuple(self.intents)
        def mark_delivered(self,intent_id,delivered_at): self.delivered.append(intent_id)
    r=PushRepo(); p=PushWithTokens(); sender=FakePushSender(); now=datetime(2026,9,21,12,tzinfo=UTC)
    r.intents.append(NotificationIntent('expired','a','expired',EngagementCategory.CONTENT,DeliveryChannel.PUSH,'t','b','/',now-timedelta(hours=2),now-timedelta(hours=1),70))
    s=EngagementService(r,p,now=lambda:now,push_sender=sender)
    out=s.dispatch_due_push()
    assert out['sent']==0 and out['skipped']==1 and sender.calls==[] and r.delivered==['expired']
