from datetime import UTC,datetime
from app.modules.assessment.application.service import AssessmentService
from app.modules.assessment.domain.model import *
class R:
 def __init__(self):self.q={};self.o={}
 def save_question(self,x):self.q[x.id]=x
 def question(self,id):return self.q.get(id)
 def delete_question(self,id):self.q.pop(id,None)
 def save_origin(self,x):self.o[x.duplicate_fingerprint]=x
 def origin_by_fingerprint(self,fp):return self.o.get(fp)
def S():return AssessmentService(R(),lambda:datetime(2026,9,24,tzinfo=UTC))
def test_gift_import_preserves_original_and_deduplicates():
 s=S();txt='::Q1::Analyser les données du cas clinique et déterminer le mécanisme le plus probable. {=Mécanisme A ~Mécanisme B ~Mécanisme C}';a=s.import_gift('b','c','paper-2025',txt);b=s.import_gift('b','c','paper-2026',txt);assert a.imported==1 and b.duplicates==1 and len(s.repo.q)==1;origin=next(iter(s.repo.o.values()));assert origin.inferred_bloom==BloomLevel.ANALYZE and len(origin.import_sha256)==64
def test_moodle_xml_import_and_export_roundtrip_contract():
 s=S();xml='<quiz><question type="multichoice"><name><text>Cardio 1</text></name><questiontext><text>Comparer les mécanismes et identifier la conséquence physiologique la plus cohérente.</text></questiontext><answer fraction="100"><text>Réponse A</text></answer><answer fraction="0"><text>Réponse B</text></answer><answer fraction="0"><text>Réponse C</text></answer></question></quiz>';r=s.import_moodle_xml('b','cardio','doc',xml);assert r.imported==1;qid=r.question_ids[0];out=s.export_moodle_xml([qid]);assert '<quiz>' in out and 'Réponse A' in out
def test_variant_contract_preserves_objective_and_forbids_verbatim_copy():
 s=S();q=s.create_question('b','c',None,QuestionType.SINGLE,'Analyser une situation clinique suffisamment détaillée afin de sélectionner le mécanisme physiologique le plus cohérent parmi plusieurs hypothèses plausibles.',('A','B','C'),('A',),'Explication suffisamment développée pour justifier le mécanisme et éliminer les autres options.',(1,),'source',False,1,4,BloomLevel.ANALYZE,'Analyser un mécanisme',('Identifier','Relier'),('ok','x','y'),True);spec=s.variant_specification(q.id,BloomLevel.EVALUATE,5);assert spec.target_bloom=='evaluate' and 'verbatim_copy' in spec.forbidden and spec.preserve_learning_objective=='Analyser un mécanisme'
def test_bloom_inference_prefers_higher_order_verbs():
 s=S();assert s.infer_bloom('Évaluer et justifier la meilleure stratégie thérapeutique')[0]==BloomLevel.EVALUATE;assert s.infer_bloom('Définir le terme anatomique')[0]==BloomLevel.REMEMBER
