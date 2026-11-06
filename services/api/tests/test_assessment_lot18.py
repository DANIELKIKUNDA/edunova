from datetime import UTC,datetime
from app.modules.assessment.application.service import AssessmentService
from app.modules.assessment.domain.model import *
N=datetime(2026,9,24,10,tzinfo=UTC)
class R:
 def __init__(self):self.q={};self.b={};self.a={};self.r={}
 def save_question(self,x):self.q[x.id]=x
 def question(self,id):return self.q.get(id)
 def questions_for_course(self,c):return tuple(x for x in self.q.values() if x.course_id==c)
 def save_blueprint(self,x):self.b[x.id]=x
 def blueprint(self,id):return self.b.get(id)
 def save_attempt(self,x):self.a[x.id]=x
 def attempt(self,id):return self.a.get(id)
 def save_result(self,x):self.r[x.attempt_id]=x
def build():
 r=R();s=AssessmentService(r,lambda:N)
 q1=s.create_question('bank','anat','osteo',QuestionType.SINGLE,'Os du bras ?',('Humérus','Fémur'),('Humérus',),'Humérus.',(12,),'source page 12',True,2,1)
 q2=s.create_question('bank','anat','osteo',QuestionType.TRUE_FALSE,'Le fémur est au membre inférieur.',('Vrai','Faux'),('Vrai',),'Exact.',(13,),'source page 13',True,1,1)
 b=s.create_blueprint('Blanc anatomie','anat',30,2,60);return s,r,q1,q2,b
def test_exam_lifecycle_and_grading():
 s,r,q1,q2,b=build();a=s.start('u',b.id);a=s.answer('u',a.id,q1.id,['Humérus'],False,1);a=s.answer('u',a.id,q2.id,['Faux'],True,2);res=s.submit('u',a.id,3);assert res.percent==67 and res.passed and len(res.questions)==2
def test_question_requires_ground_truth():
 s=AssessmentService(R(),lambda:N)
 try:s.create_question('b','c',None,QuestionType.SINGLE,'Q',('A','B'),(),'',(), 'x');assert False
 except ValueError:pass
def test_only_approved_questions_enter_exam():
 s,r,q1,q2,b=build();s.create_question('bank','anat',None,QuestionType.SINGLE,'Draft',('A','B'),('A',),'',(1,),'draft',False)
 a=s.start('u',b.id);assert len(a.question_ids)==2
def test_optimistic_answer_conflict():
 s,r,q1,q2,b=build();a=s.start('u',b.id);s.answer('u',a.id,q1.id,['Humérus'],False,1)
 try:s.answer('u',a.id,q2.id,['Vrai'],False,1);assert False
 except ValueError as e:assert 'conflict' in str(e)
def test_provenance_is_sha256():
 s,r,q1,q2,b=build();assert len(q1.provenance_sha256)==64 and q1.source_pages==(12,)
def test_bloom_quality_report_rewards_real_reasoning():
 s=AssessmentService(R(),lambda:N)
 r=s.evaluate_question_quality(QuestionType.SINGLE,'Un patient de 67 ans présente une douleur thoracique à effort avec irradiation au bras gauche. À partir des mécanismes physiopathologiques décrits, quelle hypothèse explique le mieux la relation entre demande myocardique et perfusion coronaire ?',('Augmentation isolée du retour veineux','Déséquilibre apport-besoins en oxygène du myocarde','Diminution physiologique de la fréquence cardiaque','Hyperventilation sans conséquence hémodynamique'),('Déséquilibre apport-besoins en oxygène du myocarde',),'La situation impose de relier les symptômes à une inadéquation entre consommation myocardique en oxygène et capacité de perfusion coronaire, plutôt que de rappeler un fait isolé.',(42,43),BloomLevel.ANALYZE,'Analyser un tableau clinique pour relier symptômes et mécanisme physiopathologique',('Identifier les données discriminantes','Relier les données au mécanisme','Éliminer les distracteurs incompatibles'),('Ne rend pas compte de l’ischémie','Réponse correcte','Contredit le contexte d’effort','N’explique pas le mécanisme'),True)
 assert r.score>=90 and r.higher_order and not r.blocking_issues

def test_bloom_blueprint_enforces_cognitive_mix_and_quality():
 s,r,_,_,_=build()
 for i,level in enumerate((BloomLevel.APPLY,BloomLevel.ANALYZE,BloomLevel.EVALUATE,BloomLevel.CREATE)):
  s.create_question('advanced','anat','osteo',QuestionType.EXERCISE if level==BloomLevel.CREATE else QuestionType.SINGLE,f'Cas clinique complexe numéro {i}: un étudiant doit mobiliser plusieurs éléments du cours afin de résoudre une situation nouvelle et justifier le choix le plus cohérent parmi les propositions suivantes.',('Option plausible A','Option correcte fondée sur le mécanisme','Option plausible C'),('Option correcte fondée sur le mécanisme',),'La correction explicite le raisonnement attendu, les indices discriminants et la raison pour laquelle les autres propositions ne satisfont pas les données du problème.',(20+i,),'source académique suffisamment détaillée',True,2,4,level,f'Résoudre une situation au niveau {level.value}',('Analyser les données','Choisir le principe pertinent','Conclure'),('Distracteur A','Correct','Distracteur C'),True)
 b=s.create_blueprint('Examen cognitif','anat',60,4,60,True,{x.value:25 for x in (BloomLevel.APPLY,BloomLevel.ANALYZE,BloomLevel.EVALUATE,BloomLevel.CREATE)},70)
 a=s.start('student',b.id);levels={r.question(q).bloom_level for q in a.question_ids}
 assert levels=={BloomLevel.APPLY,BloomLevel.ANALYZE,BloomLevel.EVALUATE,BloomLevel.CREATE}

def test_low_quality_question_excluded_by_industrial_gate():
 s,r,_,_,_=build();b=s.create_blueprint('Gate','anat',20,1,60,True,None,80)
 try:s.start('u2',b.id);assert False
 except ValueError as e:assert 'insufficient' in str(e)
