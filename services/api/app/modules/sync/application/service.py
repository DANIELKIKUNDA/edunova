from __future__ import annotations

from datetime import datetime

from app.modules.sync.application.ports import SyncRepository
from app.modules.sync.domain.model import DeviceRegistration, MutationOutcome, PullPage, SyncMutation, MergePolicy, policy_for, validate_payload_size
from app.modules.sync.application.validation import validate_sync_payload


class SyncService:
    MAX_BATCH = 100
    MAX_PULL = 500

    def __init__(self, repository: SyncRepository, now) -> None:
        self.repository = repository
        self.now = now

    def register_device(self, *, account_id: str, registration: DeviceRegistration) -> None:
        if not registration.device_id.strip() or len(registration.device_id) > 128:
            raise ValueError("invalid_device_id")
        if registration.platform not in {"android", "ios", "web", "windows", "macos", "linux", "unknown"}:
            raise ValueError("invalid_device_platform")
        self.repository.register_device(account_id=account_id, registration=registration, now=self.now())


    def list_devices(self, *, account_id: str):
        return self.repository.list_devices(account_id=account_id)

    def revoke_device(self, *, account_id: str, device_id: str) -> None:
        self.repository.revoke_device(account_id=account_id, device_id=device_id, now=self.now())

    def acknowledge(self, *, account_id: str, device_id: str, cursor: int) -> int:
        if cursor < 0:
            raise ValueError("invalid_sync_cursor")
        return self.repository.acknowledge(account_id=account_id, device_id=device_id, cursor=cursor, now=self.now())

    def compact(self, *, account_id: str) -> dict:
        return self.repository.compact(account_id=account_id, now=self.now())

    def push(self, *, account_id: str, device_id: str, mutations: tuple[SyncMutation, ...]) -> tuple[MutationOutcome, ...]:
        if not mutations:
            return ()
        if len(mutations) > self.MAX_BATCH:
            raise ValueError("sync_batch_too_large")
        seen: set[str] = set()
        outcomes: list[MutationOutcome] = []
        now = self.now()
        for mutation in mutations:
            if mutation.mutation_id in seen:
                raise ValueError("duplicate_mutation_id_in_batch")
            seen.add(mutation.mutation_id)
            policy = policy_for(mutation.entity_type)
            if policy.policy is MergePolicy.LOCAL_ONLY:
                raise ValueError("local_only_entity_cannot_sync")
            if policy.policy is MergePolicy.SERVER_AUTHORITATIVE:
                raise ValueError("server_authoritative_entity_cannot_push")
            validate_payload_size(mutation.payload, policy)
            if mutation.operation.value == "upsert":
                validate_sync_payload(mutation.entity_type, mutation.payload)
            outcomes.append(self.repository.apply_mutation(account_id=account_id, device_id=device_id, mutation=mutation, now=now))
        return tuple(outcomes)

    def pull(self, *, account_id: str, device_id: str, cursor: int = 0, limit: int = 200) -> PullPage:
        if cursor < 0:
            raise ValueError("invalid_sync_cursor")
        self.repository.assert_device_active(account_id=account_id, device_id=device_id, now=self.now())
        floor = self.repository.retained_floor(account_id=account_id)
        if cursor < floor:
            return PullPage(changes=(), next_cursor=floor, has_more=False, retained_floor=floor, reset_required=True)
        limit = max(1, min(limit, self.MAX_PULL))
        page = self.repository.pull(account_id=account_id, cursor=cursor, limit=limit)
        return PullPage(changes=page.changes, next_cursor=page.next_cursor, has_more=page.has_more, retained_floor=floor, reset_required=False)

    def bootstrap(self, *, account_id: str, device_id: str) -> PullPage:
        self.repository.assert_device_active(account_id=account_id, device_id=device_id, now=self.now())
        page = self.repository.snapshot(account_id=account_id)
        floor = self.repository.retained_floor(account_id=account_id)
        return PullPage(changes=page.changes, next_cursor=page.next_cursor, has_more=False, retained_floor=floor, reset_required=False)
