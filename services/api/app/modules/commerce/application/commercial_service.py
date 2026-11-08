from __future__ import annotations
import json
from datetime import timedelta
from uuid import uuid4, uuid5, NAMESPACE_URL
from app.modules.commerce.domain.commercial import *
from app.modules.campus.domain.model import CampusRole, MembershipState

ADMIN_ROLES={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN}
class CommercialService:
    def __init__(self, repo, campus_repo, now, audit=None): self.repo=repo; self.campus=campus_repo; self.now=now; self.audit=audit
    def _admin(self,institution_id,actor_id):
        m=self.campus.membership(institution_id,actor_id)
        if not m or m.state!=MembershipState.ACTIVE or m.role not in ADMIN_ROLES: raise PermissionError('campus_commerce_admin_required')
    def create_license(self,*,institution_id,actor_id,plan_code,seats,price_cdf,duration_days=365,grace_days=14):
        self._admin(institution_id,actor_id)
        if price_cdf != 0:
            raise ValueError('verified_payment_required_for_paid_campus_license')
        if not isinstance(seats, int) or isinstance(seats, bool) or not 1 <= seats <= 100000:
            raise ValueError('invalid_license_seats')
        if not isinstance(price_cdf, int) or isinstance(price_cdf, bool) or price_cdf < 0:
            raise ValueError('invalid_license_price')
        if not 1 <= duration_days <= 3660 or not 0 <= grace_days <= 90:
            raise ValueError('invalid_license_duration')
        if not isinstance(plan_code, str) or not plan_code.strip() or plan_code != plan_code.strip() or len(plan_code)>128 or any(ord(c)<32 or ord(c)==127 for c in plan_code):
            raise ValueError('invalid_plan_code')
        now=self.now()
        lic=CampusLicense(str(uuid4()),institution_id,plan_code,LicenseState.ACTIVE,seats,price_cdf,now,now+timedelta(days=duration_days),now+timedelta(days=duration_days+grace_days),actor_id,now)
        self.repo.save_license(lic)
        # A complimentary administrative grant is not revenue: never invent a 1 FC charge.
        # The license itself and audit record provide the non-financial trace.
        if self.audit:self.audit.write(actor_id=actor_id,action='commerce.campus_license.created',entity_type='campus_license',entity_id=lic.id,metadata={'institution_id':institution_id,'seats':seats})
        return lic
    def renew_license(self, *, institution_id, actor_id, renewal_reference, plan_code, seats, price_cdf, duration_days=365, grace_days=14):
        """Administrative provisioning only; never initiates or confirms a payment."""
        self._admin(institution_id, actor_id)
        if price_cdf != 0:
            raise ValueError('verified_payment_required_for_paid_campus_renewal')
        if (not isinstance(renewal_reference, str) or not 1 <= len(renewal_reference) <= 128
            or renewal_reference != renewal_reference.strip()
            or any(ord(char) < 32 or ord(char) == 127 for char in renewal_reference)):
            raise ValueError('invalid_renewal_reference')
        if not isinstance(seats, int) or isinstance(seats, bool) or not 1 <= seats <= 100000:
            raise ValueError('invalid_license_seats')
        if not isinstance(price_cdf, int) or isinstance(price_cdf, bool) or price_cdf < 0:
            raise ValueError('invalid_license_price')
        if not 1 <= duration_days <= 3660 or not 0 <= grace_days <= 90:
            raise ValueError('invalid_license_duration')
        if (not isinstance(plan_code, str) or not plan_code.strip()
            or plan_code != plan_code.strip() or len(plan_code)>128
            or any(ord(c)<32 or ord(c)==127 for c in plan_code)):
            raise ValueError('invalid_plan_code')
        now = self.now()
        license_id = str(uuid5(NAMESPACE_URL, f'edunova:campus-renewal:{institution_id}:{renewal_reference}'))
        lic = self.repo.renew_license_atomic(
            institution_id=institution_id, license_id=license_id, plan_code=plan_code,
            seats=seats, price_cdf=price_cdf, duration_days=duration_days,
            grace_days=grace_days, actor_id=actor_id, now=now,
        )
        return lic

    def license_status(self,institution_id):
        lic=self.repo.current_license(institution_id); active=self.campus.overview(institution_id)['students_active']; now=self.now()
        return {'license':lic,'effective_state':lic.effective_state(now).value if lic else None,'active_students':active,'permitted':bool(lic and lic.permits(now,active)),'seat_overage':max(0,active-(lic.seats if lic else 0))}
    def suspend_license(self,*,institution_id,actor_id):
        self._admin(institution_id,actor_id); lic=self.repo.current_license(institution_id)
        if not lic:raise ValueError('license_not_found')
        self.repo.update_license_state(lic.id,LicenseState.SUSPENDED);return self.repo.current_license(institution_id)
    def cancel_license(self,*,institution_id,actor_id):
        self._admin(institution_id,actor_id); lic=self.repo.current_license(institution_id)
        if not lic:raise ValueError('license_not_found')
        self.repo.update_license_state(lic.id,LicenseState.CANCELED);return self.repo.current_license(institution_id)
    def create_partner(self,*,actor_id,institution_id,name,share_bps):
        self._admin(institution_id,actor_id); p=RevenuePartner(str(uuid4()),name,share_bps,PartnerState.ACTIVE,self.now()); self.repo.save_partner(p); return p
    def create_share_rule(self,*,actor_id,institution_id,partner_id,share_bps,product_code=None):
        self._admin(institution_id,actor_id); r=RevenueShareRule(str(uuid4()),partner_id,institution_id,product_code,share_bps,self.now(),None); self.repo.save_rule(r); return r
    def record_revenue_share(self,*,institution_id,account_id,product_code,reference_id,gross_cdf):
        if gross_cdf<=0:raise ValueError('invalid_gross_amount')
        rule=self.repo.active_rule(institution_id,product_code,self.now())
        if not rule:return None
        partner=(gross_cdf*rule.share_bps)//10000; platform=gross_cdf-partner; now=self.now()
        # Idempotent business event: duplicate provider callbacks cannot duplicate revenue.
        if self.repo.ledger_has(LedgerKind.PAYMENT,'payment',reference_id,rule.partner_id):return {'gross_cdf':gross_cdf,'partner_cdf':partner,'platform_cdf':platform,'partner_id':rule.partner_id,'duplicate':True}
        self.repo.append_ledger(CommercialLedgerEntry(str(uuid4()),institution_id,account_id,rule.partner_id,LedgerKind.PAYMENT,'payment',reference_id,gross_cdf,now))
        if partner:self.repo.append_ledger(CommercialLedgerEntry(str(uuid4()),institution_id,account_id,rule.partner_id,LedgerKind.PARTNER_SHARE,'payment',reference_id,-partner,now))
        return {'gross_cdf':gross_cdf,'partner_cdf':partner,'platform_cdf':platform,'partner_id':rule.partner_id,'duplicate':False}
    def record_refund(self,*,institution_id,account_id,product_code,reference_id,original_reference_id,gross_cdf):
        if gross_cdf<=0:raise ValueError('invalid_refund_amount')
        rule=self.repo.active_rule(institution_id,product_code,self.now());now=self.now()
        if not rule:return None
        partner=(gross_cdf*rule.share_bps)//10000
        if self.repo.ledger_has(LedgerKind.REFUND,'refund',reference_id,rule.partner_id):return {'duplicate':True}
        meta=json.dumps({'original_reference_id':original_reference_id},sort_keys=True)
        self.repo.append_ledger(CommercialLedgerEntry(str(uuid4()),institution_id,account_id,rule.partner_id,LedgerKind.REFUND,'refund',reference_id,-gross_cdf,now,meta))
        if partner:self.repo.append_ledger(CommercialLedgerEntry(str(uuid4()),institution_id,account_id,rule.partner_id,LedgerKind.ADJUSTMENT,'refund',reference_id,partner,now,meta))
        return {'gross_cdf':-gross_cdf,'partner_cdf':-partner,'platform_cdf':-(gross_cdf-partner),'partner_id':rule.partner_id,'duplicate':False}
    def settle_partner(self,*,actor_id,institution_id,partner_id,period_start,period_end):
        self._admin(institution_id,actor_id)
        if period_end<=period_start:raise ValueError('invalid_settlement_period')
        rows=self.repo.partner_entries(partner_id,period_start,period_end)
        gross=sum(x.amount_cdf for x in rows if x.kind in {LedgerKind.PAYMENT,LedgerKind.REFUND})
        partner=-sum(x.amount_cdf for x in rows if x.kind==LedgerKind.PARTNER_SHARE)-sum(x.amount_cdf for x in rows if x.kind==LedgerKind.ADJUSTMENT)
        platform=gross-partner
        s=PartnerSettlement(str(uuid4()),partner_id,period_start,period_end,gross,partner,platform,SettlementState.CALCULATED.value,self.now()); return self.repo.save_settlement(s)
    def close_settlement(self,*,actor_id,institution_id,settlement_id):
        self._admin(institution_id,actor_id);return self.repo.transition_settlement(settlement_id,{SettlementState.CALCULATED.value},SettlementState.CLOSED.value)
    def mark_settlement_paid(self,*,actor_id,institution_id,settlement_id):
        self._admin(institution_id,actor_id);s=self.repo.transition_settlement(settlement_id,{SettlementState.CLOSED.value},SettlementState.PAID.value)
        self.repo.append_ledger(CommercialLedgerEntry(str(uuid4()),institution_id,None,s.partner_id,LedgerKind.SETTLEMENT,'partner_settlement',s.id,-max(s.partner_cdf,1),self.now()))
        return s
    def reconcile_provider(self,*,provider,expected_payments,provider_records):
        # expected/provider records: iterable of {'reference': str, 'amount_cdf': int}
        exp={x['reference']:int(x['amount_cdf']) for x in expected_payments}; got={x['reference']:int(x['amount_cdf']) for x in provider_records}
        missing=tuple(sorted(set(exp)-set(got)));unknown=tuple(sorted(set(got)-set(exp)));mismatch=tuple(sorted(k for k in set(exp)&set(got) if exp[k]!=got[k]))
        return ReconciliationResult(provider,len(exp),len(set(exp)&set(got))-len(mismatch),missing,mismatch,unknown)
