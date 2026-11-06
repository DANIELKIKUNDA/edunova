from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.runtime import runtime
from app.modules.identity.application.service import RegisterInput

client = TestClient(app)


def _account(prefix: str = "sync"):
    email = f"{prefix}-{uuid4().hex[:10]}@example.test"
    account, tokens = runtime.identity.register(RegisterInput(display_name="Sync User", password="strong-pass-123", email=email, phone_number=None, device_name="pytest"))
    return account.id, {"Authorization": f"Bearer {tokens.access_token}"}


def _device(headers, device_id=None):
    device_id = device_id or f"dev-{uuid4().hex}"
    r = client.post("/v1/sync/devices", headers=headers, json={"device_id":device_id,"name":"Pixel test","platform":"android","app_version":"0.8.0"})
    assert r.status_code == 201, r.text
    return device_id


def _mutation(entity_type, entity_id, *, base_version=None, payload=None, mutation_id=None):
    return {
        "mutation_id": mutation_id or f"mut-{uuid4().hex}",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "operation": "upsert",
        "payload": payload or {},
        "base_version": base_version,
        "client_modified_at": datetime.now(UTC).isoformat(),
    }



def _profile_payload(level="BAC1"):
    return {"faculty":"Médecine","program":"Médecine humaine","level":level,"semester":"S1","institution":None}

def _event_payload(title="Chimie", start="2026-10-01T08:00:00+00:00"):
    return {"title":title,"kind":"interrogation","startsAt":start,"endsAt":None,"courseId":None,"notes":None}

def _prefs(daily=30):
    return {
        "dailyBudgetMinutes":daily,"maxNotificationsPerDay":2,"quietStartMinute":1320,"quietEndMinute":420,
        "maxContinuousMinutes":50,"breakMinutes":10,"maxCoursesPerDay":4,"maxCourseSwitches":5,
        "targetReadiness":80,"planningHorizonDays":14,
    }

def test_sync_requires_registered_device_and_rejects_local_only():
    _, headers = _account("sync-boundary")
    m = _mutation("academic_profile", "profile", payload=_profile_payload())
    r = client.post("/v1/sync/push", headers=headers, json={"device_id":"dev-not-registered","mutations":[m]})
    assert r.status_code == 422
    device = _device(headers)
    local = _mutation("personal_document", "doc-1", payload={"title":"secret.pdf"})
    r = client.post("/v1/sync/push", headers=headers, json={"device_id":device,"mutations":[local]})
    assert r.status_code == 403
    assert r.json()["detail"] == "local_only_entity_cannot_sync"


def test_sync_idempotent_replay_and_pull_cursor():
    _, headers = _account("sync-replay")
    device = _device(headers)
    mid = f"mut-{uuid4().hex}"
    m = _mutation("calendar_event", "evt-1", payload=_event_payload(), mutation_id=mid)
    first = client.post("/v1/sync/push", headers=headers, json={"device_id":device,"mutations":[m]})
    assert first.status_code == 200, first.text
    assert first.json()["outcomes"][0]["disposition"] == "applied"
    replay = client.post("/v1/sync/push", headers=headers, json={"device_id":device,"mutations":[m]})
    assert replay.status_code == 200
    assert replay.json()["outcomes"][0]["disposition"] == "duplicate"

    pulled = client.get(f"/v1/sync/pull?device_id={device}&cursor=0", headers=headers)
    assert pulled.status_code == 200
    data = pulled.json()
    assert len(data["changes"]) == 1
    cursor = data["next_cursor"]
    assert cursor > 0
    empty = client.get(f"/v1/sync/pull?device_id={device}&cursor={cursor}", headers=headers)
    assert empty.json()["changes"] == []


def test_sync_optimistic_conflict_never_silently_overwrites():
    _, headers = _account("sync-conflict")
    a = _device(headers, f"dev-a-{uuid4().hex}")
    b = _device(headers, f"dev-b-{uuid4().hex}")
    first = client.post("/v1/sync/push", headers=headers, json={"device_id":a,"mutations":[_mutation("planning_preferences","default",payload=_prefs(30))]})
    assert first.status_code == 200
    version = first.json()["outcomes"][0]["record"]["version"]
    assert version == 1

    update_a = _mutation("planning_preferences","default",base_version=1,payload=_prefs(45))
    assert client.post("/v1/sync/push", headers=headers, json={"device_id":a,"mutations":[update_a]}).json()["outcomes"][0]["disposition"] == "applied"

    stale = _mutation("planning_preferences","default",base_version=1,payload=_prefs(60))
    result = client.post("/v1/sync/push", headers=headers, json={"device_id":b,"mutations":[stale]}).json()["outcomes"][0]
    assert result["disposition"] == "conflict"
    assert result["canonical"]["payload"]["dailyBudgetMinutes"] == 45
    assert result["canonical"]["version"] == 2


