"""Phase 17 central governance: aggregated privacy-preserving read models."""
from datetime import UTC, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.audit import SqlAuditSink
from app.modules.platform_governance.infrastructure.institution_registry import InstitutionControlRepository
from app.modules.campus.infrastructure.sqlalchemy_repo import InstitutionRow


def test_central_statistics_do_not_include_student_data():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    with sf() as s:
        for i, state in enumerate(('active', 'active', 'suspended', 'archived')):
            s.add(InstitutionRow(id=f'i{i}', slug=f'campus{i}', name=f'Campus {i}', legal_name='',
                country_code='CD', city='Lubumbashi', state=state, row_version=1,
                created_by='owner', created_at=datetime.now(UTC), updated_at=datetime.now(UTC)))
        s.commit()
    assert InstitutionControlRepository(sf).statistics() == {
        'total': 4, 'active': 2, 'suspended': 1, 'archived': 1}
    engine.dispose()


def test_platform_audit_filters_other_domains_and_private_metadata():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    audit = SqlAuditSink(sessionmaker(bind=engine))
    audit.write(actor_id='operator', action='platform.institution.state_changed',
        entity_type='campus_institution', entity_id='uni-1', metadata={'secret': 'private'})
    audit.write(actor_id='student', action='student.payment.created',
        entity_type='student_payment', entity_id='payment-1', metadata={'secret': 'private'})
    result = audit.list_platform_events(limit=10, offset=0)
    assert result['total'] == 1
    assert result['items'][0]['entity_id'] == 'uni-1'
    assert 'metadata' not in result['items'][0]
    assert 'private' not in str(result)
    assert audit.list_platform_events(limit=10, offset=1)['items'] == []
    engine.dispose()
