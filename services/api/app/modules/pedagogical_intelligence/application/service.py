from math import isfinite
from app.modules.pedagogical_intelligence.domain.model import LearningSignal,TeachingInsight,PedagogicalReport

class PedagogicalIntelligenceService:
    """Explainable teaching-support rules. Never diagnoses learners or automates grading."""
    def analyze(self, signals:list[LearningSignal]) -> PedagogicalReport:
        insights=[]
        for s in signals:
            if s.learner_count < 1 or s.assessed_count < 0 or s.assessed_count > s.learner_count or s.failure_count < 0 or s.failure_count > s.assessed_count:
                raise ValueError('pedintel_invalid_counts')
            if s.mean_score is not None and not (isfinite(s.mean_score) and 0 <= s.mean_score <= 100): raise ValueError('pedintel_invalid_score')
            if s.attendance_rate is not None and not (isfinite(s.attendance_rate) and 0 <= s.attendance_rate <= 100): raise ValueError('pedintel_invalid_attendance')
            coverage=s.assessed_count/s.learner_count
            evidence=[f'learners={s.learner_count}',f'assessed={s.assessed_count}',f'coverage={coverage:.2f}']
            if s.assessed_count>=3 and s.mean_score is not None:evidence.append(f'mean_score={s.mean_score:.2f}')
            if s.assessed_count>=3:evidence.append(f'failure_rate={s.failure_count/s.assessed_count:.2f}')
            if s.assessed_count>=3 and s.attendance_rate is not None:evidence.append(f'attendance_rate={s.attendance_rate:.2f}')
            confidence='high' if s.assessed_count>=10 and coverage>=.8 else 'medium' if s.assessed_count>=5 and coverage>=.6 else 'low'
            if s.assessed_count < 3:
                insights.append(TeachingInsight(s.objective_id,'watch','collect_more_evidence','Moins de trois apprenants évalués : données agrégées insuffisantes pour qualifier le groupe.',tuple(evidence),'low'));continue
            if coverage < .5:
                insights.append(TeachingInsight(s.objective_id,'watch','collect_more_evidence','Moins de la moitié du groupe dispose de preuves évaluées; ne pas conclure sur la maîtrise.',tuple(evidence),confidence));continue
            failure_rate=s.failure_count/s.assessed_count if s.assessed_count else 0
            weak=(s.mean_score is not None and s.mean_score<60) or failure_rate>=.4
            if weak:
                insights.append(TeachingInsight(s.objective_id,'high','reteach_and_check','Les preuves agrégées indiquent une difficulté collective; reprendre l’objectif puis effectuer une vérification formative.',tuple(evidence),confidence))
            elif s.attendance_rate is not None and s.attendance_rate<70:
                insights.append(TeachingInsight(s.objective_id,'watch','address_participation','Les acquis disponibles ne suffisent pas à ignorer une faible participation; vérifier l’accès et l’assiduité avant d’adapter le contenu.',tuple(evidence),confidence))
            else:
                insights.append(TeachingInsight(s.objective_id,'normal','continue_and_monitor','Aucun signal collectif fort ne justifie une remédiation générale; poursuivre et surveiller les prochaines preuves.',tuple(evidence),confidence))
        return PedagogicalReport('deterministic_pedagogical_rules_v1',False,len(signals),tuple(insights))


