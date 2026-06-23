"""
AstraOps - Recommendation engine
-----------------------------------
Maps model predictions (impact score, closure probability, clearance ETA)
to concrete operator action cards: manpower count, barricade level,
diversion severity, escalation level -- per blueprint step 5.

Includes rule-based overrides for causes where the data shows an
overwhelmingly strong pattern (vip_movement, public_event, protest,
construction) even when the model hasn't seen many examples of them
(vip_movement = 20 rows total in the source data, too few to fully trust
a learned model alone).
"""

from dataclasses import dataclass, asdict

HIGH_CLOSURE_CAUSES = {"vip_movement", "public_event", "protest", "construction", "tree_fall"}


@dataclass
class ActionCard:
    manpower: int
    barricade_level: str       # none | light | standard | heavy
    diversion_severity: str    # none | local_reroute | corridor_diversion | full_closure_diversion
    escalation_level: str      # field_team | shift_supervisor | traffic_control_room | senior_command
    rationale: list


def _manpower_from_score(impact_score: float, closure_prob: float) -> int:
    base = 2
    base += int(impact_score // 15)          # +1 per 15 impact points
    if closure_prob >= 0.5:
        base += 3
    elif closure_prob >= 0.25:
        base += 1
    return min(base, 12)


def _barricade_level(closure_prob: float, cause: str) -> str:
    if cause in {"vip_movement", "protest"}:
        return "heavy"
    if closure_prob >= 0.5:
        return "heavy"
    if closure_prob >= 0.2:
        return "standard"
    if closure_prob >= 0.05:
        return "light"
    return "none"


def _diversion_severity(closure_prob: float, hotspot_score: float, cause: str) -> str:
    if cause in {"vip_movement", "protest"} or closure_prob >= 0.6:
        return "full_closure_diversion"
    if closure_prob >= 0.3 or hotspot_score >= 70:
        return "corridor_diversion"
    if closure_prob >= 0.1:
        return "local_reroute"
    return "none"


def _escalation_level(impact_score: float, priority: str, cause: str) -> str:
    if cause in {"vip_movement", "protest"} or impact_score >= 70:
        return "senior_command"
    if impact_score >= 45 or priority.lower() == "high":
        return "traffic_control_room"
    if impact_score >= 20:
        return "shift_supervisor"
    return "field_team"


def recommend(
    event_cause: str,
    priority: str,
    impact_score: float,
    closure_probability: float,
    hotspot_score: float,
    eta_hours: float | None,
) -> ActionCard:
    cause = (event_cause or "").lower()
    rationale = []

    # Rule-based override: causes with overwhelming, well-established
    # closure patterns get pinned to a strong response even if the model's
    # learned probability is moderate, because the historical sample size
    # for these causes is small (e.g. vip_movement = 20 rows) and a missed
    # high-impact event (a VIP convoy, a protest) is costlier than an
    # unnecessary extra barricade.
    effective_closure_prob = closure_probability
    if cause in HIGH_CLOSURE_CAUSES:
        effective_closure_prob = max(closure_probability, 0.45)
        rationale.append(
            f"'{cause}' historically has an elevated road-closure rate; "
            f"applying a precautionary floor on closure risk."
        )

    manpower = _manpower_from_score(impact_score, effective_closure_prob)
    barricade = _barricade_level(effective_closure_prob, cause)
    diversion = _diversion_severity(effective_closure_prob, hotspot_score, cause)
    escalation = _escalation_level(impact_score, priority, cause)

    rationale.append(f"Impact score {impact_score:.1f}/100 drives base manpower of {manpower}.")
    rationale.append(f"Closure probability {effective_closure_prob:.0%} sets barricade level '{barricade}'.")
    if hotspot_score >= 70:
        rationale.append(f"Location hotspot score {hotspot_score:.0f}/100 escalates diversion severity.")
    if eta_hours is not None:
        rationale.append(f"Estimated clearance time ~{eta_hours:.1f} hours informs resource hold duration.")

    return ActionCard(
        manpower=manpower,
        barricade_level=barricade,
        diversion_severity=diversion,
        escalation_level=escalation,
        rationale=rationale,
    )


if __name__ == "__main__":
    examples = [
        dict(event_cause="vehicle_breakdown", priority="High", impact_score=35.0,
             closure_probability=0.04, hotspot_score=60.0, eta_hours=0.8),
        dict(event_cause="vip_movement", priority="High", impact_score=55.0,
             closure_probability=0.35, hotspot_score=80.0, eta_hours=2.0),
        dict(event_cause="tree_fall", priority="High", impact_score=61.0,
             closure_probability=0.39, hotspot_score=90.0, eta_hours=3.5),
    ]
    for ex in examples:
        card = recommend(**ex)
        print(ex["event_cause"], "->", asdict(card))
        print()