def test_reading_progress_merges_monotonically_across_devices():
    _, headers = _account("sync-progress")
    a = _device(headers, f"dev-a-{uuid4().hex}")
    b = _device(headers, f"dev-b-{uuid4().hex}")
    first = _mutation("reading_progress","course-1",payload={"page":80,"progress":0.50})
    r = client.post("/v1/sync/push", headers=headers, json={"device_id":a,"mutations":[first]})
    assert r.status_code == 200
    second = _mutation("reading_progress","course-1",payload={"page":40,"progress":0.30})
    r = client.post("/v1/sync/push", headers=headers, json={"device_id":b,"mutations":[second]})
    rec = r.json()["outcomes"][0]["record"]
    assert rec["payload"]["page"] == 80
    assert rec["payload"]["progress"] == 0.5


def test_append_only_events_are_immutable_but_same_payload_is_idempotent():
    _, headers = _account("sync-append")
    d = _device(headers)
    q = _mutation("quiz_attempt","attempt-1",payload={"score":70,"course_id":"c1"})
    first = client.post("/v1/sync/push", headers=headers, json={"device_id":d,"mutations":[q]}).json()["outcomes"][0]
    assert first["disposition"] == "applied"
    same = _mutation("quiz_attempt","attempt-1",payload={"score":70,"course_id":"c1"})
    assert client.post("/v1/sync/push", headers=headers, json={"device_id":d,"mutations":[same]}).json()["outcomes"][0]["disposition"] == "duplicate"
    changed = _mutation("quiz_attempt","attempt-1",payload={"score":100,"course_id":"c1"})
    conflict = client.post("/v1/sync/push", headers=headers, json={"device_id":d,"mutations":[changed]}).json()["outcomes"][0]
    assert conflict["disposition"] == "conflict"
    assert conflict["reason"] == "append_only_entity_is_immutable"


def test_sync_is_isolated_by_account():
    _, h1 = _account("sync-owner1")
    _, h2 = _account("sync-owner2")
    d1 = _device(h1)
    d2 = _device(h2)
    m = _mutation("calendar_event","evt-private",payload=_event_payload("Only account 1"))
    assert client.post("/v1/sync/push", headers=h1, json={"device_id":d1,"mutations":[m]}).status_code == 200
    r2 = client.get(f"/v1/sync/pull?device_id={d2}&cursor=0", headers=h2)
    assert r2.status_code == 200
    assert r2.json()["changes"] == []

def test_conflict_replay_preserves_canonical_result():
    _, headers = _account("sync-replay-conflict")
    a = _device(headers, f"dev-a-{uuid4().hex}")
    b = _device(headers, f"dev-b-{uuid4().hex}")
    first = client.post("/v1/sync/push", headers=headers, json={"device_id":a,"mutations":[_mutation("planning_preferences","default",payload=_prefs(30))]})
    assert first.status_code == 200
    client.post("/v1/sync/push", headers=headers, json={"device_id":a,"mutations":[_mutation("planning_preferences","default",base_version=1,payload=_prefs(45))]})
    mid=f"mut-{uuid4().hex}"
    stale=_mutation("planning_preferences","default",base_version=1,payload=_prefs(60),mutation_id=mid)
    conflict=client.post("/v1/sync/push",headers=headers,json={"device_id":b,"mutations":[stale]}).json()["outcomes"][0]
    replay=client.post("/v1/sync/push",headers=headers,json={"device_id":b,"mutations":[stale]}).json()["outcomes"][0]
    assert conflict["disposition"] == "conflict"
    assert replay["disposition"] == "conflict"
    assert replay["canonical"]["version"] == 2
    assert replay["canonical"]["payload"]["dailyBudgetMinutes"] == 45


