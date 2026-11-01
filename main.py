import argparse
from src.orchestrator import ArbitragePulseOrchestrator

def main():
    parser = argparse.ArgumentParser(
        description="ArbitragePulse: Autonomous Agentic Commerce Pricing Engine"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve all non-blocked proposals (non-interactive mode)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate market and log proposals without altering catalog data"
    )
    parser.add_argument(
        "--catalog",
        default="src/data/mock_store_catalog.json",
        help="Path to store catalog JSON"
    )
    parser.add_argument(
        "--competitors",
        default="src/data/mock_competitors.json",
        help="Path to competitor data JSON"
    )

    args = parser.parse_args()

    orchestrator = ArbitragePulseOrchestrator(
        catalog_path=args.catalog,
        competitor_path=args.competitors
    )

    orchestrator.run_cycle(
        auto_approve=True if args.auto_approve else None,
        dry_run=args.dry_run,
        interactive=True
    )

if __name__ == "__main__":
    main()