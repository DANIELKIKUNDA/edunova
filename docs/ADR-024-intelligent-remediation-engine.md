# ADR-024 — Intelligent Remediation Engine
Status: accepted — v0.20.0

EduNova separates diagnosis from remediation and mastery. A low score is evidence, not a diagnosis by itself. LOT 19 aggregates learning progress and Error Bank evidence into versioned misconceptions with severity and confidence. A remediation path is deterministic and explainable: diagnose → targeted sourced explanation → worked example → guided practice → transfer → independent reassessment. Explanation-only completion is forbidden as proof of mastery. High-stakes content remains source-bound and human-governed. LLMs may draft explanations/items later but cannot independently mark a misconception resolved.

Resolution requires new evidence. Optimistic locking protects concurrent/offline mutations. Successful remediation returns to spaced review; unsuccessful verification returns to targeted practice. LOT 16 and LOT 17 remain consumers of learning evidence rather than being replaced by LOT 19.
