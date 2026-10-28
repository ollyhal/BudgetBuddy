from budgetbuddy.dashboard import data
from budgetbuddy.importer import import_file
from test_recurring import _history


def test_monthly_flows_and_categories(conn, data_dir, tmp_path):
    import_file(conn, _history(tmp_path), data_dir)
    txns = data.bank_transactions(conn)
    flows = data.income_vs_outgoings(txns).set_index("month")
    october = flows.loc["2026-10"]
    assert october["Income"] == 4600
    assert october["Into ISAs"] == 800
    assert october["Left over"] == october["Income"] - october["Spending"] - 800

    spend = data.spending(txns)
    assert "Transfers" not in set(spend["category"]) and "Income" not in set(spend["category"])
    order = data.category_order(spend)
    assert order[0] == "Mortgage" and len(order) <= data.MAX_CATEGORY_SERIES + 1
    monthly = data.monthly_by_category(spend, order)
    assert list(monthly.index) == ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
    assert abs(monthly.sum(axis=1).loc["2026-10"] - spend[spend["month"] == "2026-10"]["spent"].sum()) < 0.01


def test_recurring_and_isa_tables(conn, data_dir, tmp_path, fixtures):
    import_file(conn, _history(tmp_path), data_dir)
    import_file(conn, fixtures / "vanguard_orders_pasted.txt", data_dir, account="Vanguard ISA A")
    table = data.recurring_table(conn)
    assert table.loc[table["money_in"], "Per month"].sum() == 4600
    assert set(table["Group"]) == {"Income", "Bills & regular payments", "Subscriptions", "Savings & ISAs"}
    isas = data.isa_table(conn)
    assert list(isas["ISA"]) == ["Vanguard ISA A"] and isas["Value"].isna().all()
