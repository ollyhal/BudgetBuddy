import pytest

from budgetbuddy import categorise as cat
from budgetbuddy.importer import import_file
from budgetbuddy.merchants import clean_merchant


@pytest.mark.parametrize(
    "counterparty, reference, expected",
    [
        ("TESCO STORES 1234", "", "Tesco"),
        ("PAYPAL *NETFLIX", "", "Netflix"),
        ("AMZNMKTPLACE*2K4XY", "", "Amazon"),
        ("E.ON Energy", "", "E.ON Energy"),
        ("JOE BLOGGS PLUMBING LTD", "", "Joe Bloggs Plumbing"),
        ("Premier Vet Alliance", "UK00881256", "Premier Vet Alliance"),
        ("", "SOMETHING", "Something"),
        ("", "", "Unknown"),
    ],
)
def test_clean_merchant(counterparty, reference, expected):
    assert clean_merchant(counterparty, reference) == expected


def _categories(conn):
    return {
        r["merchant"]: (r["category"], r["category_source"])
        for r in conn.execute("SELECT merchant, category, category_source FROM transactions")
    }


def test_import_categorises(conn, data_dir, fixtures):
    import_file(conn, fixtures / "starling_sample.csv", data_dir)
    got = _categories(conn)
    assert got["Tesco"] == ("Groceries", "builtin")
    assert got["Costa Coffee"] == ("Eating Out", "builtin")
    assert got["Vanguard"] == ("Transfers", "transfer")
    assert got["ACME"] == ("Income", "starling")
    assert got["Example Energy"] == ("Bills & Utilities", "starling")


def test_excel_tab_file_categories(conn, data_dir, fixtures):
    import_file(conn, fixtures / "starling_excel_tabs.csv", data_dir)
    got = _categories(conn)
    assert got["Example Bank"] == ("Mortgage", "starling")
    assert got["Example Vets"] == ("Pets", "builtin")
    assert got["Example Water"] == ("Bills & Utilities", "builtin")


def test_keywords_need_whole_words(conn):
    row = {"is_transfer": 0, "category_source": None, "category": None, "counterparty": "Velvet Lounge",
           "reference": "XO2B77", "source_category": "", "amount_pence": -1000}
    assert cat.choose_category(row, "Velvet Lounge", []) == (cat.UNCATEGORISED, "fallback")


def test_rule_learns_and_beats_builtin(conn, data_dir, fixtures):
    import_file(conn, fixtures / "starling_sample.csv", data_dir)
    category, changed = cat.add_rule(conn, "costa coffee", "eating out")
    assert (category, changed) == ("Eating Out", 2)  # source changes from builtin to rule
    cat.add_rule(conn, "Tesco", "Home")
    assert _categories(conn)["Tesco"] == ("Home", "rule")
    # Later imports use the rule too
    import_file(conn, fixtures / "starling_overlap.csv", data_dir)
    assert _categories(conn)["Costa Coffee"] == ("Eating Out", "rule")


def test_manual_override_survives_recategorising(conn, data_dir, fixtures):
    import_file(conn, fixtures / "starling_sample.csv", data_dir)
    (txn_id,) = conn.execute("SELECT id FROM transactions WHERE merchant = 'Tesco'").fetchone()
    cat.set_transaction_category(conn, txn_id, "holidays")
    cat.add_rule(conn, "Tesco", "Groceries")
    assert _categories(conn)["Tesco"] == ("Holidays", "manual")


def test_uncategorised_queue_and_spending(conn, data_dir, tmp_path):
    path = tmp_path / "s.csv"
    path.write_text(
        "Date,Counter Party,Reference,Type,Amount (GBP),Balance (GBP),Spending Category,Notes\n"
        "01/10/2026,Mystery Shop,,CARD PAYMENT,-40.00,100,GENERAL,\n"
        "02/10/2026,Mystery Shop,,CARD PAYMENT,-10.00,90,GENERAL,\n"
        "03/10/2026,Tesco,,CARD PAYMENT,-60.00,30,GROCERIES,\n"
        "03/10/2026,Vanguard,,FASTER PAYMENT,-20.00,20,SAVING,\n"
    )
    import_file(conn, path, data_dir)
    (group,) = cat.uncategorised(conn)
    assert (group.merchant, group.count, group.total_pence) == ("Mystery Shop", 2, -5000)
    spending = cat.spending_by_category(conn, "2026-10")
    assert spending == [("Groceries", 6000, 1), ("Uncategorised", 5000, 2)]