class CanonicalPedagogicalIntelligenceService:
    """Teacher-facing analysis over canonical published results and closed attendance only."""
    def __init__(self, repo, campus, teaching): self.repo=repo;self.campus=campus;self.teaching=teaching;self.rules=PedagogicalIntelligenceService()
    def _staff(self, actor, institution_id, offering_id):
        from app.modules.campus.domain.model import CampusRole,MembershipState
        m=self.campus.membership(institution_id,actor)
        if not m or m.state!=MembershipState.ACTIVE: raise PermissionError('pedintel_active_membership_required')
        if m.role in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}: return
        if m.role == CampusRole.FACULTY_ADMIN:
            # Faculty staff must not open another faculty's pedagogical evidence.
            # Reuse TeachingService's canonical descendant-unit filtering.
            if offering_id not in {off.id for off in self.teaching.my_offerings(actor,institution_id)}:
                raise PermissionError('pedintel_faculty_scope_forbidden')
            return
        a=self.teaching.assignment(offering_id,actor)
        if m.role==CampusRole.TEACHER and a and a.active: return
        raise PermissionError('pedintel_teaching_staff_required')
    def offering_report(self, actor, institution_id, offering_id):
        off=self.teaching.offering(institution_id,offering_id)
        if not off: raise ValueError('pedintel_offering_not_found')
        self._staff(actor,institution_id,offering_id)
        enrolled={e.student_account_id for e in self.campus.enrollments_for_cohort(off.cohort_id) if e.active and e.institution_id==institution_id}
        x=self.repo.offering_signal(institution_id,offering_id,allowed_accounts=enrolled)
        # Course-level results also require a minimum aggregate cell size.
        if x['learner_count']<3 or x['assessed_count']<3:
            x={**x,'mean_score':None,'failure_count':0,'attendance_rate':None,
               'evidence':({'evidence_count':None,'evidence_hash':None},),
               'aggregate_suppressed':True}
        else:
            x={**x,'aggregate_suppressed':False}
        # No objective-level inference: curriculum course is the narrowest canonical scope currently linked to published results.
        if x['learner_count']:
            signal=LearningSignal(x['objective_id'],x['learner_count'],x['assessed_count'],x['mean_score'],x['failure_count'],x['attendance_rate'])
            insight=self.rules.analyze([signal]).insights[0].__dict__
        else:
            insight=TeachingInsight(x['objective_id'],'watch','collect_more_evidence','Aucun étudiant actif inscrit : aucune conclusion pédagogique possible.',('learners=0',),'low').__dict__
        return {'scope':'curriculum_course','offering_id':offering_id,'curriculum_course_id':x['curriculum_course_id'],
                'method':'deterministic_pedagogical_rules_v1','predictive_model':False,'signal':{k:v for k,v in x.items() if k!='evidence'},
                'insight':insight,'evidence':x['evidence'],
                'limitations':('No objective-level claim is made because published grade results are not canonically mapped to learning objectives yet.','Aggregate scores for fewer than three learners are suppressed.',)}

    def objective_report(self, actor, institution_id, offering_id):
        off=self.teaching.offering(institution_id,offering_id)
        if not off: raise ValueError('pedintel_offering_not_found')
        self._staff(actor,institution_id,offering_id)
        enrolled={e.student_account_id for e in self.campus.enrollments_for_cohort(off.cohort_id) if e.active and e.institution_id==institution_id}
        rows=self.repo.objective_signals(institution_id,offering_id,enrolled)
        signals=[]
        for x in rows:
            if x['learner_count']:
                signals.append(LearningSignal(x['objective_id'],x['learner_count'],x['assessed_count'],x['mean_score'],x['failure_count'],None))
        report=self.rules.analyze(signals) if signals else PedagogicalReport('deterministic_pedagogical_rules_v1',False,0,())
        insights={x.objective_id:x.__dict__ for x in report.insights}
        # Large historical cohorts can have high numerical coverage despite a
        # partial legacy question breakdown. Never promote that to high-quality
        # evidence in the staff-facing decision-support narrative.
        for row in rows:
            if (row.get('evidence_integrity') in {'legacy_unverified','mixed_verified_and_legacy'}
                or row.get('mapping_provenance') in {'contains_retrospective_mapping','unknown'}):
                item=insights.get(row['objective_id'])
                if item:
                    insights[row['objective_id']]={**item,'confidence':'low',
                        'reason':item['reason']+' Les détails historiques de la notation et/ou la datation de la cartographie pédagogique ne sont pas pleinement garantis : interprétation prudente requise.'}
        return {'scope':'learning_objective','offering_id':offering_id,'method':report.method,'predictive_model':False,
                'objectives':[{**x,'insight':insights.get(x['objective_id'])} for x in rows],
                'limitations':('Only graded assessment attempts explicitly bound to this offering and questions explicitly mapped to an objective are included.',
                               'Evidence integrity: verified_snapshot_v2 preserves grading-time question points and passing threshold; verified_auto_sum validates the current catalog; legacy_unverified does not establish completeness; mixed results must be interpreted by contract.',
                               'Objective mapping provenance is independent of grade integrity: retrospective mappings cannot prove which learning objective was linked when the assessment was taken.')}

    def register_objective(self, actor,institution_id,offering_id,objective_id,title):
        self._staff(actor,institution_id,offering_id);x=self.repo.offering_signal(institution_id,offering_id)
        if not objective_id.strip() or not title.strip():raise ValueError('pedintel_objective_required')
        self.repo.upsert_objective(institution_id,x['curriculum_course_id'],objective_id.strip(),title.strip())
        return {'objective_id':objective_id.strip(),'title':title.strip(),'curriculum_course_id':x['curriculum_course_id']}
    def map_question(self,actor,institution_id,offering_id,objective_id,question_id):
        self._staff(actor,institution_id,offering_id);x=self.repo.offering_signal(institution_id,offering_id)
        self.repo.map_question(institution_id,x['curriculum_course_id'],objective_id,question_id);return {'mapped':True,'question_id':question_id,'objective_id':objective_id}
    def bind_blueprint(self,actor,institution_id,offering_id,blueprint_id):
        self._staff(actor,institution_id,offering_id);x=self.repo.offering_signal(institution_id,offering_id)
        self.repo.bind_blueprint(institution_id,offering_id,x['curriculum_course_id'],blueprint_id);return {'bound':True,'blueprint_id':blueprint_id,'offering_id':offering_id}
    def gradebook_assessment_reconciliation(self, actor, institution_id, offering_id):
        off=self.teaching.offering(institution_id,offering_id)
        if not off: raise ValueError('pedintel_offering_not_found')
        self._staff(actor,institution_id,offering_id)
        enrolled={e.student_account_id for e in self.campus.enrollments_for_cohort(off.cohort_id)
                  if e.active and e.institution_id==institution_id}
        return self.repo.gradebook_assessment_reconciliation(institution_id,offering_id,enrolled)

    def teaching_dashboard(self, actor, institution_id, offering_id):
        off=self.teaching.offering(institution_id,offering_id)
        if not off: raise ValueError('pedintel_offering_not_found')
        self._staff(actor,institution_id,offering_id)
        objective=self.objective_report(actor,institution_id,offering_id)
        enrolled={e.student_account_id for e in self.campus.enrollments_for_cohort(off.cohort_id) if e.active and e.institution_id==institution_id}
        trends=self.repo.objective_trends(institution_id,offering_id,enrolled)
        # Trends are descriptive. Different blueprints are not asserted to be psychometrically equivalent.
        objectives=[]
        for row in objective['objectives']:
            insight=row.get('insight') or {}
            coverage=(row.get('assessed_count',0)/row.get('learner_count',1)) if row.get('learner_count') else 0.0
            objectives.append({**row,'coverage':coverage,'priority':'unassessed' if row.get('assessed_count',0)==0 else insight.get('level','unassessed')})
        priority_order={'high':0,'watch':1,'normal':2,'unassessed':3}
        objectives=tuple(sorted(objectives,key=lambda x:(priority_order.get(x['priority'],9),x.get('objective_id',''))))
        high=sum(x['priority']=='high' for x in objectives); watch=sum(x['priority']=='watch' for x in objectives)
        unassessed=sum(x.get('assessed_count',0)==0 for x in objectives)
        return {'scope':'teacher_dashboard','offering_id':offering_id,'predictive_model':False,
                'method':'deterministic_pedagogical_rules_v1','summary':{'objective_count':len(objectives),'high_priority_count':high,'watch_count':watch,'unassessed_count':unassessed,'recurrent_error_count':len(trends['recurrent_errors'])},
                'objectives':objectives,'assessment_timeline':trends['timeline'],'recurrent_errors':trends['recurrent_errors'],
                'priority_actions':tuple({'objective_id':x['objective_id'],'objective_title':x.get('objective_title'),'severity':x['priority'],'action':(x.get('insight') or {}).get('action'),'reason':(x.get('insight') or {}).get('reason'),'confidence':(x.get('insight') or {}).get('confidence')} for x in objectives if x.get('insight') and x['priority'] in {'high','watch','unassessed'}),
                'guardrails':('Group-level evidence only; no learner diagnosis or automated grade/jury action.',
                              'Assessment periods are descriptive and are not assumed psychometrically equivalent.',
                              'A recurrent incorrect response is a teaching signal, not proof of a misconception cause.',
                              'Priority ordering is deterministic decision support; the teacher remains the final decision-maker.',
                              'Legacy question-level results have not been certified as complete; evidence_integrity identifies their limits.',
                              'Objective mapping provenance distinguishes contemporaneous from retrospective associations; mapping metadata is not a signed assessment-time snapshot.',
                              'Staff-editable gradebook candidate references can be score-corroborated but not authenticated as official grade provenance.')}

