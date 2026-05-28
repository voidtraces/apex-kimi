"""Pure decision functions for the refinement loop and final status.

Keeping these deterministic and testable is what makes the loop provably halt
(Refinement Legitimacy Law) and degradation deterministic. No model judgment,
no prompt knowledge here.
"""
_BLOCKING = {"CRITICAL", "HIGH"}
MAX_PASSES = 2

# Stages every run must record before OUTPUT; L0 legitimately skips GROUNDED.
_REQUIRED_STAGES = ("CLARIFIED", "TRIAGED", "GROUNDED", "DRAFTED", "VERIFIED")


def missing_stages(state: dict, flow: str) -> list[str]:
    """Required stage keys absent from state['stages'] (bookkeeping audit, not stage re-execution)."""
    done = state.get("stages", {})
    return [
        s for s in _REQUIRED_STAGES
        if s not in done and not (s == "GROUNDED" and flow == "L0")
    ]


def _has_blocking(critic: dict) -> bool:
    return any(d.get("severity") in _BLOCKING for d in critic.get("defects", []))


def should_refine(critic: dict, passes: int) -> bool:
    """Refine only on a CRITICAL/HIGH defect and only under the hard pass cap."""
    return _has_blocking(critic) and passes < MAX_PASSES


def final_status(critic: dict, budget_exhausted: bool) -> str:
    """OK only if no blocking defects and budget intact; else UNVERIFIED.

    (Status derives solely from blocking defects + budget; there is no
    ``passes`` parameter — the refinement count is already enforced by
    ``should_refine``'s MAX_PASSES cap, so it carried no signal here.)
    """
    if budget_exhausted:
        return "UNVERIFIED"
    return "UNVERIFIED" if _has_blocking(critic) else "OK"
