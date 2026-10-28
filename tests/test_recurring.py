import datetime as dt

from budgetbuddy import recurring as rec
from budgetbuddy.cli import main
from budgetbuddy.importer import import_file

HEADER = "Date,Counter Party,Reference,Type,Amount (GBP),Balance (GBP),Spending Category,Notes\n"


def _history(tmp_path):
    """Six months (May to October 2026) of a made up joint account."""
    lines = []

    def add(day, who, amount, kind="CARD PAYMENT", category="GENERAL", ref=""):
        lines.append((day, f"{day:%d/%m/%Y},{who},{ref},{kind},{amount:.2f},0,{category},\n"))

    for month in range(5, 11):
        add(dt.date(2026, month, 25), "ACME LTD", 2500, "FASTER PAYMENT", "INCOME", "SALARY")
        add(dt.date(2026, month, 28), "BETA PLC", 2100, "FASTER PAYMENT", "INCOME", "PAY")
        add(dt.date(2026, month, 1), "Example Bank", -2000, "DIRECT DEBIT", "MORTGAGE")
        add(dt.date(2026, month, 3), "Vanguard", -500, "STANDING ORDER", "SAVING", "ISA A")
        add(dt.date(2026, month, 3), "Vanguard", -300, "STANDING ORDER", "SAVING", "ISA B")
        add(dt.date(2026, month, 12), "Netflix", -10.99 if month < 8 else -12.99, category="ENTERTAINMENT")
        add(dt.date(2026, month, 15), "Example Energy", -150 - month * 12, "DIRECT DEBIT", "BILLS_AND_SERVICES")
        add(dt.date(2026, month, 20), "Amazon", -8.99, category="SHOPPING")
        add(dt.date(2026, month, 2 + month), "Amazon", -20 - month * 7, category="SHOPPING")
        if month <= 7:
            add(dt.date(2026, month, 5), "Example Gym", -35, "DIRECT DEBIT", "LIFESTYLE")
    for week in range(26):
        add(dt.date(2026, 5, 4) + dt.timedelta(weeks=week), "Jo Cleaner", -40, "FASTER PAYMENT")
    add(dt.date(2026, 6, 9), "Corner Shop", -5)
    add(dt.date(2026, 9, 2), "Corner Shop", -7)

    path = tmp_path / "history.csv"
    path.write_text(HEADER + "".join(line for _, line in sorted(lines, key=lambda x: x[0])))
    return path


def _by_name(conn):
    return {(r["name"], r["use_amount"]): r for r in rec.items(conn)}


def test_detects_regular_items(conn, data_dir, tmp_path):
    import_file(conn, _history(tmp_path), data_dir)
    found = {(r["name"], r["frequency"], r["use_status"]) for r in rec.items(conn)}
    assert ("ACME", "monthly", "active") in found
    assert ("BETA", "monthly", "active") in found
    assert ("Example Bank", "monthly", "active") in found
    assert ("Jo Cleaner", "weekly", "active") in found
    assert ("Example Gym", "monthly", "lapsed") in found
    # Prime style subscription found among irregular Amazon orders; the orders themselves are not
    amazon = [r for r in rec.items(conn) if r["name"] == "Amazon"]
    assert [(r["use_amount"], r["frequency"]) for r in amazon] == [(-899, "monthly")]
    assert not any(r["name"] == "Corner Shop" for r in rec.items(conn))


def test_two_isa_standing_orders_kept_apart(conn, data_dir, tmp_path):
    import_file(conn, _history(tmp_path), data_dir)
    vanguard = sorted(r["use_amount"] for r in rec.items(conn) if r["name"] == "Vanguard")
    assert vanguard == [-50000, -30000]
    assert all(rec.group_of(r) == "Savings & ISAs" for r in rec.items(conn) if r["name"] == "Vanguard")


def test_amounts_price_rise_and_variable_bills(conn, data_dir, tmp_path):
    import_file(conn, _history(tmp_path), data_dir)
    items = _by_name(conn)
    netflix = items[("Netflix", -1299)]
    assert netflix["previous_amount_pence"] == -1099
    assert netflix["next_due"] == "2026-11-12"
    energy = next(r for (name, _), r in items.items() if name == "Example Energy")
    assert energy["variable"] == 1
    assert energy["use_amount"] == -(15000 + 1200 * 9)  # average of Aug, Sep, Oct


def test_user_choices_survive_redetection(conn, data_dir, tmp_path):
    import_file(conn, _history(tmp_path), data_dir)
    items = _by_name(conn)
    netflix_id = items[("Netflix", -1299)]["id"]
    cleaner_id = items[("Jo Cleaner", -4000)]["id"]
    rec.set_user_status(conn, netflix_id, "ended")
    rec.set_amount(conn, cleaner_id, -4500)
    rec.refresh(conn)
    rows = {r["id"]: r for r in rec.items(conn)}
    assert rows[netflix_id]["use_status"] == "ended"
    assert rows[cleaner_id]["use_amount"] == -4500


def test_monthly_equivalent_and_next_dates():
    assert rec.monthly_equivalent(-4000, "weekly") == -17333
    assert rec.monthly_equivalent(-60000, "yearly") == -5000
    assert rec.next_after(dt.date(2026, 1, 31), "monthly", 31) == dt.date(2026, 2, 28)
    assert rec.next_after(dt.date(2026, 3, 15), "yearly") == dt.date(2027, 3, 15)


def test_cli_recurring(tmp_path, capsys):
    data = ["--data-dir", str(tmp_path / "d")]
    main(data + ["import", str(_history(tmp_path))])
    capsys.readouterr()
    assert main(data + ["recurring", "add", "Car insurance", "600", "--every", "yearly", "--next", "15/03/2027", "--category", "insurance"]) == 0
    assert main(data + ["recurring"]) == 0
    out = capsys.readouterr().out
    assert "Income  (£4,600.00 a month)" in out
    assert "Car insurance" in out and "added by you" in out
    assert "Netflix: up from £10.99 to £12.99" in out
    assert "Example Gym" in out.split("Stopped appearing")[1]
