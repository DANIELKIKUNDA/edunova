"""Opt-in alumni: tenant-specific consent and explicit institutional verification."""
from urllib.parse import urlsplit
from ipaddress import ip_address
from app.modules.campus.domain.model import CampusRole, MembershipState, InstitutionState

_ADMINS = frozenset({CampusRole.OWNER, CampusRole.RECTOR, CampusRole.ADMIN, CampusRole.ACADEMIC_ADMIN})


class CampusAlumniService:
    def __init__(self, repo, campus, now, audit=None):
        self.repo, self.campus, self.now, self.audit = repo, campus, now, audit

    def _check_tenant(self, institution):
        target = self.campus.institution(institution)
        if target is None or target.state != InstitutionState.ACTIVE:
            raise PermissionError('alumni_institution_inactive')

    def _member(self, account, institution):
        self._check_tenant(institution)
        m = self.campus.membership(institution, account)
        if m and m.state == MembershipState.ACTIVE:
            return m
        raise PermissionError('alumni_membership_required')

    def _viewer(self, account, institution):
        self._check_tenant(institution)
        m = self.campus.membership(institution, account)
        if m and m.state == MembershipState.ACTIVE:
            return
        # An explicit access revocation/suspension takes precedence over alumni status.
        if m and m.state in {MembershipState.REVOKED, MembershipState.SUSPENDED}:
            raise PermissionError('alumni_membership_revoked')
        # Previously verified alumni keep access to their alumni network after
        # academic membership has expired, but not to campus staff endpoints.
        p = self.repo.own(institution, account)
        if not p or p['status'] != 'verified':
            raise PermissionError('alumni_verified_membership_required')

    def _staff(self, account, institution):
        m = self._member(account, institution)
        if m.role not in _ADMINS:
            raise PermissionError('alumni_administrator_required')

    def _audit(self, account, action, target_id):
        if self.audit:
            self.audit.write(actor_account_id=account, action=action,
                             target_type='campus_alumni', target_id=target_id, metadata={})

    def my_institutions(self, account):
        """Discover only verified personal alumni networks without active enrollment.

        An explicitly suspended/revoked membership always wins. This endpoint
        does not grant new membership or permission to change alumni records.
        """
        result = []
        for institution in self.repo.verified_institutions(account):
            target = self.campus.institution(institution)
            if target is None or target.state != InstitutionState.ACTIVE:
                continue
            membership = self.campus.membership(institution, account)
            if membership and membership.state in (MembershipState.REVOKED, MembershipState.SUSPENDED):
                continue
            result.append({'institution_id': institution, 'name': target.name})
        return result

    def my_profile(self, account, institution):
        self._viewer(account, institution) if self.repo.own(institution, account) else self._member(account, institution)
        return self.repo.own(institution, account)

    def apply(self, account, institution, *, display_name, program_name, graduation_year,
              headline='', visible=False, expected_version=0):
        self._member(account, institution)
        if any(not isinstance(v, str) for v in (display_name, program_name, headline)):
            raise ValueError('alumni_profile_fields_invalid')
        display_name, program_name, headline = display_name.strip(), program_name.strip(), headline.strip()
        if not (2 <= len(display_name) <= 160 and 2 <= len(program_name) <= 160 and len(headline) <= 240):
            raise ValueError('alumni_profile_fields_invalid')
        if type(graduation_year) is not int or not 1950 <= graduation_year <= self.now().year:
            raise ValueError('alumni_graduation_year_invalid')
        if type(visible) is not bool or type(expected_version) is not int or expected_version < 0:
            raise ValueError('alumni_profile_version_invalid')
        result = self.repo.apply(institution, account, dict(display_name=display_name,
            program_name=program_name, graduation_year=graduation_year,
            headline=headline, visible=visible), expected_version, self.now())
        self._audit(account, 'alumni.profile.submitted', result['id'])
        return result

    def pending(self, account, institution):
        self._staff(account, institution)
        return self.repo.pending(institution)

    def decide(self, account, institution, profile_id, expected_version, decision, reference):
        self._staff(account, institution)
        if decision not in ('verified', 'rejected'):
            raise ValueError('alumni_decision_invalid')
        if not isinstance(reference, str) or not 6 <= len(reference.strip()) <= 160:
            raise ValueError('alumni_reference_required')
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('alumni_profile_version_invalid')
        result = self.repo.decide(institution, profile_id, account, expected_version,
                                  decision, reference.strip(), self.now())
        self._audit(account, 'alumni.profile.' + decision, profile_id)
        return result

    def directory(self, account, institution):
        self._viewer(account, institution)
        return self.repo.directory(institution)

    def opportunities(self, account, institution):
        self._viewer(account, institution)
        return self.repo.opportunities(institution)

    def post_opportunity(self, account, institution, title, description, application_url=''):
        self._staff(account, institution)
        if not isinstance(title, str) or not isinstance(description, str) or not isinstance(application_url, str):
            raise ValueError('alumni_opportunity_fields_invalid')
        title, description, application_url = title.strip(), description.strip(), application_url.strip()
        if not (4 <= len(title) <= 180 and 10 <= len(description) <= 2000 and len(application_url) <= 500):
            raise ValueError('alumni_opportunity_fields_invalid')
        if application_url:
            # Published URLs are shown to students/alumni. Refuse ambiguous or
            # local targets (including IP literals), embedded credentials and
            # control characters rather than trusting urlsplit's permissive parse.
            try:
                url = urlsplit(application_url)
                hostname = url.hostname
                port = url.port  # Forces validation of malformed port numbers.
                if (url.scheme != 'https' or not hostname or url.username is not None
                        or url.password is not None or url.fragment
                        or any(c.isspace() or ord(c) < 32 or ord(c) == 127
                               for c in application_url)
                        or hostname.rstrip('.').lower() in {'localhost'}
                        or hostname.lower().endswith(('.localhost', '.local', '.internal'))
                        or '.' not in hostname.rstrip('.')
                        or port == 0):
                    raise ValueError('alumni_opportunity_url_invalid')
                try:
                    ip_address(hostname)
                except ValueError:
                    pass  # Public DNS name; no network lookup is performed.
                else:
                    raise ValueError('alumni_opportunity_url_invalid')
            except (ValueError, TypeError):
                raise ValueError('alumni_opportunity_url_invalid') from None
        result = self.repo.post_opportunity(institution, account, title, description, application_url, self.now())
        self._audit(account, 'alumni.opportunity.published', result['id'])
        return result

    def withdraw_opportunity(self, account, institution, id, expected_version):
        self._staff(account, institution)
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('alumni_opportunity_version_invalid')
        result = self.repo.withdraw_opportunity(institution, id, expected_version, self.now())
        self._audit(account, 'alumni.opportunity.withdrawn', id)
        return result
