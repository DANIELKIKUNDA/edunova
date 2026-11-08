import asyncio

from app.modules.document_engine.domain.model import DocumentChunk
from app.modules.pedagogy.application.generation import PedagogyGenerator
from app.modules.pedagogy.application.ports import GenerationResponse
from app.modules.pedagogy.domain.model import ContentStatus, SummaryKind


class StubAi:
    def __init__(self, payload):
        self.payload = payload
        self.last_request = None

    async def generate(self, request):
        self.last_request = request
        return GenerationResponse(payload=self.payload, provider='stub', model_id='quality-test')


def _chunks():
    return [
        DocumentChunk(
            id='chunk-1',
            section_id='section-1',
            start_page=10,
            end_page=11,
            text='La membrane possède un potentiel de repos. Le sodium participe à la dépolarisation.',
            ordinal=1,
            token_estimate=40,
        )
    ]


def test_summary_generation_is_source_bound_and_medical_reviewed():
    ai = StubAi({
        'title': 'Potentiel membranaire',
        'body_markdown': 'Le potentiel membranaire dépend des gradients ioniques et de la perméabilité sélective.' * 3,
        'estimated_minutes': 4,
        'factual_claim_count': 1,
        'cited_claim_count': 1,
        'source_indexes': [0],
    })
    summary = asyncio.run(PedagogyGenerator(ai).generate_summary(
        document_id='doc-1',
        course_id='physio',
        section_id='section-1',
        title='Potentiel membranaire',
        kind=SummaryKind.EXPRESS,
        chunks=_chunks(),
        is_medical=True,
    ))
    assert summary.meta.source_refs[0].start_page == 10
    assert summary.meta.status == ContentStatus.REVIEW_REQUIRED
    assert ai.last_request.source_refs[0].chunk_id == 'chunk-1'


def test_flashcard_generation_validates_and_preserves_sources():
    ai = StubAi({'cards': [
        {'front': 'Ion principal de la dépolarisation ?', 'back': 'Na+', 'difficulty': 2, 'source_indexes': [0]},
        {'front': 'Que décrit le potentiel de repos ?', 'back': 'La différence de potentiel transmembranaire au repos.', 'difficulty': 3, 'source_indexes': [0]},
        {'front': 'Quel concept dépend de gradients ioniques ?', 'back': 'Le potentiel membranaire.', 'difficulty': 2, 'source_indexes': [0]},
    ]})
    cards = asyncio.run(PedagogyGenerator(ai).generate_flashcards(
        document_id='doc-1', course_id='physio', section_id='section-1', chunks=_chunks(), count=3,
    ))
    assert len(cards) == 3
    assert all(card.meta.source_refs for card in cards)


def test_quiz_generation_requires_four_options_and_one_answer():
    ai = StubAi({'questions': [
        {
            'prompt': 'Quel ion domine la dépolarisation ?',
            'options': ['Na+', 'K+', 'Cl-', 'Ca2+'],
            'correct_index': 0,
            'explanation': 'Le sodium est associé à la phase ascendante dans le passage source.',
            'difficulty': 2,
            'source_indexes': [0],
        },
        {
            'prompt': 'Le potentiel de repos concerne quoi ?',
            'options': ['Membrane', 'ADN', 'Os', 'Peau'],
            'correct_index': 0,
            'explanation': 'Le passage porte sur le potentiel transmembranaire.',
            'difficulty': 2,
            'source_indexes': [0],
        },
        {
            'prompt': 'La dépolarisation modifie quoi ?',
            'options': ['Potentiel membranaire', 'Masse atomique', 'pH sanguin toujours', 'Taille du noyau'],
            'correct_index': 0,
            'explanation': 'La dépolarisation est une variation du potentiel membranaire.',
            'difficulty': 3,
            'source_indexes': [0],
        },
    ]})
    questions = asyncio.run(PedagogyGenerator(ai).generate_quiz(
        document_id='doc-1', course_id='physio', section_id='section-1', chunks=_chunks(), count=3,
    ))
    assert len(questions) == 3
    assert questions[0].correct_option_ids == ('A',)
    assert questions[0].meta.source_refs[0].start_page == 10


def test_mixed_quiz_generation_supports_numeric_and_free_text():
    ai = StubAi({'questions': [
        {
            'kind': 'numeric', 'prompt': 'Quelle valeur est donnée dans cet exercice numérique ?',
            'options': [], 'correct_indexes': [], 'expected_numeric': 9.81, 'numeric_tolerance': 0.02,
            'relative_tolerance': 0, 'expected_text': None, 'accepted_text_answers': [],
            'explanation': 'La valeur attendue est explicitement indiquée dans la source.',
            'difficulty': 2, 'source_indexes': [0], 'tags': ['calcul'],
        },
        {
            'kind': 'free_text', 'prompt': 'Quel ion est associé à la dépolarisation dans le passage ?',
            'options': [], 'correct_indexes': [], 'expected_numeric': None, 'numeric_tolerance': 0,
            'relative_tolerance': 0, 'expected_text': 'sodium', 'accepted_text_answers': ['Na+'],
            'explanation': 'Le passage cite le sodium pour la dépolarisation.',
            'difficulty': 2, 'source_indexes': [0], 'tags': ['membrane'],
        },
        {
            'kind': 'true_false', 'prompt': 'Le passage associe le sodium à la dépolarisation.',
            'options': ['Vrai', 'Faux'], 'correct_indexes': [0], 'expected_numeric': None,
            'numeric_tolerance': 0, 'relative_tolerance': 0, 'expected_text': None,
            'accepted_text_answers': [], 'explanation': 'Le passage le dit explicitement.',
            'difficulty': 1, 'source_indexes': [0], 'tags': ['membrane'],
        },
    ]})
    questions = asyncio.run(PedagogyGenerator(ai).generate_mixed_quiz(
        document_id='doc-1', course_id='physio', section_id='section-1', chunks=_chunks(), count=3,
    ))
    assert [q.kind.value for q in questions] == ['numeric', 'free_text', 'true_false']
    assert questions[0].numeric_tolerance == 0.02
    assert 'Na+' in questions[1].accepted_text_answers


def test_generation_identity_is_stable_for_same_source_and_prompt():
    ai = StubAi({
        'title':'Stable','body_markdown':'Un contenu suffisamment long pour satisfaire la validation. ' * 4,
        'estimated_minutes':3,'factual_claim_count':1,'cited_claim_count':1,'source_indexes':[0],
    })
    generator = PedagogyGenerator(ai)
    first = asyncio.run(generator.generate_summary(document_id='doc-1', course_id='c', section_id='s', title='T', kind=SummaryKind.EXPRESS, chunks=_chunks()))
    second = asyncio.run(generator.generate_summary(document_id='doc-1', course_id='c', section_id='s', title='T', kind=SummaryKind.EXPRESS, chunks=_chunks()))
    assert first.meta.source_fingerprint == second.meta.source_fingerprint
    assert first.meta.generation_key == second.meta.generation_key
    assert first.meta.generation_key
