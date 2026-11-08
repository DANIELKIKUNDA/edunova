from __future__ import annotations
import json
import os
import secrets
import hmac
from hashlib import sha256
from math import isfinite
from sqlalchemy.exc import SQLAlchemyError
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.institutional_analytics.domain.model import *

class InstitutionalAnalyticsService:
    STAFF={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN,CampusRole.TEACHER,CampusRole.AUDITOR}
    def __init__(self,repo,campus,teaching,audit=None):self.repo=repo;self.campus=campus;self.teaching=teaching;self.audit=audit
    def _authorize(self,actor,i,offering_id=None):
        m=self.campus.membership(i,actor)
        if not m or m.state!=MembershipState.ACTIVE or m.role not in self.STAFF:raise PermissionError('institutional_analytics_staff_required')
        if m.role==CampusRole.TEACHER:
            if not offering_id:raise PermissionError('institutional_analytics_teacher_scope_required')
            a=self.teaching.assignment(offering_id,actor)
            if not a or not a.active:raise PermissionError('institutional_analytics_teacher_scope_denied')
        return m
    # Phase 15/v0.50.5: legacy Lot-27 endpoints MUST NOT bypass the
    # disclosure policy of the governed institutional observatory.  Their
    # original JSON shape is retained, but untrusted/small cells are NULL.
    def _legacy_governed(self,actor,i,*,academic_period_id=None,academic_unit_id=None,
                         cohort_id=None,offering_id=None):
        member=self._authorize(actor,i,offering_id)
        if member.role==CampusRole.TEACHER:
            if academic_unit_id:
                raise PermissionError('institutional_analytics_teacher_unit_denied')
            # _authorize checks assignment; validate tenant AND bound scope.
            off=self.teaching.offering(i,offering_id)
            if not off:raise ValueError('institutional_analytics_offering_not_found')
            if (academic_period_id and off.academic_period_id!=academic_period_id or
                cohort_id and off.cohort_id!=cohort_id):
                raise ValueError('institutional_analytics_scope_mismatch')
            data=self.repo.snapshot(i,academic_period_id,cohort_id,offering_id,governed=True)
            audience=self.repo.distinct_active_students(i,academic_period_id,cohort_id,offering_id)
            metrics=self._governed_metrics(data,audience)
            hierarchy=self._nested_scope_disclosure_safe(i,audience,
                academic_period_id=academic_period_id,cohort_id=cohort_id,offering_id=offering_id)
            peers=(not self.repo.overlapping_cohort_disclosure_risk(i,
                academic_period_id,cohort_id,offering_id)) if hierarchy and audience>=3 else True
            temporal_safe=True
            if audience>=3 and hierarchy and peers:
                temporal_safe=self._temporal_release_safe(i,
                    {'academic_period_id':academic_period_id,'academic_unit_id':None,
                     'cohort_id':cohort_id,'offering_id':offering_id},metrics)
            if not hierarchy:self._suppress_nested_metrics(metrics)
            elif not temporal_safe:self._suppress_nested_metrics(metrics,'temporal_disclosure_suppressed')
            elif not peers:self._suppress_nested_metrics(metrics,'suppressed_overlapping_scope')
            status=('eligible' if audience>=3 and hierarchy and peers and temporal_safe else
                    'nested_difference_suppressed' if not hierarchy else
                    'overlapping_scope_suppressed' if not peers else
                    'temporal_disclosure_suppressed' if not temporal_safe else 'insufficient_population')
            brief={'scope':data['scope'],'metrics':metrics,
                   'data_quality':{'status':status,'unique_active_students':audience if status=='eligible' else None}}
        else:
            brief=self.decision_brief(actor,i,academic_period_id=academic_period_id,
                academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id)
        # Only release a known metric if its EXACT cell passed all of the
        # contributor, integrity, tenant, hierarchy and peer checks.  Never
        # copy a raw counter or an untrusted source into a legacy response.
        metrics=brief['metrics']; visible=lambda key: metrics[key]['status']=='available'
        # Read no second raw projection: mismatched snapshots under concurrent
        # writes could yield a protected rate with an unprotected counter.
        denominator=lambda key: metrics[key]['denominator'] if visible(key) else None
        return {'institution_id':i,'scope':brief['scope'],
            'population':{'active_enrollments':brief['data_quality']['unique_active_students'],
                          'offerings':None},
            'teaching':{
                'sessions_total':denominator('teaching.completion_rate'),
                'sessions_completed':None,
                'completion_rate':metrics['teaching.completion_rate']['value'],
                'topics_total':denominator('teaching.syllabus_coverage_rate'),
                'topics_taught':None,
                'syllabus_coverage_rate':metrics['teaching.syllabus_coverage_rate']['value']},
            'attendance':{'records':metrics['attendance.attendance_rate']['denominator'],
                'present':None,'late':None,'absent':None,'justified':None,
                'attendance_rate':metrics['attendance.attendance_rate']['value'],
                'absence_rate':None},
            'assignments':{'assignments':None,
                'submission_opportunities':metrics['assignments.submission_rate']['denominator'],
                'submitted':None,'submission_rate':metrics['assignments.submission_rate']['value']},
            'results':{'complete_results':metrics['results.pass_rate']['denominator'],
                'passed':None,'pass_rate':metrics['results.pass_rate']['value']},
            'privacy':{'contract_version':3,'status':brief['data_quality']['status'],
                'legacy_raw_counters_suppressed':True,
                'historical_results_non_authoritative':True}}

    def definitions(self,actor,i):self._authorize(actor,i);return METRICS
    def dashboard(self,actor,i,*,academic_period_id=None,cohort_id=None,offering_id=None):
        data=self._legacy_governed(actor,i,academic_period_id=academic_period_id,
                                   cohort_id=cohort_id,offering_id=offering_id)
        if self.audit:self.audit.write(actor_id=actor,action='institutional_analytics.dashboard.viewed',
            entity_type='institution',entity_id=i,metadata={'scope':data['scope'],'contract_version':3})
        return data

    def signals(self,actor,i,*,academic_period_id=None,cohort_id=None,offering_id=None):
        data=self.dashboard(actor,i,academic_period_id=academic_period_id,cohort_id=cohort_id,offering_id=offering_id)
        out=[]
        for section,field,threshold,kind,title in (
            ('attendance','attendance_rate',75,SignalKind.ATTENDANCE,'Assiduité à surveiller'),
            ('assignments','submission_rate',70,SignalKind.SUBMISSION,'Remises à surveiller'),
            ('results','pass_rate',60,SignalKind.PERFORMANCE,'Résultats à examiner'),
            ('teaching','completion_rate',70,SignalKind.DELIVERY,'Réalisation pédagogique à examiner')):
            rate=data[section][field]
            if rate is not None and rate<threshold:
                out.append(InstitutionalSignal(kind,SignalSeverity.WATCH,'scope',
                    offering_id or cohort_id or i,title,
                    f'Indicateur agrégé vérifié: {rate}%.',('institutional analytics governed metric v3',)))
        return tuple(out)

    def unit_dashboard(self,actor,i,unit_id,*,academic_period_id=None):
        return self._legacy_governed(actor,i,academic_period_id=academic_period_id,
                                     academic_unit_id=unit_id)

    def _snapshot_scope(self,actor,i,*,scope_type,scope_id=None,academic_period_id=None):
        allowed={'institution','academic_unit','cohort','offering'}
        if scope_type not in allowed or (scope_type!='institution' and not scope_id) or (scope_type=='institution' and scope_id):
            raise ValueError('institutional_analytics_invalid_snapshot_scope')
        kw={'academic_period_id':academic_period_id}
        if scope_type!='institution':kw[{'academic_unit':'academic_unit_id',
                       'cohort':'cohort_id','offering':'offering_id'}[scope_type]]=scope_id
        # Validate identity and faculty/teacher membership on *every* archival
        # operation, not just at capture. No wildcard history for scoped data.
        self._legacy_governed(actor,i,**kw)
        return kw

    def _temporal_release_safe(self,i,scope,metrics):
        """Lock the FIRST sensitive publication in a persistent institution scope.

        Later reads are allowed only for an identical aggregate AND membership.
        Fail closed on missing server secret, uninitialized ledger, or integrity
        problems; this is a per-scope temporal guard, not differential privacy.
        """
        if not any(metrics[key]['status']=='available' for key in self.STUDENT_METRICS):
            # With no student-level aggregated metric published, a new metric
            # may become eligible in future. Nothing sensitive was released.
            return True
        # An omitted academic period must not create an alternative commitment
        # for the exact same offering/cohort. These are immutable bound scopes.
        scope=dict(scope)
        if not scope.get('academic_period_id'):
            off_id=scope.get('offering_id')
            co_id=scope.get('cohort_id')
            if off_id:
                off=self.teaching.offering(i,off_id)
                if not off:return False
                scope['academic_period_id']=off.academic_period_id
            elif co_id:
                cohort=self.campus.cohort(i,co_id)
                if not cohort:return False
                scope['academic_period_id']=cohort.academic_period_id
        try:
            return self.repo.check_or_lock_live_release(i,scope,
                {k:{'status':v['status'],'value':v['value'],
                    'denominator':v['denominator'],
                    'source_contract':v['source_contract'],
                    'source_lineage_version':v['source_lineage_version']}
                 for k,v in metrics.items()},self._archive_secret())
        except (RuntimeError, ValueError, SQLAlchemyError):
            return False  # missing migration or damaged ledger: no publication

    ARCHIVE_CONTRACT_VERSION=5
    @staticmethod
    def _archive_secret():
        # No predictable fallback. JWT_SECRET is already mandatory in production.
        key=os.getenv('INSTITUTIONAL_ANALYTICS_HMAC_SECRET') or os.getenv('JWT_SECRET')
        if not key or len(key)<32:
            raise RuntimeError('institutional_analytics_archive_secret_not_configured')
        return key

    def _archive_proof(self,i,kw,nonce):
        return self.repo.population_membership_proof(i,
            period_id=kw.get('academic_period_id'),
            academic_unit_id=kw.get('academic_unit_id'),
            cohort_id=kw.get('cohort_id'),offering_id=kw.get('offering_id'),
            nonce=nonce,secret=self._archive_secret())

    def capture_snapshot(self,actor,i,*,academic_period_id=None,academic_unit_id=None,cohort_id=None,offering_id=None):
        member=self._authorize(actor,i,offering_id)
        if member.role == CampusRole.AUDITOR:
            # The auditor may inspect governed analytics, never create a new archive.
            raise PermissionError('institutional_analytics_auditor_read_only')
        selected=[('academic_unit',academic_unit_id),('cohort',cohort_id),('offering',offering_id)]
        nonempty=[x for x in selected if x[1] is not None]
        if len(nonempty)>1:raise ValueError('institutional_analytics_ambiguous_snapshot_scope')
        scope_type,scope_id=nonempty[0] if nonempty else ('institution',None)
        self._snapshot_scope(actor,i,scope_type=scope_type,scope_id=scope_id,academic_period_id=academic_period_id)
        payload=self._legacy_governed(actor,i,academic_period_id=academic_period_id,
                 academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id)
        kw={'academic_period_id':academic_period_id,'academic_unit_id':academic_unit_id,
            'cohort_id':cohort_id,'offering_id':offering_id}
        nonce=secrets.token_hex(24)
        public_canonical=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        secret=self._archive_secret()
        content_proof=hmac.new(secret.encode(),
            ('edunova:institutional-archive:v5:'+i+':'+nonce+':'+public_canonical).encode(),
            sha256).hexdigest()
        proof={'version':5,'nonce':nonce,'membership_hmac':self._archive_proof(i,kw,nonce),
               'payload_hmac':content_proof}
        snap=self.repo.save_immutable_snapshot(i,payload,scope_type,scope_id,academic_period_id,
            metric_contract_version=self.ARCHIVE_CONTRACT_VERSION,private_proof=proof)
        if self.audit:self.audit.write(actor_id=actor,action='institutional_analytics.snapshot.created',
            entity_type=scope_type,entity_id=scope_id or i,metadata={'snapshot_id':snap['id'],'contract_version':5})
        return snap

    def history(self,actor,i,*,scope_type,scope_id=None,academic_period_id=None,limit=50):
        kw=self._snapshot_scope(actor,i,scope_type=scope_type,scope_id=scope_id,
                                academic_period_id=academic_period_id)
        current=self._legacy_governed(actor,i,**kw)
        permitted=current['privacy']['status']=='eligible'
        items=self.repo.list_snapshots(i,scope_type,scope_id,academic_period_id,limit)
        earliest=self.repo.first_snapshot_id(i,scope_type,scope_id)
        out=[]
        for index,item in enumerate(items):
            item=dict(item)
            proof=(item.get('payload') or {}).get('_internal_archive_proof')
            # Pre-v5 snapshots lack BOTH bound membership and authenticated content.
            # Releasing them would enable forgery or historical differencing.
            verified=(item['metric_contract_version']==5 and
                isinstance(proof,dict) and proof.get('version')==5 and
                isinstance(proof.get('nonce'),str) and len(proof['nonce'])==48 and
                isinstance(proof.get('membership_hmac'),str) and
                len(proof['membership_hmac'])==64 and
                isinstance(proof.get('payload_hmac'),str) and
                len(proof['payload_hmac'])==64 and
                item.get('stored_integrity_ok') is True)
            if verified:
                read_kw=dict(kw)
                read_kw['academic_period_id']=item['academic_period_id']
                try:
                    public={k:v for k,v in item['payload'].items()
                            if k!='_internal_archive_proof'}
                    canonical=json.dumps(public,sort_keys=True,separators=(',',':'),ensure_ascii=False)
                    expected=hmac.new(self._archive_secret().encode(),
                        ('edunova:institutional-archive:v5:'+i+':'+proof['nonce']+':'+canonical).encode(),
                        sha256).hexdigest()
                    verified=(hmac.compare_digest(proof['membership_hmac'],
                        self._archive_proof(i,read_kw,proof['nonce'])) and
                        hmac.compare_digest(proof['payload_hmac'],expected))
                except RuntimeError:
                    verified=False  # missing/rotated signing configuration: fail closed
            if not permitted:
                status='current_scope_suppressed'
            elif item['metric_contract_version']<5:
                status='legacy_unverified_snapshot'
            elif not verified:
                status='capture_population_or_integrity_changed'
            elif item['id']!=earliest:
                # Once any snapshot of this exact scope was exposed, NEVER
                # expose a later one, even through a period filter or limit=1.
                status='historical_temporal_suppressed'
            else:
                status='governed_current_archive'
            # Internal HMAC/nonce must never be returned even on the happy path.
            item.pop('stored_integrity_ok',None)
            if status=='governed_current_archive':
                item['payload']={k:v for k,v in item['payload'].items()
                                 if k!='_internal_archive_proof'}
            else:
                item['payload']=None
                item['content_sha256']=None
            item['privacy_status']=status
            out.append(item)
        return tuple(out)

    def compare_snapshots(self,actor,i,*,scope_type,scope_id=None,academic_period_id=None):
        xs=self.history(actor,i,scope_type=scope_type,scope_id=scope_id,
                        academic_period_id=academic_period_id,limit=2)
        if len(xs)<2:return {'available':False,'reason':'at_least_two_snapshots_required','items':list(xs)}
        current,previous=xs[0],xs[1]
        if not current['payload'] or not previous['payload']:
            return {'available':False,'reason':'unverified_or_privacy_suppressed_snapshots',
                    'items':[{'id':x['id'],'privacy_status':x['privacy_status']} for x in xs]}
        paths=(('attendance','attendance_rate'),('assignments','submission_rate'),
               ('results','pass_rate'),('teaching','completion_rate'),('teaching','syllabus_coverage_rate'))
        deltas={}
        for section,name in paths:
            old=previous['payload'][section][name];new=current['payload'][section][name]
            deltas[f'{section}.{name}']={'previous':old,'current':new,
                'delta':round(new-old,2) if old is not None and new is not None else None}
        return {'available':True,'previous_snapshot_id':previous['id'],
                'current_snapshot_id':current['id'],'deltas':deltas}

    def pedagogical_intelligence(self,actor,i,*,academic_period_id=None,cohort_id=None,offering_id=None):
        # The Lot-27 pedagogical aggregator joins attempt results by course
        # without a complete enrolled-learner/provenance contract.  Suppress
        # those legacy cells rather than claiming their tenant safety.
        self._legacy_governed(actor,i,academic_period_id=academic_period_id,
                              cohort_id=cohort_id,offering_id=offering_id)
        return {'assessment':{'attempts':None,'average_percent':None,'pass_rate':None,'by_bloom':{}},
            'knowledge_graph':{'published_concepts':None,'published_relations':None,'courses_covered':None},
            'interpretation':{'weakest_bloom_levels':[],
                'explanation':'Agrégats historiques non certifiés pour ce périmètre; utiliser les indicateurs gouvernés.',
                'automatic_judgement':False},'privacy':{'status':'unverified_legacy_lineage'}}

    def executive_report(self,actor,i,*,academic_period_id=None,academic_unit_id=None,cohort_id=None,offering_id=None):
        base=self._legacy_governed(actor,i,academic_period_id=academic_period_id,
                                   academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id)
        # Never call raw legacy pedagogical aggregation, even via the unit path.
        pedagogy={'assessment':{'attempts':None,'average_percent':None,'pass_rate':None,'by_bloom':{}},
            'knowledge_graph':{'published_concepts':None,'published_relations':None,'courses_covered':None},
            'interpretation':{'weakest_bloom_levels':[], 'automatic_judgement':False,
                'explanation':'Source pedagogique historique non certifiee'},
            'privacy':{'status':'unverified_legacy_lineage'}}
        signals=[] if academic_unit_id else self.signals(actor,i,academic_period_id=academic_period_id,
                                                        cohort_id=cohort_id,offering_id=offering_id)
        return {'contract_version':3,'generated_from':'governed_institutional_sources_only',
            'scope':base['scope'],'kpis':{k:base[k] for k in ('population','teaching','attendance','assignments','results')},
            'pedagogical_intelligence':pedagogy,
            'signals':[{'kind':x.kind.value,'severity':x.severity.value,'title':x.title,
                        'explanation':x.explanation,'evidence':list(x.evidence)} for x in signals],
            'privacy':{'personal_tutor':False,'private_documents':False,
                       'private_study_activity':False,'individual_answers':False},
            'disclosure':base['privacy']}
    # Phase 15: reuses the Lot-27 institutional projections, never individual answers,
    # Student Success case files, tutors, or jury decisions. This is decision *support*,
    # not an automatic administrative decision.
    INTELLIGENCE_ROLES={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,
                        CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN,CampusRole.AUDITOR}
    MIN_DISCLOSURE_STUDENTS=3
    MIN_PERIOD_COMPARISON_STUDENTS=5
    STUDENT_METRICS=frozenset({'attendance.attendance_rate',
        'assignments.submission_rate','results.pass_rate'})
    INTELLIGENCE_METRICS={
        'teaching.completion_rate':('teaching','completion_rate','sessions_total'),
        'teaching.syllabus_coverage_rate':('teaching','syllabus_coverage_rate','topics_total'),
        'attendance.attendance_rate':('attendance','attendance_rate','records'),
        'assignments.submission_rate':('assignments','submission_rate','submission_opportunities'),
        'results.pass_rate':('results','pass_rate','complete_results'),
    }

    def _intelligence_scope(self,actor,i,*,academic_period_id=None,academic_unit_id=None,cohort_id=None,offering_id=None):
        m=self._authorize(actor,i,offering_id)
        if m.role not in self.INTELLIGENCE_ROLES:
            raise PermissionError('institutional_intelligence_decision_staff_required')
        if academic_unit_id and (offering_id or cohort_id):
            raise ValueError('institutional_intelligence_ambiguous_scope')
        if academic_period_id and not self.campus.period(i,academic_period_id):
            raise ValueError('institutional_intelligence_period_not_found')
        if academic_unit_id:
            unit=self.campus.unit(i,academic_unit_id)
            if not unit or not unit.active:raise ValueError('institutional_intelligence_unit_not_found')
        if cohort_id:
            co=self.campus.cohort(i,cohort_id)
            if not co or not co.active:raise ValueError('institutional_intelligence_cohort_not_found')
            if academic_period_id and co.academic_period_id!=academic_period_id:
                raise ValueError('institutional_intelligence_scope_mismatch')
        if offering_id:
            off=self.teaching.offering(i,offering_id)
            if not off:raise ValueError('institutional_intelligence_offering_not_found')
            if (academic_period_id and off.academic_period_id!=academic_period_id or
                cohort_id and off.cohort_id!=cohort_id):
                raise ValueError('institutional_intelligence_scope_mismatch')
        if m.role==CampusRole.FACULTY_ADMIN:
            if not m.unit_id or not academic_unit_id:
                raise PermissionError('institutional_intelligence_faculty_unit_required')
            # A unit administrator cannot request its parent or a sibling subtree.
            cur=academic_unit_id; seen=set()
            while cur and cur not in seen and cur!=m.unit_id:
                seen.add(cur)
                node=self.campus.unit(i,cur)
                cur=node.parent_id if node and node.active else None
            if cur!=m.unit_id:raise PermissionError('institutional_intelligence_unit_scope_denied')
        return m

    # Definition/lineage are explicitly versioned. These are descriptive
    # statistical sources, not a database or cryptographic attestation.
    SOURCE_CONTRACTS={
        'teaching':'institutional_teaching_sessions',
        'attendance':'closed_clear_attendance',
        'assignments':'eligible_assignment_submissions',
        'results':'published_validated_gradebook',
    }
    SOURCE_LINEAGE_VERSION=2
    MIN_COMPARABLE_REACH_PERCENT=80.0
    REACH_METRICS=frozenset({'attendance.attendance_rate','results.pass_rate'})

    @staticmethod
    def _governed_metrics(data,unique_students):
        enough=isinstance(unique_students,int) and not isinstance(unique_students,bool) and unique_students>=InstitutionalAnalyticsService.MIN_DISCLOSURE_STUDENTS
        metrics={}
        provenance=data.get('_metric_contributors',{})
        if not isinstance(provenance,dict):provenance={}
        integrity=data.get('_source_integrity',{})
        if not isinstance(integrity,dict):integrity={}
        for name,(section,metric,denominator) in InstitutionalAnalyticsService.INTELLIGENCE_METRICS.items():
            group=data.get(section,{})
            if not isinstance(group,dict):group={}
            count=group.get(denominator)
            contributors=provenance.get(name)
            safe_contributors=(type(contributors) is int and contributors>=3 and
                type(unique_students) is int and contributors<=unique_students) if name in InstitutionalAnalyticsService.STUDENT_METRICS else True
            source_valid=(integrity.get(name) is True if name in InstitutionalAnalyticsService.REACH_METRICS else integrity.get(name,True) is True)
            value=group.get(metric)
            number_valid=(type(value) in (int,float) and isfinite(value) and 0<=value<=100)
            released=bool(enough and type(count) is int and count>=3 and safe_contributors and number_valid and source_valid)
            suppressed=not enough or type(count) is not int or count<3 or not safe_contributors
            source_contract=InstitutionalAnalyticsService.SOURCE_CONTRACTS[section]
            # Participation reach is NOT completeness of all expected events.
            # It measures how much of the enrolled population contributed at
            # least one *eligible* observation, without revealing small cells.
            reach=(round(contributors/unique_students*100,2) if released and name in InstitutionalAnalyticsService.REACH_METRICS else None)
            reach_status=('sufficient_observed_population' if reach is not None and
                reach>=InstitutionalAnalyticsService.MIN_COMPARABLE_REACH_PERCENT else
                'limited_observed_population' if reach is not None else 'not_estimated')
            # A public-release fingerprint contains only already-disclosable
            # aggregates and a versioned contract (never student identifiers).
            digest=(sha256(json.dumps({'metric':name,'value':value,
                    'denominator':count,'scope':data.get('scope'),
                    'institution_id':data.get('institution_id'),
                    'source_contract':source_contract,
                    'source_lineage_version':InstitutionalAnalyticsService.SOURCE_LINEAGE_VERSION},
                    sort_keys=True,separators=(',',':')).encode()).hexdigest() if released else None)
            metrics[name]={
                'value':value if released else None,
                'denominator':count if released else None,
                'status':'available' if released else ('suppressed_small_population' if suppressed else 'unavailable_or_untrusted_source'),
                'definition_version':1,
                'source_contract':source_contract,
                'source_lineage_version':InstitutionalAnalyticsService.SOURCE_LINEAGE_VERSION,
                'source_fingerprint_sha256':digest,
                'population_reach':{'percent':reach,'status':reach_status,
                    'definition':'distinct eligible observed learners / distinct active learners' if name in InstitutionalAnalyticsService.REACH_METRICS else 'not_estimated_for_this_source'},
            }
        return metrics

    MIN_SAFE_COMPLEMENT_STUDENTS=3

    def _nested_scope_disclosure_safe(self,i,audience,*,academic_period_id=None,
            academic_unit_id=None,cohort_id=None,offering_id=None):
        """Protect a small *complement* when releasing nested, overlapping views.

        E.g. a parent institution with 4 learners and a cohort with 3:
        subtracting two public aggregations could reveal the fourth learner's
        contribution. This guard releases no metric/count/fingerprint for the
        nested scope in that case. This is a local hierarchical safeguard, NOT
        a guarantee against arbitrary cross-query inference or updates over time.
        """
        if not any((academic_unit_id,cohort_id,offering_id)):
            return True
        parent_period_id=academic_period_id
        if parent_period_id is None and offering_id:
            off=self.teaching.offering(i,offering_id)
            if not off: return False
            parent_period_id=off.academic_period_id
        if parent_period_id is None and cohort_id:
            co=self.campus.cohort(i,cohort_id)
            if not co: return False
            parent_period_id=co.academic_period_id
        parent_count=self.repo.distinct_active_students(i,parent_period_id)
        if type(parent_count) is not int or parent_count<audience:
            return False
        difference=parent_count-audience
        return difference==0 or difference>=self.MIN_SAFE_COMPLEMENT_STUDENTS

    @staticmethod
    def _suppress_nested_metrics(metrics,reason="suppressed_nested_difference"):
        # No value, denominator, population coverage or fingerprint may survive.
        for entry in metrics.values():
            entry['value']=None
            entry['denominator']=None
            entry['source_fingerprint_sha256']=None
            entry['status']=reason
            entry['population_reach']['percent']=None
            entry['population_reach']['status']='not_estimated'
        return metrics

    def decision_brief(self,actor,i,*,academic_period_id=None,academic_unit_id=None,cohort_id=None,offering_id=None):
        """Non-authoritative, privacy-governed institutional observatory v1."""
        self._intelligence_scope(actor,i,academic_period_id=academic_period_id,
            academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id)
        if academic_unit_id:
            data=self.repo.snapshot_for_unit(i,academic_unit_id,academic_period_id,governed=True)
        else:
            data=self.repo.snapshot(i,academic_period_id,cohort_id,offering_id,governed=True)
        audience=self.repo.distinct_active_students(i,academic_period_id,cohort_id,offering_id,academic_unit_id)
        metrics=self._governed_metrics(data,audience)
        hierarchy_safe=self._nested_scope_disclosure_safe(i,audience,
            academic_period_id=academic_period_id,academic_unit_id=academic_unit_id,
            cohort_id=cohort_id,offering_id=offering_id)
        # Static peer-cohort suppression complements the parent/child guard:
        # two otherwise releasable, overlapping cohorts can differ by only
        # one student even when both have large parent complements.
        overlap_safe=True
        if hierarchy_safe and audience>=self.MIN_DISCLOSURE_STUDENTS and any(
                (academic_unit_id,cohort_id,offering_id)):
            overlap_safe=not self.repo.overlapping_cohort_disclosure_risk(i,
                academic_period_id,cohort_id,offering_id,academic_unit_id)
        if not hierarchy_safe:
            self._suppress_nested_metrics(metrics)
        elif not overlap_safe:
            self._suppress_nested_metrics(metrics,'suppressed_overlapping_scope')
        scope={'academic_period_id':academic_period_id,'academic_unit_id':academic_unit_id,
               'cohort_id':cohort_id,'offering_id':offering_id}
        temporal_safe=True
        if hierarchy_safe and overlap_safe and audience>=self.MIN_DISCLOSURE_STUDENTS:
            temporal_safe=self._temporal_release_safe(i,scope,metrics)
            if not temporal_safe:
                self._suppress_nested_metrics(metrics,'temporal_disclosure_suppressed')
        findings=[]
        for key,level,threshold in (('attendance.attendance_rate','watch',75),
                                    ('assignments.submission_rate','watch',70),
                                    ('results.pass_rate','watch',60),
                                    ('teaching.completion_rate','watch',70)):
            metric=metrics[key]
            if (metric['status']=='available' and metric['value']<threshold and
                (key not in self.REACH_METRICS or
                 metric['population_reach']['status']=='sufficient_observed_population')):
                findings.append({'metric':key,'level':level,'observed':metric['value'],
                    'threshold':threshold,'message':'Vérification institutionnelle recommandée',
                    'automatic_decision':False})
        scope={'academic_period_id':academic_period_id,'academic_unit_id':academic_unit_id,
               'cohort_id':cohort_id,'offering_id':offering_id}
        if self.audit:self.audit.write(actor_id=actor,action='institutional_intelligence.brief.viewed',
            entity_type='institution',entity_id=i,metadata={'scope':scope,'contract_version':1})
        return {'contract_version':1,'institution_id':i,'scope':scope,
            'data_quality':{'unique_active_students':audience if audience>=3 and hierarchy_safe and overlap_safe and temporal_safe else None,
                            'minimum_disclosure_population':3,
                            'minimum_safe_complement_population':self.MIN_SAFE_COMPLEMENT_STUDENTS,
                            'status':('nested_difference_suppressed' if not hierarchy_safe else
                                      'overlapping_scope_suppressed' if not overlap_safe else
                                      'temporal_disclosure_suppressed' if not temporal_safe else
                                      'eligible' if audience>=3 else 'insufficient_population'),
                            'limitations':['rates are observational, not causal',
                              'small hierarchical complements and small peer-cohort differences are suppressed; per-scope temporal commitments prevent changed live re-publication but cross-scope inference remains a disclosure risk',
                              'population reach is not proof of complete capture of all eligible events',
                              'completeness varies by source; validated results only for gradebook',
                              'non-authoritative; no jury, gradebook or student case is modified']},
            'metrics':metrics,'findings':findings,
            'policy':{'automatic_decision':False,'individual_level':False,
                      'student_identity_exposed':False,'private_learning_data_used':False}}

    EXECUTIVE_ACTIONS={
        'teaching.completion_rate': 'Vérifier avec la direction des études la réalisation des séances prévues.',
        'teaching.syllabus_coverage_rate': 'Examiner la progression des contenus avec les départements.',
        'attendance.attendance_rate': 'Examiner les modalités de suivi des présences sans cibler d’étudiant.',
        'assignments.submission_rate': 'Examiner les modalités institutionnelles de remise des travaux.',
        'results.pass_rate': 'Demander une revue pédagogique des évaluations publiées, sans décision automatique.',
    }

    def executive_readout(self,actor,i,*,academic_period_id=None,academic_unit_id=None,
                          cohort_id=None,offering_id=None):
        """Actionable but non-authoritative view over ALREADY governed brief data.

        No extra raw query, student identifier, or rate from suppressed cells.
        Recommendations are procedural, not inferences about individual learners.
        """
        brief=self.decision_brief(actor,i,academic_period_id=academic_period_id,
            academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id)
        indicators=[]; priorities=[]
        signalled={f['metric']:f for f in brief['findings']}
        for key,metric in brief['metrics'].items():
            item={'metric':key,'status':metric['status'],
                  'observed_percent':metric['value'] if metric['status']=='available' else None,
                  'population_reach_status':metric['population_reach']['status'],
                  'source_contract':metric['source_contract'],
                  'source_lineage_version':metric['source_lineage_version'],
                  'source_fingerprint_sha256':metric['source_fingerprint_sha256']}
            indicators.append(item)
            if key in signalled and metric['status']=='available':
                priorities.append({'metric':key,'priority':'review',
                    'observed_percent':metric['value'],
                    'recommended_action':self.EXECUTIVE_ACTIONS[key],
                    'requires_human_review':True})
        missing=sum(x['status']!='available' for x in indicators)
        result={'contract_version':1,'institution_id':i,'scope':brief['scope'],
                'quality':{'status':brief['data_quality']['status'],
                    'metric_count':len(indicators),'unavailable_metric_count':missing,
                    'all_indicators_available':missing==0},
                'indicators':indicators,'priorities':priorities,
                'policy':{'decision_support_only':True,'automatic_decision':False,
                          'direct_student_identifiers_exposed':False,
                          'cross_scope_privacy_not_certified':True}}
        if self.audit:self.audit.write(actor_id=actor,action='institutional_intelligence.executive_readout.viewed',
            entity_type='institution',entity_id=i,
            metadata={'scope':brief['scope'],'contract_version':1})
        return result

    def compare_period_briefs(self,actor,i,*,previous_period_id,current_period_id,academic_unit_id=None):
        """Period-over-period institutional signal, never a student-level diff.

        This intentionally refuses overlapping learner populations or tiny
        groups: naïve subtraction of two released aggregates can expose one
        person's result. Same unit and same metric definition are mandatory.
        This is conservative disclosure control, not formal differential privacy.
        """
        if not previous_period_id or not current_period_id or previous_period_id==current_period_id:
            raise ValueError('institutional_intelligence_distinct_periods_required')
        for pid in (previous_period_id,current_period_id):
            self._intelligence_scope(actor,i,academic_period_id=pid,academic_unit_id=academic_unit_id)
        previous_period=self.campus.period(i,previous_period_id)
        current_period=self.campus.period(i,current_period_id)
        if (not previous_period.active or not current_period.active or
            previous_period.kind!=current_period.kind or
            previous_period.ends_on>=current_period.starts_on):
            raise ValueError('institutional_intelligence_incomparable_periods')
        old=self.decision_brief(actor,i,academic_period_id=previous_period_id,
            academic_unit_id=academic_unit_id)
        new=self.decision_brief(actor,i,academic_period_id=current_period_id,
            academic_unit_id=academic_unit_id)
        overlap=self.repo.period_population_overlap(i,previous_period_id,current_period_id,
            academic_unit_id)
        # Counts below 3 are withheld by decision_brief; comparative disclosure
        # is subject to the STRICTER floor of 5, including at either side.
        safe=(isinstance(old['data_quality']['unique_active_students'],int) and
              old['data_quality']['unique_active_students']>=self.MIN_PERIOD_COMPARISON_STUDENTS and
              isinstance(new['data_quality']['unique_active_students'],int) and
              new['data_quality']['unique_active_students']>=self.MIN_PERIOD_COMPARISON_STUDENTS and
              overlap==0)
        out={}
        for key in self.INTELLIGENCE_METRICS:
            a=old['metrics'][key];b=new['metrics'][key]
            comparable=(safe and a['status']=='available' and b['status']=='available' and
                a['definition_version']==b['definition_version'] and
                a['source_contract']==b['source_contract'] and
                a['source_lineage_version']==b['source_lineage_version'] and
                (key not in self.REACH_METRICS or
                 (a['population_reach']['status']=='sufficient_observed_population' and
                  b['population_reach']['status']=='sufficient_observed_population')))
            out[key]={'previous':a['value'] if comparable else None,
                      'current':b['value'] if comparable else None,
                      'delta_percentage_points':round(b['value']-a['value'],2) if comparable else None,
                      'status':'comparable' if comparable else
                         ('privacy_suppressed' if not safe else 'source_unavailable_or_version_mismatch'),
                      'definition_version':a['definition_version'],
                      'source_contract':a['source_contract'],
                      'source_lineage_version':a['source_lineage_version']}
        scope={'academic_unit_id':academic_unit_id,'previous_period_id':previous_period_id,
               'current_period_id':current_period_id}
        if self.audit:self.audit.write(actor_id=actor,
            action='institutional_intelligence.period_comparison.viewed',
            entity_type='institution',entity_id=i,metadata={'scope':scope,'contract_version':1})
        return {'contract_version':1,'institution_id':i,'scope':scope,
            'comparison_policy':{'minimum_distinct_students_per_period':5,
                'requires_disjoint_learner_populations':True,
                'data_release':'eligible' if safe else 'privacy_suppressed',
                'minimum_reach_percent_for_student_observation_comparisons':self.MIN_COMPARABLE_REACH_PERCENT,
                'automatic_decision':False,'student_identity_exposed':False,
                'caveat':'Not causal; disjoint periods and k-threshold do not prove anonymity against repeated overlapping queries.'},
            'metrics':out}

    def export_csv(self,actor,i,*,academic_period_id=None,academic_unit_id=None,cohort_id=None,offering_id=None):
        import csv,io
        # No separate legacy raw-query route: same privacy decision as JSON.
        d=self._legacy_governed(actor,i,academic_period_id=academic_period_id,
                               academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id)
        rows=[('section','metric','value')]
        for section in ('population','teaching','attendance','assignments','results'):
            for key,value in d[section].items():
                rows.append((section,key,'' if value is None else value))
        out=io.StringIO();csv.writer(out).writerows(rows);return out.getvalue()
