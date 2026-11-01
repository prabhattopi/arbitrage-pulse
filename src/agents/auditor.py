import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from src.core.models import PriceProposal, ProposalStatus

class AuditorAgent:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_path = self.log_dir / "agent_work_log.json"
        self.console = Console()

    def display_proposals(self, proposals: List[PriceProposal]) -> None:
        """Renders an interactive executive summary table in the terminal."""
        table = Table(title="🤖 ArbitragePulse: Pricing Action Diff & Audit Review", show_lines=True)

        table.add_column("SKU", style="cyan", no_wrap=True)
        table.add_column("Product", style="bold white")
        table.add_column("Old Price", style="yellow")
        table.add_column("Proposed", style="green")
        table.add_column("Action", style="magenta")
        table.add_column("Margin %", justify="right")
        table.add_column("Status / Sentinel Check", style="bold")
        table.add_column("Reasoning", style="dim")

        for p in proposals:
            status_style = "green" if p.status == ProposalStatus.AUTO_APPROVED else "red"
            margin_text = f"{p.profit_margin_pct:.1f}%"
            diff_text = f"${p.old_price:.2f} ➔ ${p.proposed_price:.2f}"

            table.add_row(
                p.sku,
                p.product_title,
                f"${p.old_price:.2f}",
                f"${p.proposed_price:.2f}",
                p.action.value,
                margin_text,
                f"[{status_style}]{p.status.value}[/{status_style}]",
                p.reasoning
            )

        self.console.print(table)

    def request_human_approval(self, proposal: PriceProposal, auto_input: str = None) -> bool:
        """Prompts human merchant for confirmation. If safety check failed, warns explicitly."""
        if proposal.status == ProposalStatus.BLOCKED_MARGIN_VIOLATION:
            self.console.print(f"[bold red]⛔ BLOCKED:[/bold red] Cannot approve {proposal.sku} due to hard margin breach.")
            return False

        if auto_input is not None:
            choice = auto_input.strip().lower()
        else:
            prompt_msg = f"Approve price adjustment for {proposal.sku} from ${proposal.old_price:.2f} to ${proposal.proposed_price:.2f}? (y/N): "
            choice = input(prompt_msg).strip().lower()

        approved = choice in ["y", "yes"]
        return approved

    def record_decision(self, proposal: PriceProposal, approved: bool, reviewer: str = "Merchant") -> Dict[str, Any]:
        """Appends verified decision into the audit trail work log for Devpost submission proof."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sku": proposal.sku,
            "product_title": proposal.product_title,
            "old_price": proposal.old_price,
            "proposed_price": proposal.proposed_price,
            "action": proposal.action.value,
            "profit_margin_pct": proposal.profit_margin_pct,
            "sentinel_status": proposal.status.value,
            "reasoning": proposal.reasoning,
            "human_approved": approved,
            "reviewer": reviewer
        }

        existing_logs = []
        if self.audit_log_path.exists():
            try:
                with open(self.audit_log_path, "r", encoding="utf-8") as f:
                    existing_logs = json.load(f)
            except Exception:
                existing_logs = []

        existing_logs.append(record)

        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(existing_logs, f, indent=2)

        return record