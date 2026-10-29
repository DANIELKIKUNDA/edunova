#!/usr/bin/env python3
"""Dispatch due EduNova push notifications.

Production usage: run from the API container via cron/systemd timer every 1-5 minutes.
If FCM_ENABLED is false, the command is a safe no-op.
"""
from app.runtime import runtime

if __name__ == "__main__":
    print(runtime.engagement.dispatch_due_push(limit=200))