def test_append_only_delete_and_impossible_base_version_are_rejected():
    _, headers = _account("sync-reject")
    d=_device(headers)
    delete=_mutation("quiz_attempt","a1",payload={})
    delete["operation"]="delete"
    result=client.post("/v1/sync/push",headers=headers,json={"device_id":d,"mutations":[delete]}).json()["outcomes"][0]
    assert result["disposition"] == "rejected"
    assert result["reason"] == "append_only_entity_cannot_delete"
    impossible=_mutation("calendar_event","new-event",base_version=9,payload=_event_payload("x"))
    result=client.post("/v1/sync/push",headers=headers,json={"device_id":d,"mutations":[impossible]}).json()["outcomes"][0]
    assert result["disposition"] == "rejected"
    assert result["reason"] == "base_version_on_missing_entity"

def test_bootstrap_returns_current_snapshot_not_full_history():
    _, headers = _account("sync-bootstrap")
    d=_device(headers)
    first=_mutation("calendar_event","evt-boot",payload=_event_payload("v1"))
    r=client.post("/v1/sync/push",headers=headers,json={"device_id":d,"mutations":[first]}).json()["outcomes"][0]
    v=r["record"]["version"]
    second=_mutation("calendar_event","evt-boot",base_version=v,payload=_event_payload("v2"))
    client.post("/v1/sync/push",headers=headers,json={"device_id":d,"mutations":[second]})
    snap=client.get(f"/v1/sync/bootstrap?device_id={d}",headers=headers)
    assert snap.status_code==200
    changes=[x for x in snap.json()["changes"] if x["entity_id"]=="evt-boot"]
    assert len(changes)==1
    assert changes[0]["payload"]["title"]=="v2"
    assert changes[0]["version"]==2
    assert snap.json()["next_cursor"]>=2


def test_sync_payload_schema_and_private_path_are_rejected():
    _, headers = _account("sync-schema")
    d = _device(headers)
    incomplete = _mutation("academic_profile", "profile", payload={"level":"BAC1"})
    r = client.post("/v1/sync/push", headers=headers, json={"device_id":d,"mutations":[incomplete]})
    assert r.status_code == 422
    assert "sync_payload_missing" in r.json()["detail"]

    leaking = _mutation("academic_profile", "profile", payload={**_profile_payload(), "localUri":"/private/secret.pdf"})
    r = client.post("/v1/sync/push", headers=headers, json={"device_id":d,"mutations":[leaking]})
    assert r.status_code == 422
    assert r.json()["detail"] == "private_local_field_cannot_sync"


def test_device_ack_listing_and_revocation_are_enforced():
    _, headers = _account("sync-device-life")
    d = _device(headers)
    m = _mutation("calendar_event", "evt-ack", payload=_event_payload("ACK"))
    pushed = client.post("/v1/sync/push", headers=headers, json={"device_id":d,"mutations":[m]}).json()["outcomes"][0]
    seq = pushed["record"]["server_seq"]
    ack = client.post("/v1/sync/ack", headers=headers, json={"device_id":d,"cursor":seq})
    assert ack.status_code == 200
    assert ack.json()["acked_cursor"] == seq
    rows = client.get("/v1/sync/devices", headers=headers).json()["devices"]
    row = next(x for x in rows if x["device_id"] == d)
    assert row["acked_cursor"] == seq and row["active"] is True

    revoked = client.delete(f"/v1/sync/devices/{d}", headers=headers)
    assert revoked.status_code == 200
    pull = client.get(f"/v1/sync/pull?device_id={d}&cursor={seq}", headers=headers)
    assert pull.status_code == 422
    assert pull.json()["detail"] == "sync_device_revoked"
    again = client.post("/v1/sync/devices", headers=headers, json={"device_id":d,"name":"same","platform":"android","app_version":"0.8.1"})
    assert again.status_code == 422
    assert again.json()["detail"] == "sync_device_revoked"


def test_ack_cannot_move_beyond_server_cursor():
    _, headers = _account("sync-ack-ahead")
    d = _device(headers)
    r = client.post("/v1/sync/ack", headers=headers, json={"device_id":d,"cursor":999999})
    assert r.status_code == 422
    assert r.json()["detail"] == "sync_ack_cursor_ahead"


