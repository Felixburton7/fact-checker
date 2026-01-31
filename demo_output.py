#!/usr/bin/env python3
"""
Demo script to show the debate output format without API calls.

This creates mock data to demonstrate what the actual output will look like.
Run this to preview the terminal formatting before using API credits.

Usage: python demo_output.py
"""

from checker_of_facts.hackathon_models import (
    ClaimTruthPair,
    DebateTurn,
    ModeratorSummary,
    ModeratorFinalVerdict,
)
from checker_of_facts.hackathon_engine import (
    print_header,
    print_claim_truth,
    print_debate_turn,
    print_moderator_summary,
    print_final_verdict,
)


def main():
    # Create mock data
    pair = ClaimTruthPair(
        claim="German had less than 13,200 coronavirus cases with less than 32 deaths as of 19th March 2020 due to the pandemic.",
        truth="As of 19 March 2020, Germany has reported 13,083 cases and 31 deaths, for a case fatality rate of approximately 0.2%.",
        pair_id="demo_001",
    )
    
    # Mock Round 1 turns
    round1_turns = [
        DebateTurn(
            juror_id="pragmatist",
            juror_name="The Common Sense Judge",
            persona="pragmatist",
            round_number=1,
            turn_index=1,
            content="Looking at this from a practical standpoint, the claim captures the essential facts quite well. The external claim says 'less than 13,200 cases' and the actual figure is 13,083 - that's accurate. Similarly, 'less than 32 deaths' encompasses the actual 31 deaths. For an average reader, this would convey the correct magnitude and timeframe. I lean toward 'Faithful' but acknowledge the 'less than' framing deserves scrutiny.",
        ),
        DebateTurn(
            juror_id="skeptic",
            juror_name="The Skeptic",
            persona="skeptic",
            round_number=1,
            turn_index=2,
            content="I must challenge the pragmatist's easy acceptance. The use of 'less than' creates a ceiling that is technically accurate but potentially misleading. Why say 'less than 13,200' instead of 'about 13,000'? The framing implies the numbers might be approaching 13,200 when they're actually 117 below that threshold. More concerning: the external claim omits the case fatality rate of 0.2%, which provides crucial context. Without this, readers can't properly assess the severity.",
        ),
        DebateTurn(
            juror_id="pedant",
            juror_name="The Pedantic Fact-Checker",
            persona="pedant",
            round_number=1,
            turn_index=3,
            content="Let me be precise: the claim states 'German' (grammatically incorrect, should be 'Germany'). The numbers: 'less than 13,200' is true (13,083 < 13,200 ✓), and 'less than 32' is true (31 < 32 ✓). The date '19th March 2020' matches '19 March 2020' ✓. However, the original fact specifically states '13,083 cases and 31 deaths' - exact figures that have been rounded UP to thresholds in the claim. This is a subtle but meaningful mutation in precision.",
        ),
        DebateTurn(
            juror_id="devil_advocate",
            juror_name="The Devil's Advocate",
            persona="devil_advocate",
            round_number=1,
            turn_index=4,
            content="Interesting that everyone is focusing on the numbers. Let me argue the opposite - that this IS a faithful representation. News headlines and tweets regularly use 'less than' or 'over' phrasing for digestibility. The BBC, Reuters, and AP all do this. If we held every summary to exact precision standards, journalism would be impossible. The core message - Germany's case/death count at a specific date - is preserved. I'd argue this is standard summarization, not mutation.",
        ),
        DebateTurn(
            juror_id="context_expert",
            juror_name="The Context Expert",
            persona="context_expert",
            round_number=1,
            turn_index=5,
            content="The missing case fatality rate (0.2%) is significant. In March 2020, this figure was crucial for understanding Germany's pandemic response was working better than Italy's or Spain's. By omitting this context, the claim removes what made this statistic newsworthy. Also, 'due to the pandemic' is redundant - of course coronavirus cases are due to the pandemic. This padding suggests the claim may have been hastily written or transformed from the original source.",
        ),
    ]
    
    # Mock moderator summary
    summary = ModeratorSummary(
        summary="The jury is split on whether the numeric rounding and 'less than' framing constitutes faithful summarization or subtle mutation. Key contention centers on the omission of the 0.2% case fatality rate.",
        key_points=[
            "Numeric bounds ('less than') are technically accurate but use different precision",
            "The 0.2% case fatality rate is omitted from the external claim",
            "Minor grammatical error ('German' vs 'Germany')",
            "Debate over journalism norms vs strict accuracy",
        ],
        areas_of_agreement=[
            "The core facts (case count, death count, date) are directionally correct",
            "The numbers are not exaggerated or false",
        ],
        areas_of_disagreement=[
            "Whether 'less than X' framing is misleading or standard practice",
            "Whether omitting the CFR changes the meaning significantly",
        ],
        guidance_for_next_round="Focus on whether the omitted case fatality rate fundamentally changes the message, and whether the rounding pattern suggests intent to mislead or is standard summarization practice.",
    )
    
    # Mock final verdict
    verdict = ModeratorFinalVerdict(
        label="Faithful",
        confidence=0.72,
        summary="While the external claim uses rounded thresholds and omits the case fatality rate, it accurately conveys Germany's COVID-19 situation as of the specified date. The numeric bounds are technically correct, and the omission of CFR, while notable, does not distort the core message.",
        rationale_bullets=[
            "All stated numbers are technically accurate (13,083 < 13,200, 31 < 32)",
            "Date and location are correctly preserved",
            "Rounding via 'less than' is common in news summaries",
            "Omitted CFR doesn't change the fundamental meaning for most readers",
        ],
        key_arguments_for_faithful=[
            "Technical accuracy of numeric bounds maintained",
            "Standard journalism practice of using round thresholds",
            "Core message (Germany's pandemic numbers at a point in time) preserved",
        ],
        key_arguments_for_mutated=[
            "Case fatality rate (key comparative metric) omitted",
            "Precision of original source reduced to approximate bounds",
            "Minor grammatical error suggests hasty transformation",
        ],
        final_reasoning="The external claim represents a reasonable summary of the internal fact. While the pedant and context expert raise valid concerns about precision and context loss, these fall within acceptable bounds for news summarization. The claim does not exaggerate, invent, or fundamentally misrepresent the source data. The 'less than' framing, while less precise, does not mislead readers about the scale of the pandemic in Germany at that time.",
    )
    
    # Demo the output formatting
    print_header("DEMO: JURY DEBATE OUTPUT FORMAT")
    print_claim_truth(pair)
    
    print_header("ROUND 1 (5 Jurors)")
    print("Speaking order: pragmatist, skeptic, pedant, devil_advocate, context_expert\n")
    for turn in round1_turns:
        print_debate_turn(turn)
    
    print_moderator_summary(summary)
    
    print("\n[ROUND 2 would show 5 more juror turns here...]\n")
    
    print_final_verdict(verdict)
    
    print("\n" + "=" * 60)
    print("This is a DEMO using mock data.")
    print("Run with real API calls to see actual AI-generated debate.")
    print("=" * 60)


if __name__ == "__main__":
    main()
