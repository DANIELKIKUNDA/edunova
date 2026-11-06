from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path

class CurriculumCatalogService:
    """Read-only, source-faithful curriculum reference catalog.

    Source anomalies are surfaced, never silently repaired. Editorial suggestions are
    carried separately and are not applied to the canonical rows.
    """
    def __init__(self, catalog_path: Path | None = None):
        self.catalog_path = catalog_path or (Path(__file__).resolve().parents[3] / 'data' / 'curricula' / 'medicine_2025_2026.json')
        self._catalog = json.loads(self.catalog_path.read_text(encoding='utf-8'))

    def catalog(self):
        return deepcopy(self._catalog)

    def semesters(self, *, cycle: str | None = None, level: str | None = None):
        rows=self._catalog['semesters']
        if cycle: rows=[x for x in rows if x['cycle'].casefold()==cycle.casefold()]
        if level: rows=[x for x in rows if x['level'].casefold()==level.casefold()]
        return deepcopy(rows)

    def semester(self, number: int):
        return next((deepcopy(x) for x in self._catalog['semesters'] if x['semester']==number),None)

    def find_entries(self, query: str):
        q=query.strip().casefold()
        if not q:return []
        out=[]
        for s in self._catalog['semesters']:
            for e in s['entries']:
                hay=' '.join(str(e.get(k) or '') for k in ('code','title','ue')).casefold()
                if q in hay:out.append({'cycle':s['cycle'],'level':s['level'],'semester':s['semester'],**deepcopy(e)})
        return out

    def audit(self):
        issues=[]; semester_results=[]
        for s in self._catalog['semesters']:
            entries=s['entries']; known=[e for e in entries if e.get('total_hours') is not None]
            hours=sum(e['total_hours'] for e in known); credits=sum(e['credits'] for e in entries if e.get('credits') is not None)
            incomplete=sum(1 for e in entries if e.get('title') is None or e.get('total_hours') is None)
            notes=list(s.get('notes') or [])
            if hours!=s['declared_totals']['hours']:
                issues.append({'semester':s['semester'],'kind':'computed_hours_vs_declared','computed':hours,'declared':s['declared_totals']['hours'],'severity':'source_review'})
            if credits!=s['declared_totals']['credits']:
                issues.append({'semester':s['semester'],'kind':'computed_credits_vs_declared','computed':credits,'declared':s['declared_totals']['credits'],'severity':'source_review'})
            for note in notes:issues.append({'semester':s['semester'],'kind':'source_note','detail':note,'severity':'source_review'})
            for e in entries:
                flags=[k for k,v in e.items() if k.startswith('source_') and v is True]
                for flag in flags:issues.append({'semester':s['semester'],'kind':flag,'code':e.get('code'),'title':e.get('title'),'severity':'source_review'})
            semester_results.append({'semester':s['semester'],'level':s['level'],'entry_count':len(entries),'known_hours_sum':hours,'known_credits_sum':credits,'declared_hours':s['declared_totals']['hours'],'declared_credits':s['declared_totals']['credits'],'incomplete_entries':incomplete})
        return {'catalog_id':self._catalog['catalog_id'],'semester_count':len(self._catalog['semesters']),'entry_count':sum(len(x['entries']) for x in self._catalog['semesters']),'suggestions_applied':False,'semester_results':semester_results,'issues':issues}
