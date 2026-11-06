# LOT 18 v0.19.2 — Cognitive Assessment Intelligence

## Purpose
EduNova must test university-level reasoning, not reward superficial recall. The assessment engine therefore treats a question as an engineered learning instrument with an explicit learning objective, cognitive level, source evidence, reasoning path and quality gate.

## Revised Bloom taxonomy contract
- **Remember**: retrieve a fact only when factual recall is itself educationally justified.
- **Understand**: explain, classify, compare or interpret.
- **Apply**: use a rule/mechanism in a new but bounded situation.
- **Analyze**: discriminate relevant evidence, connect mechanisms, identify relationships or diagnose a structured case.
- **Evaluate**: judge alternatives against explicit criteria/evidence and justify the best conclusion.
- **Create**: construct a plan, synthesis, solution or argument. EduNova rejects MCQ as a sufficient CREATE-level format; constructed response/exercise is required.

Industrial exam blueprints can impose an exact Bloom distribution. This prevents a 50-question exam from degenerating into 50 recall items simply because those are easiest to generate.

## Question quality gate (0–100)
The deterministic gate checks stem substance, explicit learning objective, source pages, substantive correction, higher-order reasoning steps, authentic case context, option uniqueness, distractor rationale coverage and common cueing problems. A blueprint can require a minimum score; low-quality questions remain drafts but cannot enter that industrial exam.

For higher-order questions, EduNova expects context + discriminating evidence + reasoning. In medical/high-stakes contexts, clinical vignettes are first-class metadata, but a long vignette alone never proves cognitive quality.

## Distractors
Distractors should represent plausible misconceptions or reasoning errors. They are not random false statements. Authoring metadata can preserve a rationale for every option so reviewers can verify why a distractor is educationally useful and not merely tricky.

## Feedback
The correction explains the reasoning, not only the answer. Results expose performance by Bloom level in addition to chapter, allowing EduNova to distinguish e.g. “knows facts” from “struggles to apply/analyze”. These are learning indicators, not a diagnosis or guaranteed prediction of academic performance.

## AI-generation policy
An LLM/provider may propose items, but provider output is never trusted as an approved question. Proposed items must pass deterministic structural/quality gates, source grounding and the existing human editorial approval path. Medical/high-stakes questions remain approval-gated. Provider/model/prompt provenance should be retained by the Content Factory/Studio layer when generation is enabled.

## Anti-primary-school rule
Default production blueprints should emphasize Apply/Analyze/Evaluate, with Remember used deliberately rather than as the dominant fallback. CREATE uses constructed response. Difficulty and Bloom level are independent: an obscure recall fact is not “higher order” merely because it is difficult.