def test_compaction_requires_stale_client_to_bootstrap_again():
    _, headers = _account("sync-compaction")
    d = _device(headers)
    base = None
    latest = 0
    # 65 sequential changes create enough safe history to compact with the default 50-event cushion.
    for i in range(65):
        payload = _prefs(30 + (i % 30))
        m = _mutation("planning_preferences", "default", base_version=base, payload=payload)
        out = client.post("/v1/sync/push", headers=headers, json={"device_id":d,"mutations":[m]}).json()["outcomes"][0]
        assert out["disposition"] == "applied"
        base = out["record"]["version"]
        latest = out["record"]["server_seq"]
    assert client.post("/v1/sync/ack", headers=headers, json={"device_id":d,"cursor":latest}).status_code == 200
    compact = client.post("/v1/sync/maintenance/compact", headers=headers)
    assert compact.status_code == 200
    floor = compact.json()["retained_floor"]
    assert floor > 0
    stale = client.get(f"/v1/sync/pull?device_id={d}&cursor=0", headers=headers)
    assert stale.status_code == 200
    assert stale.json()["reset_required"] is True
    assert stale.json()["retained_floor"] == floor
    snap = client.get(f"/v1/sync/bootstrap?device_id={d}", headers=headers)
    assert snap.status_code == 200
    assert snap.json()["reset_required"] is False
    assert any(x["entity_type"] == "planning_preferences" for x in snap.json()["changes"])


def test_compaction_waits_for_all_active_devices_before_advancing_floor():
    _, headers = _account("sync-compaction-two-devices")
    a = _device(headers, f"dev-a-{uuid4().hex}")
    b = _device(headers, f"dev-b-{uuid4().hex}")
    base = None
    latest = 0
    for i in range(65):
        out = client.post(
            "/v1/sync/push",
            headers=headers,
            json={"device_id": a, "mutations": [_mutation("planning_preferences", "default", base_version=base, payload=_prefs(30 + (i % 30)))]},
        ).json()["outcomes"][0]
        assert out["disposition"] == "applied"
        base = out["record"]["version"]
        latest = out["record"]["server_seq"]
    assert client.post("/v1/sync/ack", headers=headers, json={"device_id": a, "cursor": latest}).status_code == 200
    blocked = client.post("/v1/sync/maintenance/compact", headers=headers)
    assert blocked.status_code == 200
    assert blocked.json()["retained_floor"] == 0
    # Device B catches up. Only now may compaction advance safely.
    pulled = client.get(f"/v1/sync/pull?device_id={b}&cursor=0", headers=headers).json()
    assert pulled["next_cursor"] == latest
    assert client.post("/v1/sync/ack", headers=headers, json={"device_id": b, "cursor": latest}).status_code == 200
    compacted = client.post("/v1/sync/maintenance/compact", headers=headers)
    assert compacted.status_code == 200
    assert compacted.json()["retained_floor"] > 0


def test_sync_device_inventory_is_account_isolated():
    _, h1 = _account("sync-device-owner-a")
    _, h2 = _account("sync-device-owner-b")
    d1 = _device(h1, f"dev-owner-a-{uuid4().hex}")
    d2 = _device(h2, f"dev-owner-b-{uuid4().hex}")
    ids1 = {x["device_id"] for x in client.get("/v1/sync/devices", headers=h1).json()["devices"]}
    ids2 = {x["device_id"] for x in client.get("/v1/sync/devices", headers=h2).json()["devices"]}
    assert d1 in ids1 and d2 not in ids1
    assert d2 in ids2 and d1 not in ids2
    foreign = client.delete(f"/v1/sync/devices/{d1}", headers=h2)
    assert foreign.status_code == 404



def test_course_follow_syncs_across_devices():
    _, headers = _account("sync-follow")
    a = _device(headers, f"dev-a-{uuid4().hex}")
    b = _device(headers, f"dev-b-{uuid4().hex}")
    m = _mutation("course_follow", "course-physio", payload={"courseId":"course-physio","followed":True})
    out = client.post("/v1/sync/push", headers=headers, json={"device_id":a,"mutations":[m]})
    assert out.status_code == 200, out.text
    assert out.json()["outcomes"][0]["disposition"] == "applied"
    page = client.get(f"/v1/sync/pull?device_id={b}&cursor=0&limit=50", headers=headers)
    assert page.status_code == 200, page.text
    rec = [r for r in page.json()["changes"] if r["entity_type"]=="course_follow" and r["entity_id"]=="course-physio"][-1]
    assert rec["payload"] == {"courseId":"course-physio","followed":True}


def test_course_follow_payload_is_strict():
    _, headers = _account("sync-follow-invalid")
    a = _device(headers, f"dev-a-{uuid4().hex}")
    m = _mutation("course_follow", "course-1", payload={"courseId":"course-1","followed":"yes","localUri":"/private/x.pdf"})
    out = client.post("/v1/sync/push", headers=headers, json={"device_id":a,"mutations":[m]})
    assert out.status_code == 422
