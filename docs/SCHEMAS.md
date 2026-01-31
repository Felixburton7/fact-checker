# Schemas

## Core objects
- ClaimInput { text, locale?, user_context? }
- ClaimAtom { id, text, type, entities[], timeframe?, numeric_values? }
- JurorReaction { target_juror_id, target_turn_index, reaction }
- JurorTurn { juror_id, persona, turn_index, content, reactions[] }
- ModeratorVerdict { label, confidence, rationale_bullets[], minority_report? }
- JudgeVerdict { judge_id, label, confidence, rationale_bullets[], cited_evidence_ids[], missing_evidence[] }
- FinalVerdict { label, confidence, consensus_rationale[], cited_evidence_ids[], disagreements?, minority_report? }
- FactCheckReport { run_id, input, claims[], overall_summary? }

## Output rule
Debate turns and moderator rationale are based on internal model knowledge and do not include citations.
