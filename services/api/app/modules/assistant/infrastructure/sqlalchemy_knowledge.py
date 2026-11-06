from __future__ import annotations

from sqlalchemy import Integer, String, Text, func, literal_column, select
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.assistant.domain.model import SourceChunk
from app.modules.document_engine.application.search import search_chunks
from app.modules.document_engine.domain.model import DocumentChunk
from app.shared.infrastructure.database import Base


class KnowledgeChunkRow(Base):
    __tablename__ = "knowledge_chunks"
    chunk_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(128), index=True)
    course_id: Mapped[str] = mapped_column(String(128), index=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_page: Mapped[int] = mapped_column(Integer)
    end_page: Mapped[int] = mapped_column(Integer)
    text_content: Mapped[str] = mapped_column(Text)
    source_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)


class SqlAlchemyKnowledgeRepository:
    """Persistent shared-course knowledge index.

    PostgreSQL uses server-side French full-text ranking with a GIN expression
    index. SQLite/test environments retain the deterministic TF/IDF fallback.
    The repository port remains compatible with a future hybrid pgvector
    retriever without changing the assistant domain or application service.
    """

    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def index_chunks(self, chunks: tuple[SourceChunk, ...]) -> None:
        with self.session_factory() as session:
            for c in chunks:
                if not c.course_id:
                    raise ValueError("shared_knowledge_requires_course_id")
                session.merge(
                    KnowledgeChunkRow(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        course_id=c.course_id,
                        section_title=c.section_title,
                        start_page=c.start_page,
                        end_page=c.end_page,
                        text_content=c.text,
                        source_fingerprint=c.source_fingerprint,
                    )
                )
            session.commit()

    def search(self, *, course_id: str, query: str, limit: int = 8) -> tuple[SourceChunk, ...]:
        query = " ".join(query.split()).strip()
        if not query or limit <= 0:
            return ()
        with self.session_factory() as session:
            dialect = session.get_bind().dialect.name
            if dialect == "postgresql":
                return self._search_postgresql(session, course_id=course_id, query=query, limit=limit)
            rows = session.scalars(
                select(KnowledgeChunkRow)
                .where(KnowledgeChunkRow.course_id == course_id)
                .limit(1500)
            ).all()
        return self._rank_fallback(rows, query=query, limit=limit)

    @staticmethod
    def _postgres_statement(*, course_id: str, query: str, limit: int):
        config = literal_column("'french'")
        searchable = func.coalesce(KnowledgeChunkRow.section_title, "") + " " + KnowledgeChunkRow.text_content
        vector = func.to_tsvector(config, searchable)
        tsquery = func.websearch_to_tsquery(config, query)
        rank = func.ts_rank_cd(vector, tsquery).label("rank")
        return (
            select(KnowledgeChunkRow, rank)
            .where(KnowledgeChunkRow.course_id == course_id)
            .where(vector.op("@@")(tsquery))
            .order_by(rank.desc(), KnowledgeChunkRow.chunk_id.asc())
            .limit(max(1, min(limit, 32)))
        )

    def _search_postgresql(self, session, *, course_id: str, query: str, limit: int) -> tuple[SourceChunk, ...]:
        result = session.execute(self._postgres_statement(course_id=course_id, query=query, limit=limit)).all()
        if not result:
            return ()
        raw_max = max(float(rank or 0.0) for _, rank in result) or 1.0
        return tuple(
            SourceChunk(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                course_id=row.course_id,
                section_title=row.section_title,
                start_page=row.start_page,
                end_page=row.end_page,
                text=row.text_content,
                score=min(1.0, max(0.01, float(rank or 0.0) / raw_max)),
                source_fingerprint=row.source_fingerprint,
            )
            for row, rank in result
        )

    @staticmethod
    def _rank_fallback(rows, *, query: str, limit: int) -> tuple[SourceChunk, ...]:
        if not rows:
            return ()
        doc_chunks = tuple(
            DocumentChunk(
                id=r.chunk_id,
                section_id=None,
                start_page=r.start_page,
                end_page=r.end_page,
                text=r.text_content,
                ordinal=i,
                token_estimate=max(1, len(r.text_content) // 4),
            )
            for i, r in enumerate(rows)
        )
        hits = search_chunks(doc_chunks, query, limit=limit)
        if not hits:
            return ()
        by_id = {r.chunk_id: r for r in rows}
        raw_max = max(h.score for h in hits) or 1.0
        out = []
        for h in hits:
            r = by_id[h.chunk_id]
            out.append(
                SourceChunk(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    course_id=r.course_id,
                    section_title=r.section_title,
                    start_page=r.start_page,
                    end_page=r.end_page,
                    text=r.text_content,
                    score=min(1.0, max(0.01, h.score / raw_max)),
                    source_fingerprint=r.source_fingerprint,
                )
            )
        return tuple(out)
