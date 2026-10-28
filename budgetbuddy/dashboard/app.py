"""BudgetBuddy dashboard. Start it with: python -m budgetbuddy dashboard

Runs on http://localhost only; nothing leaves your computer.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from budgetbuddy import categorise as cat
from budgetbuddy import recurring as rec
from budgetbuddy.dashboard import data
from budgetbuddy.db import connect, default_data_dir

# Validated categorical order (light, dark); "Other" is always the neutral grey
PALETTE = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9"],
}
OTHER = {"light": "#8f8e88", "dark": "#77766f"}
SURFACE = {"light": "#ffffff", "dark": "#0e1117"}
GRID = {"light": "#e6e5e0", "dark": "#2b2b29"}


def _data_dir() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=None)
    args, _ = parser.parse_known_args(sys.argv[1:])
    return args.data_dir or default_data_dir()


def _mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except AttributeError:
        return "light"


def _money(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "–"
    return f"{'-' if value < 0 else ''}£{abs(value):,.0f}"


def _month_label(month: str) -> str:
    return pd.Timestamp(f"{month}-01").strftime("%b %Y")


def _style(fig: go.Figure, mode: str, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        hoverlabel=dict(namelength=-1),
        bargap=0.35,
    )
    fig.update_yaxes(gridcolor=GRID[mode], zeroline=False, tickprefix="£", separatethousands=True)
    fig.update_xaxes(showgrid=False)
    return fig


def _colour_map(order: list[str], mode: str) -> dict[str, str]:
    colours = dict(zip([c for c in order if c != "Other"], PALETTE[mode]))
    colours["Other"] = OTHER[mode]
    return colours


def main() -> None:
    st.set_page_config(page_title="BudgetBuddy", page_icon="💷", layout="wide")
    mode = _mode()
    data_dir = _data_dir()
    conn = connect(data_dir)
    txns = data.bank_transactions(conn)

    st.title("BudgetBuddy")
    if txns.empty:
        st.info("No statements imported yet. Run `python -m budgetbuddy import <file>` and refresh.")
        return

    months = sorted(txns["month"].unique())
    top = st.columns([1, 3])
    month = top[0].selectbox("Month", months[::-1], format_func=_month_label)
    top[1].caption(
        f"Data from {txns['posted_on'].min():%d %b %Y} to {txns['posted_on'].max():%d %b %Y}  ·  "
        f"stored locally in {data_dir}"
    )

    spend = data.spending(txns)
    order = data.category_order(spend)
    colours = _colour_map(order, mode)
    flows = data.income_vs_outgoings(txns)
    recurring = data.recurring_table(conn)
    isas = data.isa_table(conn)

    # Headline numbers
    month_spend = spend.loc[spend["month"] == month, "spent"].sum()
    earlier = [m for m in months if m < month][-3:]
    avg_spend = spend[spend["month"].isin(earlier)].groupby("month")["spent"].sum().mean() if earlier else None
    regular_in = recurring.loc[recurring["money_in"], "Per month"].sum()
    regular_out = recurring.loc[~recurring["money_in"], "Per month"].sum()
    isa_total = isas["Value"].dropna().sum() if not isas.empty else None

    tiles = st.columns(5)
    tiles[0].metric("Joint account balance", _money(data.latest_balance(txns)))
    tiles[1].metric(
        "ISAs (latest values)", _money(isa_total) if isa_total else "–",
        help="Record values with: python -m budgetbuddy value \"Vanguard ISA A\" 12450",
    )
    tiles[2].metric(
        f"Spent in {_month_label(month)}",
        _money(month_spend),
        delta=None if avg_spend is None or pd.isna(avg_spend) else f"{_money(month_spend - avg_spend)} vs 3 month avg",
        delta_color="inverse",
    )
    tiles[3].metric("Regular income", f"{_money(regular_in)}/mo")
    tiles[4].metric(
        "Left after regular outgoings", f"{_money(regular_in - regular_out)}/mo",
        help="Regular income less bills, subscriptions and ISA payments: what's left for everyday spending",
    )

    tab_overview, tab_spend, tab_regular, tab_isa, tab_review, tab_forecast = st.tabs(
        ["Overview", "Spending", "Regular payments", "ISAs", "Needs a category", "Forecast"]
    )

    with tab_overview:
        st.subheader("Money in and out each month")
        fig = go.Figure()
        for i, series in enumerate(["Income", "Spending", "Into ISAs"]):
            fig.add_bar(
                x=[_month_label(m) for m in flows["month"]], y=flows[series], name=series,
                marker=dict(color=PALETTE[mode][i], line=dict(color=SURFACE[mode], width=2), cornerradius=4),
                hovertemplate="%{x}<br>" + series + ": £%{y:,.2f}<extra></extra>",
            )
        st.plotly_chart(_style(fig, mode), use_container_width=True)
        table = flows.assign(month=flows["month"].map(_month_label)).set_index("month")
        st.dataframe(table.style.format("£{:,.2f}"), use_container_width=True)

    with tab_spend:
        left, right = st.columns([3, 2])
        with left:
            st.subheader("Spending by category over time")
            monthly = data.monthly_by_category(spend, order)
            fig = go.Figure()
            for series in monthly.columns:
                fig.add_bar(
                    x=[_month_label(m) for m in monthly.index], y=monthly[series], name=series,
                    marker=dict(color=colours[series], line=dict(color=SURFACE[mode], width=2)),
                    hovertemplate="%{x}<br>" + series + ": £%{y:,.2f}<extra></extra>",
                )
            fig.update_layout(barmode="stack", legend_traceorder="normal")
            st.plotly_chart(_style(fig, mode, 400), use_container_width=True)
        with right:
            st.subheader(f"{_month_label(month)} by category")
            this_month = (
                spend[spend["month"] == month].groupby("category")["spent"].sum().sort_values()
            )
            fig = go.Figure(
                go.Bar(
                    x=this_month.values, y=this_month.index, orientation="h",
                    marker=dict(color=PALETTE[mode][0], cornerradius=4),
                    text=[_money(v) for v in this_month.values], textposition="outside",
                    hovertemplate="%{y}: £%{x:,.2f}<extra></extra>",
                )
            )
            fig = _style(fig, mode, max(240, 28 * len(this_month) + 40))
            # Room on the right so the value label on the longest bar is not cut off
            fig.update_xaxes(visible=False, range=[0, (this_month.max() if len(this_month) else 1) * 1.18])
            fig.update_yaxes(tickprefix="", gridcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader(f"Biggest merchants in {_month_label(month)}")
        merchants = (
            spend[spend["month"] == month]
            .groupby(["merchant", "category"])["spent"].agg(["sum", "count"])
            .sort_values("sum", ascending=False).head(15).reset_index()
            .rename(columns={"merchant": "Merchant", "category": "Category", "sum": "Spent", "count": "Payments"})
        )
        st.dataframe(merchants.style.format({"Spent": "£{:,.2f}"}), use_container_width=True, hide_index=True)

    with tab_regular:
        if recurring.empty:
            st.info("No regular payments found yet. Import at least 3 to 6 months of statements.")
        else:
            st.caption(
                "Found automatically from your statements. Change them with "
                "`python -m budgetbuddy recurring end|ignore|amount|add`."
            )
            for group in ("Income", "Bills & regular payments", "Subscriptions", "Savings & ISAs"):
                rows = recurring[recurring["Group"] == group].drop(columns=["Group", "money_in"])
                if rows.empty:
                    continue
                st.markdown(f"**{group}** · {_money(rows['Per month'].sum())} a month")
                st.dataframe(
                    rows.sort_values("Per month", ascending=False).style.format(
                        {"Amount": "£{:,.2f}", "Per month": "£{:,.2f}"}
                    ),
                    use_container_width=True, hide_index=True,
                )
            changes = [
                r for r in rec.items(conn)
                if r["use_status"] == "active" and r["previous_amount_pence"] is not None and r["use_amount"] < 0
            ]
            for r in changes:
                st.warning(
                    f"**{r['name']}** changed from {_money(abs(r['previous_amount_pence']) / 100)} "
                    f"to £{abs(r['amount_pence']) / 100:,.2f}"
                )
            lapsed = [r for r in rec.items(conn) if r["use_status"] == "lapsed"]
            if lapsed:
                st.markdown("**Stopped appearing** (probably cancelled, left out of the forecast)")
                st.dataframe(
                    pd.DataFrame(
                        [{"Name": r["name"], "Amount": abs(r["use_amount"]) / 100, "Last seen": r["last_seen"]} for r in lapsed]
                    ).style.format({"Amount": "£{:,.2f}"}),
                    use_container_width=True, hide_index=True,
                )

    with tab_isa:
        if isas.empty:
            st.info("No ISAs imported yet.")
        else:
            st.dataframe(
                isas.style.format({"Value": "£{:,.2f}", "Net invested": "£{:,.2f}", "Growth": "£{:,.2f}"}, na_rep="–"),
                use_container_width=True, hide_index=True,
            )
            st.caption("Net invested is fund purchases less sales. Values come from what you record each month.")

    with tab_review:
        queue = cat.uncategorised(conn)
        if not queue:
            st.success("Every transaction has a category.")
        else:
            st.caption('Fix with `python -m budgetbuddy rule "<merchant>" <category>`; biggest first.')
            st.dataframe(
                pd.DataFrame(
                    [{"Merchant": g.merchant, "Payments": g.count, "Total": g.total_pence / 100} for g in queue]
                ).style.format({"Total": "£{:,.2f}"}),
                use_container_width=True, hide_index=True,
            )

    with tab_forecast:
        st.info("The 12 month cash forecast is the next stage to be built.")


main()
