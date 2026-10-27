import pytest

from budgetbuddy.cli import main
from budgetbuddy.importer import import_file


def _count(conn, sql="SELECT COUNT(*) FROM transactions"):
    return conn.execute(sql).fetchone()[0]


def test_import_and_archive(conn, data_dir, fixtures):
    r = import_file(conn, fixtures / "starling_sample.csv", data_dir)
    assert r.account == "Starling Joint" and r.rows_added == 8
    assert len(list((data_dir / "raw" / "starling").iterdir())) == 1


def test_same_file_twice_is_skipped(conn, data_dir, fixtures):
    import_file(conn, fixtures / "starling_sample.csv", data_dir)
    again = import_file(conn, fixtures / "starling_sample.csv", data_dir)
    assert again.skipped_file
    assert _count(conn) == 8


def test_overlapping_export_keeps_genuine_repeats(conn, data_dir, fixtures):
    import_file(conn, fixtures / "starling_sample.csv", data_dir)
    r = import_file(conn, fixtures / "starling_overlap.csv", data_dir)
    # Energy bill already stored; Netflix new; the third Costa on a new day is new
    assert (r.rows_added, r.duplicates) == (2, 1)
    assert _count(conn) == 10
    costas = _count(conn, "SELECT COUNT(*) FROM transactions WHERE counterparty = 'Costa Coffee'")
    assert costas == 3


def test_vanguard_needs_account_name(conn, data_dir, fixtures):
    with pytest.raises(ValueError, match="--account"):
        import_file(conn, fixtures / "vanguard_isa_a.csv", data_dir)


def test_transfers_are_linked(conn, data_dir, fixtures):
    import_file(conn, fixtures / "starling_sample.csv", data_dir)
    # Before the ISA file arrives, Vanguard payments are already flagged as transfers
    assert _count(conn, "SELECT COUNT(*) FROM transactions WHERE is_transfer = 1") == 2

    r = import_file(conn, fixtures / "vanguard_isa_a.csv", data_dir, account="Vanguard ISA A", owner="A")
    assert r.transfers_linked == 1
    groups = conn.execute(
        "SELECT a.name, t.amount_pence FROM transactions t JOIN accounts a ON a.id = t.account_id"
        " WHERE t.transfer_group IS NOT NULL ORDER BY t.amount_pence"
    ).fetchall()
    assert [tuple(g) for g in groups] == [("Starling Joint", -50000), ("Vanguard ISA A", 50000)]
    # The £300 payment (the other person's ISA, not imported yet) stays a flagged, unpaired transfer
    unpaired = conn.execute(
        "SELECT amount_pence FROM transactions WHERE is_transfer = 1 AND transfer_group IS NULL"
    ).fetchall()
    assert [u[0] for u in unpaired] == [-30000]
    assert _count(conn, "SELECT COUNT(*) FROM investment_trades") == 1


def test_cli_import_folder_and_status(tmp_path, fixtures, capsys):
    data = tmp_path / "cli-data"
    assert main(["--data-dir", str(data), "import", str(fixtures / "starling_sample.csv")]) == 0
    assert main(["--data-dir", str(data), "status"]) == 0
    out = capsys.readouterr().out
    assert "Starling Joint" in out and "8 cash transactions" in out and "£4,118.38" in out
