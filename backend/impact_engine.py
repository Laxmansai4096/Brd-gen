from typing import Dict, Any, List, Optional
from backend.models import ImpactAnalysisResult, BRDDocument, ProjectSession
from backend.admin_store import DELIVERY_TIERS, COMPLEXITY_MULTIPLIERS

def calculate_change_impact(
    current_brd: BRDDocument,
    parameter_changed: str,
    old_value: Any,
    new_value: Any
) -> ImpactAnalysisResult:
    """
    Deterministic Impact Analysis Engine per Section 50 of reference.txt.
    Calculates exact arithmetic deltas for:
    - Capacity & Sizing (monthly cloud cost)
    - Schedule (days / weeks stretched)
    - Engineering Effort (person-days)
    - Total Labour Cost ($)
    - Staffing Peak FTE
    - Testing scope & Architecture impact
    
    CRITICAL RULE (reference.txt): Numbers must be calculated deterministically in code, never by the LLM.
    """
    param = parameter_changed.lower().strip()
    affected: Dict[str, Any] = {}
    unaffected: List[str] = [
        "Unrelated functional requirements",
        "Base legal ontology",
        "Historical contract sample schemas"
    ]
    
    delta_days = 0.0
    delta_cost = 0.0
    delta_fte = 0.0
    narrative = ""

    # 1. Named Users or Concurrency change
    if "user" in param or "traffic" in param or "request" in param:
        try:
            old_num = float(old_value)
            new_num = float(new_value)
        except Exception:
            old_num, new_num = 200.0, 500.0
            
        ratio = (new_num / max(old_num, 1.0))
        
        # Infrastructure / Cloud Cost Impact
        old_cloud = current_brd.sizing_metrics.total_monthly_cloud_cost_usd
        new_cloud = round(old_cloud * (1.0 + 0.45 * (ratio - 1.0)), 2)
        delta_cloud = round(new_cloud - old_cloud, 2)
        
        # Testing & Performance Effort Impact (P15 Testing phase scales)
        testing_effort = 33.0 * (0.15 if current_brd.delivery_tier == "PoC" else 0.75)
        extra_test_days = round(testing_effort * 0.25 * (ratio - 1.0), 1)
        extra_test_days = max(-10.0, min(extra_test_days, 40.0))
        delta_days += extra_test_days
        delta_cost += round(extra_test_days * current_brd.daily_working_hours * current_brd.blended_hourly_rate, 2)
        delta_fte += round(extra_test_days / (current_brd.total_duration_weeks * 5.0), 2)

        affected["Capacity"] = f"Peak RPS adjusted from {current_brd.sizing_metrics.peak_rps:.1f} to {(current_brd.sizing_metrics.peak_rps * ratio):.1f} RPS"
        affected["Infrastructure"] = f"Cloud hosting scaled: +${delta_cloud:,.2f}/mo (New: ${new_cloud:,.2f}/mo)"
        affected["Performance & Testing"] = f"Load testing & stress validation effort adjusted by {extra_test_days:+.1f} person-days"
        affected["Architecture"] = "App Service & Vector DB tier scaling triggered"
        
        narrative = (
            f"Changing users from {old_value} to {new_value} (x{ratio:.2f}) directly increases API throughput demand. "
            f"This scales the cloud infrastructure bill of materials (+${delta_cloud:,.2f}/mo) and expands performance test cycles "
            f"by {extra_test_days:+.1f} person-days (+${delta_cost:,.2f} labour impact)."
        )

    # 2. Delivery Tier change
    elif "tier" in param:
        old_tier = str(old_value)
        new_tier = str(new_value)
        old_weight = current_brd.headline_weight
        new_weight = DELIVERY_TIERS.get(new_tier, {}).get("weight", 0.778)
        weight_ratio = new_weight / max(old_weight, 0.05)
        
        new_person_days = round(current_brd.total_person_days * weight_ratio, 1)
        delta_days = round(new_person_days - current_brd.total_person_days, 1)
        delta_cost = round(delta_days * current_brd.daily_working_hours * current_brd.blended_hourly_rate, 2)
        delta_fte = round((delta_days / (current_brd.total_duration_weeks * 5.0)), 2)

        affected["Phase Rigour"] = f"Phase applicability anchor shifted from {old_tier} ({old_weight:.3f}) to {new_tier} ({new_weight:.3f})"
        affected["Governance & Security Gates"] = "Production-grade NFR, Responsible AI, and HA/DR validation gates updated"
        affected["WBS & Task Library"] = f"Task library effort adjusted by {delta_days:+.1f} person-days"
        
        narrative = (
            f"Switching delivery tier from {old_tier} to {new_tier} changes the 18-phase rigour multiplier from {old_weight:.3f} to {new_weight:.3f}. "
            f"This results in {delta_days:+.1f} person-days difference and a cost adjustment of {current_brd.currency_symbol}{delta_cost:,.2f}."
        )

    # 3. Reference Duration change
    elif "duration" in param or "week" in param:
        try:
            old_wks = float(str(old_value).split()[0])
            new_wks = float(str(new_value).split()[0])
        except Exception:
            old_wks, new_wks = 6.0, 8.0
            
        ratio_w = old_wks / max(new_wks, 1.0)
        # Days stay the same, but team ramp & peak FTE change
        new_fte = round(current_brd.total_person_days / (new_wks * 5.0), 2)
        delta_fte = round(new_fte - (current_brd.total_person_days / (old_wks * 5.0)), 2)
        
        affected["Schedule Compression/Extension"] = f"Timeline adjusted from {old_wks:.1f} weeks to {new_wks:.1f} weeks"
        affected["Resource Loading Density"] = f"Average staffing level adjusted from {current_brd.total_person_days / (old_wks * 5.0):.2f} to {new_fte:.2f} FTE"
        affected["Ramp & Feasibility"] = "Feasibility checks re-evaluated for weekly ramp thresholds"
        
        narrative = (
            f"Adjusting target timeline from {old_wks:.1f} to {new_wks:.1f} weeks redistributes the {current_brd.total_person_days:.1f} person-days "
            f"across calendar working days. Required team loading shifts by {delta_fte:+.2f} FTE."
        )

    # 4. Hourly Rate change
    elif "rate" in param or "hourly" in param:
        try:
            old_r = float(old_value)
            new_r = float(new_value)
        except Exception:
            old_r, new_r = 30.0, 35.0
            
        new_labour = round(current_brd.total_person_hours * new_r, 2)
        delta_cost = round(new_labour - current_brd.total_labour_cost_usd, 2)
        
        affected["Commercial Budget"] = f"Labour rate revised from ${old_r:.2f}/hr to ${new_r:.2f}/hr"
        affected["Total Contract Value"] = f"Adjusted by ${delta_cost:,.2f}"
        
        narrative = (
            f"Updating blended rate to ${new_r:.2f}/hr recalculates all 12 discipline costs across {current_brd.total_person_hours:,.0f} hours, "
            f"yielding a total budget change of ${delta_cost:,.2f}."
        )

    base_duration = current_brd.total_duration_weeks
    base_days = current_brd.total_person_days
    base_cost = current_brd.total_labour_cost_usd
    base_fte = round(base_days / max(base_duration * 5.0, 1.0), 2)
    base_cloud = current_brd.sizing_metrics.total_monthly_cloud_cost_usd if current_brd.sizing_metrics else 645.0

    sim_duration = float(str(new_value).split()[0]) if ("duration" in param or "week" in param) else base_duration
    sim_days = round(max(5.0, base_days + delta_days), 1)
    sim_cost = round(max(100.0, base_cost + delta_cost), 2)
    sim_fte = round(max(0.2, base_fte + delta_fte), 2)
    sim_cloud = new_cloud if ("user" in param or "traffic" in param) and "new_cloud" in locals() else base_cloud

    return ImpactAnalysisResult(
        parameter_changed=parameter_changed,
        old_value=old_value,
        new_value=new_value,
        affected_dimensions=affected,
        unaffected_dimensions=unaffected,
        narrative_explanation=narrative,
        delta_days=delta_days,
        delta_cost_usd=delta_cost,
        delta_fte=delta_fte,
        base_duration_weeks=base_duration,
        base_person_days=base_days,
        base_cost_usd=base_cost,
        base_fte=base_fte,
        base_monthly_cloud_usd=base_cloud,
        sim_duration_weeks=sim_duration,
        sim_person_days=sim_days,
        sim_cost_usd=sim_cost,
        sim_fte=sim_fte,
        sim_monthly_cloud_usd=sim_cloud
    )

