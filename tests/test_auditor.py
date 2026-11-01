import json
from src.core.models import PriceProposal, ActionType, ProposalStatus
from src.agents.auditor import AuditorAgent

def test_auditor_blocks_margin_breaches_from_human_approval(tmp_path):
    auditor = AuditorAgent(log_dir=str(tmp_path))
    blocked_proposal = PriceProposal(
        sku="TEST-FAIL",
        product_title="Loss Item",
        old_price=100.0,
        proposed_price=40.0,
        action=ActionType.PRICE_DROP,
        status=ProposalStatus.BLOCKED_MARGIN_VIOLATION,
        reasoning="Margin floor breached",
        profit_margin_pct=-10.0,
        safety_checks_passed=False
    )
    # Even if automated input tries "y", auditor MUST reject
    approved = auditor.request_human_approval(blocked_proposal, auto_input="y")
    assert approved is False

def test_auditor_records_audit_trail_log(tmp_path):
    auditor = AuditorAgent(log_dir=str(tmp_path))
    valid_proposal = PriceProposal(
        sku="TEST-PASS",
        product_title="Profitable Item",
        old_price=100.0,
        proposed_price=94.50,
        action=ActionType.PRICE_DROP,
        status=ProposalStatus.AUTO_APPROVED,
        reasoning="Competitive undercut",
        profit_margin_pct=25.0,
        safety_checks_passed=True
    )

    approved = auditor.request_human_approval(valid_proposal, auto_input="y")
    assert approved is True

    record = auditor.record_decision(valid_proposal, approved=approved, reviewer="Lead Merchandiser")
    assert record["human_approved"] is True
    assert record["sku"] == "TEST-PASS"

    # Verify log file was written on disk
    log_file = tmp_path / "agent_work_log.json"
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["proposed_price"] == 94.50