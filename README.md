# BudgetBuddy

A private, local finance dashboard for a joint account: imports downloaded
Starling statements and Vanguard ISA exports, then (in later stages)
categorises spending, reviews expenditure and projects cash 12 months ahead.

Everything stays on your computer. There are no bank logins, no cloud
services and no network calls.

> The old Java Swing app (2012) is still in `src/` for reference. The new app is
> the `budgetbuddy` Python package.

## Setup on Windows

1. Install Python 3.11 or newer from python.org (tick "Add python.exe to PATH").
2. In PowerShell, from this folder:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Importing statements

**Starling (joint account):** in the app, Account > Statements > Export, choose
CSV and a date range.

**Vanguard (one per ISA):** on the website, My Account > Transactions >
Download, which gives an `.xlsx` spreadsheet.

```powershell
python -m budgetbuddy import "$HOME\Downloads\StarlingStatement_2026-09.csv"
python -m budgetbuddy import "$HOME\Downloads\Vanguard_A.xlsx" --account "Vanguard ISA A" --owner A
python -m budgetbuddy import "$HOME\Downloads\Vanguard_B.xlsx" --account "Vanguard ISA B" --owner B
python -m budgetbuddy status
```

You can also pass a folder, and every `.csv`/`.xlsx` inside is imported.

What the import does:

* **Detects the format** from the headers (use `--format starling|vanguard` to force it).
* **Archives the original file** in the data folder so the database can always be rebuilt.
* **Skips files already imported**, and in overlapping downloads skips the
  transactions already stored while keeping genuine repeats (two coffees on the same day).
* **Links transfers**: a Starling payment to Vanguard and the matching ISA
  deposit (same amount, up to 7 days apart) are paired and flagged, so money
  you invest is never counted as spending. Payments to Vanguard are flagged
  even before the ISA file is imported.

## Where your data lives

`C:\Users\<you>\BudgetBuddyData` by default (outside this repository):

* `budgetbuddy.db`: the SQLite database
* `raw\`: archived copies of every imported file

Set the `BUDGETBUDDY_DATA` environment variable or pass `--data-dir` to move it.
For encryption at rest, keep it on a BitLocker protected drive (an encrypted
database is planned). `.gitignore` blocks statements and databases from being
committed.

## Roadmap

1. ~~Import pipeline~~ (this stage)
2. Categorisation: merchant clean up, rules that learn from your corrections
3. Recurring payments and subscriptions
4. Dashboard (Streamlit, runs in your browser on your own machine)
5. Spending review and budgets
6. 12 month cash forecast with scenarios and lowest balance warning
7. ISA tracking: contributions against the £20,000 allowance per person per tax year

## Tests

```powershell
pytest
```

Test data in `tests/fixtures` is made up. Never put real statements there.
