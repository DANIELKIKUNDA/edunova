from sqlalchemy.dialects import postgresql

from app.modules.assistant.infrastructure.sqlalchemy_knowledge import SqlAlchemyKnowledgeRepository


def test_postgresql_retrieval_statement_is_course_scoped_ranked_and_bounded():
    statement = SqlAlchemyKnowledgeRepository._postgres_statement(
        course_id="course-1", query="potentiel action sodium", limit=8
    )
    sql = str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})).lower()
    assert "to_tsvector('french'" in sql
    assert "websearch_to_tsquery('french'" in sql
    assert "knowledge_chunks.course_id = 'course-1'" in sql
    assert "order by" in sql and "rank" in sql
    assert "limit 8" in sql