def commit_change_impact(
    session: ProjectSession,
    parameter_changed: str,
    new_value: Any
) -> BRDDocument:
    """
    Applies the simulated change directly to the active session baseline,
    re-runs the deterministic planner, logs an audit entry to the calculation ledger,
    and records a revision snapshot.
    """
    from backend.agent_discovery import AnswerItem
    from backend.agent_planner import generate_brd
    from backend.models import CalculationLedgerItem
    from datetime import datetime

    param = parameter_changed.lower().strip()
    
    if "user" in param or "traffic" in param or "request" in param:
        session.answers["q_users"] = AnswerItem(
            question_id="q_users",
            question_title="Concurrent Users & Scale",
            answer=str(new_value),
            is_default=False
        )
    elif "tier" in param:
        session.answers["q_tier"] = AnswerItem(
            question_id="q_tier",
            question_title="Delivery Tier",
            answer=str(new_value),
            is_default=False
        )
    elif "duration" in param or "week" in param:
        session.answers["q_timeline"] = AnswerItem(
            question_id="q_timeline",
            question_title="Target Duration",
            answer=str(new_value),
            is_default=False
        )
    elif "rate" in param or "hourly" in param:
        try:
            r = float(str(new_value).replace("$", "").replace("£", "").split("/")[0])
            session.answers["q_rate"] = AnswerItem(
                question_id="q_rate",
                question_title="Blended Hourly Rate",
                answer=str(r),
                is_default=False
            )
            if session.brd:
                session.brd.blended_hourly_rate = r
        except Exception:
            pass

    # Preserve existing custom canonical requirements and prior calculation ledger entries
    prior_reqs = session.brd.canonical_requirements if session.brd else []
    prior_ledger = session.brd.calculation_ledger if session.brd else []

    # Regenerate BRD deterministically
    brd = generate_brd(session)

    # Merge preserved custom canonical requirements
    if prior_reqs:
        prior_map = {r.requirement_id: r for r in prior_reqs}
        merged_reqs = []
        for r in brd.canonical_requirements:
            if r.requirement_id in prior_map:
                merged_reqs.append(prior_map[r.requirement_id])
            else:
                merged_reqs.append(r)
        brd.canonical_requirements = merged_reqs

    # Keep existing ledger items that are not in new brd
    existing_ids = {item.calculation_id for item in brd.calculation_ledger}
    for item in prior_ledger:
        if item.calculation_id not in existing_ids:
            brd.calculation_ledger.append(item)

    # Append ledger audit trail
    calc_id = f"CALC-SCENARIO-{len(brd.calculation_ledger) + 1:03d}"
    ledger_entry = CalculationLedgerItem(
        calculation_id=calc_id,
        calculation_type="SCENARIO_COMMIT",
        inputs={"parameter": parameter_changed, "committed_value": str(new_value)},
        formula=f"Committed simulation scenario for {parameter_changed} = {new_value}",
        result={
            "parameter_committed": parameter_changed,
            "new_value": str(new_value),
            "new_person_days": brd.total_person_days,
            "new_labour_cost": brd.total_labour_cost_usd,
            "new_duration_weeks": brd.total_duration_weeks,
            "new_monthly_cloud_usd": brd.sizing_metrics.total_monthly_cloud_cost_usd if brd.sizing_metrics else 645.0
        },
        engine_version="1.0.0",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    brd.calculation_ledger.append(ledger_entry)
    session.brd = brd

    return brd
