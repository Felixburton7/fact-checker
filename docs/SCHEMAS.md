# Schemas

## Core objects
- ClaimInput { text, locale?, user_context? }
- ClaimAtom { id, text, type, entities[], timeframe?, numeric_values? }
- EvidenceItem { id, url, domain, tier, title?, published_at?, retrieved_at, quote, context, hash }
- EvidencePack { claim_atom_id, items[] }
- SourceAssessment { evidence_item_id, reliability_score, relevance_score, flags[] }
- JudgeVerdict { judge_id, label, confidence, rationale_bullets[], cited_evidence_ids[], missing_evidence[] }
- FinalVerdict { label, confidence, consensus_rationale[], cited_evidence_ids[], disagreements?, minority_report? }
- FactCheckReport { run_id, input, claims[], overall_summary? }

## Output rule
Any statement in rationale that implies a factual claim must reference cited_evidence_ids.