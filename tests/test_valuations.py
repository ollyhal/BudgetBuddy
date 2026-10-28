import datetime as dt

import pytest

from budgetbuddy.cli import main
from budgetbuddy.importer import import_file
from budgetbuddy.valuations import import_values, isa_summaries, record_value


def test_value_and_growth(conn, data_dir, fixtures):
    import_file(conn, fixtures / "vanguard_orders_pasted.txt", data_dir, account="Vanguard ISA A", owner="A")
    record_value(conn, "vanguard isa a", "£290.00", dt.date(2026, 10, 1))
    record_value(conn, "Vanguard ISA A", "300.50", dt.date(2026, 10, 28))
    (s,) = isa_summaries(conn)
    # Buys £300.00 less the £20.24 sale
    assert (s.value_pence, s.valued_on, s.invested_pence, s.growth_pence) == (30050, "2026-10-28", 27976, 2074)


def test_same_day_value_is_replaced(conn, data_dir, fixtures):
    import_file(conn, fixtures / "vanguard_orders_pasted.txt", data_dir, account="Vanguard ISA A")
    record_value(conn, "Vanguard ISA A", "100", dt.date(2026, 10, 28))
    record_value(conn, "Vanguard ISA A", "200", dt.date(2026, 10, 28))
    assert conn.execute("SELECT value_pence FROM valuations").fetchall()[0][0] == 20000


def test_values_file_and_errors(conn, data_dir, fixtures, tmp_path):
    import_file(conn, fixtures / "starling_sample.csv", data_dir)
    import_file(conn, fixtures / "vanguard_orders_pasted.txt", data_dir, account="Vanguard ISA A")
    with pytest.raises(ValueError, match="bank account"):
        record_value(conn, "Starling Joint", "5")
    with pytest.raises(ValueError, match="No account called"):
        record_value(conn, "Vanguard ISA Z", "5")
    path = tmp_path / "values.csv"
    path.write_text("Date,Account,Value\n28/10/2026,Vanguard ISA A,\"1,234.56\"\n")
    assert import_values(conn, path) == 1
    assert isa_summaries(conn)[0].value_pence == 123456


def test_cli_value_and_status(tmp_path, fixtures, capsys):
    data = ["--data-dir", str(tmp_path / "d")]
    main(data + ["import", str(fixtures / "vanguard_orders_pasted.txt"), "--account", "Vanguard ISA A"])
    assert main(data + ["value", "Vanguard ISA A", "300.50", "--date", "28/10/2026"]) == 0
    assert main(data + ["value", "Nope", "1"]) == 1
    main(data + ["status"])
    out = capsys.readouterr().out
    assert "Vanguard ISA A: £300.50 on 2026-10-28, net invested £279.76, growth £20.74" in out
