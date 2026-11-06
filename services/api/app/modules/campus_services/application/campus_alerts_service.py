"""Private, on-demand Campus alert feed. NOT a push/email/SMS dispatcher.

Rules are non-destructive: an alert disappears after the underlying loan is
returned, booking no longer relevant, or registration withdrawn. No cached
membership, no snapshot of another tenant and no read acknowledgments.
"""
from __future__ import annotations
from datetime import UTC, timedelta


def utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class CampusAlertsService:
    def __init__(self, repo, campus_services, now):
        self.repo, self.services, self.now = repo, campus_services, now

    def for_account(self, account, institution):
        self.services._member(account, institution)
        now = utc(self.now())
        loans, bookings, events = self.repo.evidence(institution, account)
        alerts = []

        def emit(kind, reference, level, title, message, when):
            alerts.append({
                'id': f'{kind}:{reference}', 'kind': kind, 'reference_id': reference,
                'level': level, 'title': title, 'message': message,
                'occurs_at': utc(when).isoformat(),
            })

        for identifier, due in loans:
            deadline = utc(due)
            if deadline <= now:
                emit('library_overdue', identifier, 'urgent', 'Livre en retard',
                     'Veuillez contacter la bibliothèque pour restituer votre exemplaire.', deadline)
            elif deadline <= now + timedelta(days=3):
                emit('library_due', identifier, 'warning', 'Retour de livre prochain',
                     'Votre emprunt arrive bientôt à échéance.', deadline)

        for identifier, ends, changed in bookings:
            if now - timedelta(days=7) <= utc(ends) and utc(changed) <= now:
                emit('booking_maintenance', identifier, 'warning', 'Réservation annulée',
                     'Cette réservation a été annulée en raison d’une maintenance.', changed)

        for identifier, starts, ends, state in events:
            start = utc(starts)
            if state == 'cancelled':
                if utc(ends) >= now - timedelta(days=7):
                    emit('event_cancelled', identifier, 'warning', 'Événement annulé',
                         'Un événement auquel vous êtes inscrit a été annulé.', start)
            elif now < start <= now + timedelta(hours=24):
                emit('event_soon', identifier, 'info', 'Événement prochain',
                     'Un événement auquel vous êtes inscrit commence bientôt.', start)

        # Finite, stable feed even if a member has a very large history.
        rank = {'urgent': 0, 'warning': 1, 'info': 2}
        alerts.sort(key=lambda item: (rank[item['level']], item['occurs_at'], item['id']))
        return alerts[:50]
