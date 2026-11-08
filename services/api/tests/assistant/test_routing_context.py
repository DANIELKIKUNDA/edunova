from app.modules.assistant.application.context import build_context, evidence_confidence, unsupported_numeric_claims
from app.modules.assistant.application.routing import choose_model
from app.modules.assistant.domain.model import AssistantRequest, AssistantTask, ModelProfile, SourceChunk


def profiles():
    return (
        ModelProfile('cheap','mini',1,1,8000,frozenset({'chat'})),
        ModelProfile('good','reason',2,2,16000,frozenset({'chat','reasoning','high_reliability'})),
        ModelProfile('expensive','reason-pro',3,5,32000,frozenset({'chat','reasoning','high_reliability'})),
    )


def test_router_prefers_cheapest_compatible_model():
    d=choose_model(AssistantRequest(account_id='a',question='hello'),profiles())
    assert (d.profile.provider,d.credits)==('cheap',1)
    d2=choose_model(AssistantRequest(account_id='a',question='compare',task=AssistantTask.COMPARE),profiles())
    assert (d2.profile.provider,d2.credits)==('good',2)


def test_context_budget_keeps_top_scoring_sources():
    chunks=tuple(SourceChunk(f'c{i}','d','course',None,i+1,i+1,'x'*1200,score=1-(i*.1)) for i in range(5))
    context,selected=build_context(chunks,max_tokens=700)
    assert selected and selected[0].chunk_id == 'c0'
    assert len(context) <= 2800
    assert evidence_confidence(selected) > 0


def test_numeric_guard_flags_only_values_not_present_in_question_or_sources():
    chunks=(SourceChunk('c','d','course',None,1,1,'La dose académique citée dans le cours est 5 mg.',score=.9),)
    assert unsupported_numeric_claims('La valeur est 5 mg.', 'Quelle valeur ?', chunks) == ()
    flags=unsupported_numeric_claims('La valeur serait 500 mg.', 'Quelle valeur ?', chunks)
    assert flags == ('500mg',)
