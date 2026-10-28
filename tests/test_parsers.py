import datetime as dt
from decimal import Decimal

import pytest
from openpyxl import Workbook

from budgetbuddy.models import Transaction, parse_pence
from budgetbuddy.parsers import detect, parse_file, starling, vanguard, vanguard_orders


@pytest.mark.parametrize(
    "raw, pence",
    [("1,120.50", 112050), ("-3.40", -340), ("£12", 1200), ("(4.00)", -400), (263.05, 26305), ("", None)],
)
def test_parse_pence(raw, pence):
    assert parse_pence(raw) == pence


def test_starling_rows(fixtures):
    st = parse_file(fixtures / "starling_sample.csv")
    assert st.parser == "starling" and st.account_kind == "bank"
    # Opening balance line is skipped silently
    assert len(st.transactions) == 8 and not st.warnings
    first = st.transactions[0]
    assert first.posted_on == dt.date(2026, 9, 1)
    assert first.amount_pence == 250000
    assert first.counterparty == "ACME LTD" and first.source_category == "INCOME"
    energy = st.transactions[-1]
    assert energy.amount_pence == -112050 and energy.notes == "annual top up"


def test_detects_formats(fixtures):
    assert detect(fixtures / "starling_sample.csv") is starling
    assert detect(fixtures / "vanguard_isa_a.csv") is vanguard


def test_vanguard_csv(fixtures):
    st = parse_file(fixtures / "vanguard_isa_a.csv")
    assert [t.kind for t in st.transactions] == ["deposit", "buy", "fee"]
    assert st.transactions[0].amount_pence == 50000
    (trade,) = st.trades
    assert trade.quantity == Decimal("1.9000") and trade.cost_pence == 49980


def test_vanguard_xlsx_with_real_dates(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "ISA"
    ws.append(["Cash Transactions"])
    ws.append(["Date", "Details", "Amount", "Balance"])
    ws.append([dt.datetime(2026, 10, 1), "Regular Deposit", 250.0, 250.0])
    ws.append([])
    ws.append(["Investment Transactions"])
    ws.append(["Date", "InvestmentName", "TransactionDetails", "Quantity", "Price", "Cost"])
    ws.append([dt.datetime(2026, 10, 2), "FTSE Global All Cap", "Bought 1.5 FTSE Global All Cap", 1.5, 166.66, 249.99])
    path = tmp_path / "vanguard.xlsx"
    wb.save(path)

    st = parse_file(path)
    assert st.parser == "vanguard"
    assert st.transactions[0].posted_on == dt.date(2026, 10, 1)
    assert st.transactions[0].kind == "deposit"
    assert st.trades[0].cost_pence == 24999


@pytest.mark.parametrize(
    "details, kind",
    [
        ("Withdrawal to bank", "withdrawal"),
        ("Sold 2.0 units of Fund", "sell"),
        ("Interest", "income"),
        ("Something new", "other"),
    ],
)
def test_vanguard_classify(details, kind):
    assert vanguard.classify(details) == kind


def test_unknown_file_rejected(tmp_path):
    path = tmp_path / "random.csv"
    path.write_text("a,b,c\n1,2,3\n")
    with pytest.raises(ValueError, match="not recognised"):
        parse_file(path)


def test_starling_tab_separated_from_excel(fixtures):
    path = fixtures / "starling_excel_tabs.csv"
    assert detect(path) is starling
    st = parse_file(path)
    assert [t.amount_pence for t in st.transactions] == [-6050, -200000, -2700]
    assert [t.source_category for t in st.transactions] == ["BILLS_AND_SERVICES", "MORTGAGE", "PETS"]
    (warning,) = st.warnings
    assert "Excel" in warning


def test_excel_mangled_reference_still_matches_original(fixtures):
    (mangled,) = [t for t in parse_file(fixtures / "starling_excel_tabs.csv").transactions if t.reference == "4E+15"]
    original = Transaction(**{**mangled.__dict__, "reference": "4012345678901234"})
    assert mangled.fingerprint() == original.fingerprint()


def test_vanguard_orders_pasted_from_website(fixtures):
    path = fixtures / "vanguard_orders_pasted.txt"
    assert detect(path) is vanguard_orders
    st = parse_file(path)
    assert st.account_kind == "isa" and not st.transactions
    sell, buy = st.trades
    assert sell.traded_on == dt.date(2026, 10, 23)
    assert sell.fund == "LifeStrategy® 80% Equity Fund - Accumulation"
    assert (sell.quantity, sell.cost_pence, sell.details) == (Decimal("-0.0526"), -2024, "Single Sell")
    assert (buy.quantity, buy.cost_pence, buy.price) == (Decimal("1.0144"), 30000, Decimal("295.7413"))
    assert st.warnings == ["1 pending order(s) skipped; import again once they complete"]


def test_unicode_minus_sign():
    assert parse_pence("−£20.24") == -2024
