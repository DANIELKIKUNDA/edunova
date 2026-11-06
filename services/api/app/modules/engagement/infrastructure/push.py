from __future__ import annotations


class DisabledPushSender:
    def send(self, *, tokens: tuple[str, ...], title: str, body: str, deep_link: str) -> tuple[str, ...]:
        return tuple()


class FirebaseAdminPushSender:
    """FCM adapter loaded lazily so local development never needs Firebase credentials."""
    def __init__(self) -> None:
        try:
            import firebase_admin
            from firebase_admin import credentials
        except ImportError as exc:  # pragma: no cover - production dependency
            raise RuntimeError("firebase_admin_not_installed") from exc
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()

    def send(self, *, tokens: tuple[str, ...], title: str, body: str, deep_link: str) -> tuple[str, ...]:
        if not tokens:
            return tuple()
        from firebase_admin import messaging
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={"deep_link": deep_link},
            tokens=list(tokens),
        )
        response = messaging.send_each_for_multicast(message)
        invalid = []
        for token, result in zip(tokens, response.responses):
            if result.success:
                continue
            code = getattr(getattr(result, "exception", None), "code", "") or ""
            if "registration-token-not-registered" in str(code) or "invalid-registration-token" in str(code):
                invalid.append(token)
        return tuple(invalid)
