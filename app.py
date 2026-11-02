import streamlit as st
import pandas as pd
import json
from src.agents.scout import ScoutAgent
from src.agents.strategist import StrategistAgent
from src.agents.executor import StoreExecutorAgent

st.set_page_config(page_title="ArbitragePulse | Autonomous Commerce Agent", page_icon="⚡", layout="wide")

st.title("⚡ ArbitragePulse: Autonomous Commerce Pricing Desk")
st.caption("Multi-Agent Arbitrage Engine with Hard Margin Sentinel & Human-in-the-Loop Governance")

col1, col2 = st.columns([1, 1])

scout = ScoutAgent("src/data/mock_store_catalog.json", "src/data/mock_competitors.json")
strategist = StrategistAgent()
executor = StoreExecutorAgent("src/data/mock_store_catalog.json")

snapshots = scout.build_market_snapshots()
proposals = strategist.generate_proposals(snapshots)

st.subheader("📊 Market Snapshot & Guardrailed Proposals")

table_data = []
for p in proposals:
    table_data.append({
        "SKU": p.sku,
        "Product": p.product_title,
        "Current Price": f"${p.old_price:.2f}",
        "Target Price": f"${p.proposed_price:.2f}",
        "Action": p.action.value,
        "Margin %": f"{p.profit_margin_pct:.1f}%",
        "Sentinel Status": p.status.value,
        "Reasoning": p.reasoning
    })

df = pd.DataFrame(table_data)
st.dataframe(df, use_container_width=True)

st.divider()

st.subheader("👨‍💼 Human-in-the-Loop Approval Gate")
approvable = [p for p in proposals if p.status.value != "BLOCKED_MARGIN_VIOLATION"]
blocked = [p for p in proposals if p.status.value == "BLOCKED_MARGIN_VIOLATION"]

if blocked:
    st.error(f"⛔ Margin Sentinel automatically blocked {len(blocked)} item(s) due to hard floor breach.")

selected_skus = st.multiselect(
    "Select proposals to authorize and execute to production store:",
    options=[p.sku for p in approvable],
    default=[p.sku for p in approvable]
)

if st.button("🚀 Authorize & Execute Verified Pricing Update", type="primary"):
    to_apply = [p for p in approvable if p.sku in selected_skus]
    res = executor.execute_updates(to_apply)
    if res["verified"]:
        st.success(f"✔ Live Storefront verified and updated! ({res['updated_count']} products updated)")
        st.balloons()
    else:
        st.error("❌ Verification failed. Auto-rollback triggered.")

st.divider()
st.subheader("📜 Audit Work-Log Trail")
try:
    with open("logs/agent_work_log.json", "r") as f:
        audit_data = json.load(f)
    st.json(audit_data[-3:])
except Exception:
    st.info("No audit logs yet. Run interactive CLI or hit Execute above.")