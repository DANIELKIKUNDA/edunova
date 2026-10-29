from __future__ import annotations
import json,re
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class QualityFinding:
    code:str; blocking:bool; passed:bool; detail:str

def _norm(s:str)->str:
    return re.sub(r'\s+',' ',re.sub(r'[^\wÀ-ÿ]+',' ',s.lower())).strip()

def _tokens(s:str)->set[str]:
    return {x for x in _norm(s).split() if len(x)>3}

def semantic_similarity(a:str,b:str)->float:
    x,y=_tokens(a),_tokens(b)
    return len(x&y)/len(x|y) if x and y else 0.0

def audit_assets(assets,evidence,pages)->tuple[QualityFinding,...]:
    source=' '.join(p['text'] for p in pages)
    source_n=_norm(source)
    ev_by_asset={e.asset_id:e for e in evidence}
    findings=[]
    evidence_ok=True; grounded_ok=True; hash_ok=True
    for a in assets:
        ev=ev_by_asset.get(a.id)
        if not ev: evidence_ok=False; continue
        if _norm(ev.quote) not in source_n: grounded_ok=False
        import hashlib
        if hashlib.sha256(ev.quote.encode()).hexdigest()!=ev.quote_sha256: hash_ok=False
    findings += [
      QualityFinding('evidence_cardinality',True,evidence_ok,'Every asset has exactly one primary evidence link.'),
      QualityFinding('evidence_quote_grounded',True,grounded_ok,'Every evidence quote is present in normalized source text.'),
      QualityFinding('evidence_hash_integrity',True,hash_ok,'Evidence SHA-256 values match their immutable quotes.'),
    ]
    pedagogical=[a for a in assets if a.kind.value not in {'rag_chunk','outline'}]
    dup=False
    for i,a in enumerate(pedagogical):
        for b in pedagogical[i+1:]:
            if a.kind==b.kind and semantic_similarity(a.payload_json,b.payload_json)>=.92: dup=True
    findings.append(QualityFinding('semantic_duplicate_guard',False,not dup,'Near-duplicate pedagogical assets are flagged before review.'))
    unsupported=False
    for a in assets:
        try: payload=json.loads(a.payload_json)
        except Exception: unsupported=True; continue
        text=' '.join(str(payload.get(k,'')) for k in ('answer','back','text','definition_context','explanation') if isinstance(payload.get(k,''),str))
        # Numeric assertions are high-risk: every number emitted must occur in its cited evidence.
        ev=ev_by_asset.get(a.id)
        if ev:
            nums=set(re.findall(r'(?<!\w)\d+(?:[.,]\d+)?',text))
            evnums=set(re.findall(r'(?<!\w)\d+(?:[.,]\d+)?',ev.quote))
            if nums-evnums: unsupported=True
    findings.append(QualityFinding('numeric_claim_grounding',True,not unsupported,'Numbers in generated text must be supported by the cited evidence.'))
    return tuple(findings)
