"""Queries behind the dashboard, kept free of Streamlit so they can be tested."""

from __future__ import annotations

import sqlite3

import pandas as pd

from budgetbuddy import recurring as rec
from budgetbuddy.categorise import TRANSFERS
from budgetbuddy.valuations import isa_summaries

# Leading categories get their own colour; the rest fold into "Other"
MAX_CATEGORY_SERIES = 7


def bank_transactions(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT t.id, t.posted_on, t.amount_pence, t.merchant, t.counterparty, t.reference,
               t.category, t.category_source, t.is_transfer, t.balance_pence
        FROM transactions t JOIN accounts a ON a.id = t.account_id
        WHERE a.kind = 'bank' ORDER BY t.posted_on, t.id
        """,
        conn,
    )
    df["posted_on"] = pd.to_datetime(df["posted_on"])
    df["month"] = df["posted_on"].dt.strftime("%Y-%m")
    df["amount"] = df["amount_pence"] / 100
    return df


def spending(df: pd.DataFrame) -> pd.DataFrame:
    """Money out that is real spending: no transfers to the ISAs, no income."""
    out = df[(df["category"] != TRANSFERS) & (df["category"] != "Income") & (df["amount_pence"] < 0)].copy()
    out["spent"] = -out["amount"]
    return out


def category_order(spend: pd.DataFrame) -> list[str]:
    """Fixed, all-time order so a category keeps its colour whatever month is picked."""
    totals = spend.groupby("category")["spent"].sum().sort_values(ascending=False)
    leading = list(totals.index[:MAX_CATEGORY_SERIES])
    return leading + (["Other"] if len(totals) > MAX_CATEGORY_SERIES else [])


def monthly_by_category(spend: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    folded = spend.assign(series=spend["category"].where(spend["category"].isin(order), "Other"))
    table = folded.pivot_table(index="month", columns="series", values="spent", aggfunc="sum", fill_value=0)
    return table.reindex(columns=[c for c in order if c in table.columns])


def income_vs_outgoings(df: pd.DataFrame) -> pd.DataFrame:
    """Per month: money in, money spent, and money moved into the ISAs."""
    rows = []
    for month, g in df.groupby("month"):
        rows.append(
            {
                "month": month,
                "Income": g.loc[g["category"] == "Income", "amount"].sum(),
                "Spending": -g.loc[(g["category"] != TRANSFERS) & (g["amount"] < 0), "amount"].sum(),
                "Into ISAs": -g.loc[(g["category"] == TRANSFERS) & (g["amount"] < 0), "amount"].sum(),
            }
        )
    out = pd.DataFrame(rows, columns=["month", "Income", "Spending", "Into ISAs"])
    out["Left over"] = out["Income"] - out["Spending"] - out["Into ISAs"]
    return out


def latest_balance(df: pd.DataFrame) -> float | None:
    with_balance = df.dropna(subset=["balance_pence"])
    return None if with_balance.empty else with_balance.iloc[-1]["balance_pence"] / 100


def recurring_table(conn: sqlite3.Connection) -> pd.DataFrame:
    rows = [r for r in rec.items(conn) if r["use_status"] == "active"]
    return pd.DataFrame(
        [
            {
                "Group": rec.group_of(r),
                "Name": r["name"],
                "Amount": abs(r["use_amount"]) / 100,
                "How often": r["frequency"],
                "Per month": abs(rec.monthly_equivalent(r["use_amount"], r["frequency"])) / 100,
                "Next due": r["next_due"],
                "Varies": bool(r["variable"]),
                "money_in": r["use_amount"] > 0,
            }
            for r in rows
        ],
        columns=["Group", "Name", "Amount", "How often", "Per month", "Next due", "Varies", "money_in"],
    )


def isa_table(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ISA": s.account,
                "Owner": s.owner,
                "Value": None if s.value_pence is None else s.value_pence / 100,
                "Valued on": s.valued_on,
                "Net invested": s.invested_pence / 100,
                "Growth": None if s.growth_pence is None else s.growth_pence / 100,
            }
            for s in isa_summaries(conn)
        ],
        columns=["ISA", "Owner", "Value", "Valued on", "Net invested", "Growth"],
    )
