from typing import List, Dict, Any, Optional
from rich.console import Console
from src.agents.scout import ScoutAgent
from src.agents.strategist import StrategistAgent
from src.agents.auditor import AuditorAgent
from src.agents.executor import StoreExecutorAgent
from src.core.models import PriceProposal

class ArbitragePulseOrchestrator:
    def __init__(
        self,
        catalog_path: str = "src/data/mock_store_catalog.json",
        competitor_path: str = "src/data/mock_competitors.json",
        log_dir: str = "logs"
    ):
        self.catalog_path = catalog_path
        self.scout = ScoutAgent(catalog_path=catalog_path, competitor_path=competitor_path)
        self.strategist = StrategistAgent()
        self.auditor = AuditorAgent(log_dir=log_dir)
        self.executor = StoreExecutorAgent(catalog_path=catalog_path)
        self.console = Console()

    def run_cycle(
        self,
        auto_approve: Optional[bool] = None,
        dry_run: bool = False,
        interactive: bool = True
    ) -> Dict[str, Any]:
        self.console.print("\n[bold cyan]⚡ ArbitragePulse Agent Cycle Triggered[/bold cyan]")

        # 1. Scout Phase
        self.console.print("[dim]🔍 Step 1: Scout Agent scanning catalog and competitor feeds...[/dim]")
        snapshots = self.scout.build_market_snapshots()
        self.console.print(f"[green]✔ Scout completed: {len(snapshots)} products analyzed.[/green]")

        # 2. Strategy & Sentinel Phase
        self.console.print("[dim]🧠 Step 2: Strategist & Margin Sentinel generating safe pricing proposals...[/dim]")
        proposals = self.strategist.generate_proposals(snapshots)
        self.console.print(f"[green]✔ Guardrails passed: {len(proposals)} proposals ready.[/green]\n")

        # 3. Interactive Review
        if interactive:
            self.auditor.display_proposals(proposals)

        # 4. Human-in-the-Loop Approval Gate
        approved_proposals: List[PriceProposal] = []
        for p in proposals:
            if auto_approve is not None:
                user_choice = "y" if auto_approve else "n"
            else:
                user_choice = None

            is_approved = self.auditor.request_human_approval(p, auto_input=user_choice)
            self.auditor.record_decision(p, approved=is_approved, reviewer="Terminal Merchant")

            if is_approved:
                approved_proposals.append(p)

        self.console.print(f"\n[bold]Summary:[/bold] Approved {len(approved_proposals)} of {len(proposals)} proposals.")

        # 5. Execution Phase
        if dry_run:
            self.console.print("[yellow]⚠ Dry-run active. Skipping store mutation.[/yellow]")
            return {
                "total_evaluated": len(proposals),
                "approved_count": len(approved_proposals),
                "execution": {"status": "DRY_RUN", "verified": True, "updated_count": 0}
            }

        self.console.print("[dim]🚀 Step 5: Executor Agent applying updates and running verification...[/dim]")
        exec_result = self.executor.execute_updates(approved_proposals)

        if exec_result["verified"]:
            self.console.print(f"[bold green]✔ Store successfully updated and verified! ({exec_result['updated_count']} products modified)[/bold green]\n")
        else:
            self.console.print("[bold red]❌ Verification failed. Catalog rolled back safely.[/bold red]\n")

        return {
            "total_evaluated": len(proposals),
            "approved_count": len(approved_proposals),
            "execution": exec_result
        }