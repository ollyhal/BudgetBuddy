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

**Vanguard (one per ISA):** log in on a laptop and open the orders list.
Select the whole table (from the "Investment" heading to the last row), copy
it, paste it into Notepad and save it as a `.txt` file, one per ISA. Only
completed orders are imported; pending ones are picked up next time you
paste. If Vanguard ever offers a spreadsheet download, that works too.

```powershell
python -m budgetbuddy import "$HOME\Downloads\StarlingStatement_2026-09.csv"
python -m budgetbuddy import "$HOME\Documents\vanguard_a_orders.txt" --account "Vanguard ISA A" --owner A
python -m budgetbuddy import "$HOME\Documents\vanguard_b_orders.txt" --account "Vanguard ISA B" --owner B
python -m budgetbuddy status
```

Pasting the full list each time is fine: orders already stored are skipped.

You can also pass a folder, and every `.csv`/`.txt`/`.xlsx` inside is imported.

What the import does:

* **Detects the format** from the headers (use `--format` to force one).
* **Archives the original file** in the data folder so the database can always be rebuilt.
* **Skips files already imported**, and in overlapping downloads skips the
  transactions already stored while keeping genuine repeats (two coffees on the same day).
* **Links transfers**: a Starling payment to Vanguard and the matching ISA
  deposit (same amount, up to 7 days apart) are paired and flagged, so money
  you invest is never counted as spending. Payments to Vanguard are flagged
  even before the ISA file is imported.

## ISA values

The orders list shows what you bought, not what it is worth. Once a month,
copy each ISA's value from the Vanguard summary page:

```powershell
python -m budgetbuddy value "Vanguard ISA A" 12450.00
python -m budgetbuddy value "Vanguard ISA B" 9800.00 --date 31/10/2026
```

Or keep a file with `Date,Account,Value` columns and run
`python -m budgetbuddy value --file values.csv`. `status` then shows each
ISA's value, net invested (buys less sells) and growth.

## Categories

Every Starling transaction gets a clean merchant name and a category when it
is imported, chosen in this order:

1. **Transfers** to your ISAs (never counted as spending)
2. A category you set on one transaction with `recategorise`
3. **Your rules**, which always beat the built in ones
4. Built in keywords (Tesco is Groceries, Netflix is Subscriptions, ...)
5. Starling's own Spending Category
6. Otherwise money in is Income and money out is Uncategorised

```powershell
python -m budgetbuddy uncategorised                         # what needs a category, biggest first
python -m budgetbuddy rule "Premier Vet Alliance" Pets      # this merchant, now and in future
python -m budgetbuddy rule --contains "uber" Transport      # any payee or reference containing it
python -m budgetbuddy rule                                  # list your rules
python -m budgetbuddy rule --delete 3
python -m budgetbuddy transactions --month 2026-10 --search amazon
python -m budgetbuddy recategorise 42 Holidays              # just this one transaction
python -m budgetbuddy spending --month 2026-10
```

You can invent your own categories; anything not in the standard list is
created the first time you use it.

## Recurring payments

After each import BudgetBuddy looks for income and payments that arrive at a
steady interval (weekly, fortnightly, four weekly, monthly, quarterly,
yearly): salaries, direct debits, subscriptions and ISA standing orders.
These feed the 12 month forecast.

```powershell
python -m budgetbuddy recurring
```

lists them grouped as Income, Bills, Subscriptions and Savings & ISAs, with
the monthly totals, what is left for everyday spending, price rises, and
anything that has stopped appearing (probably cancelled).

* Payments that vary (energy, water) use the average of the last three.
* Three payments are needed, or two for a direct debit or standing order.
* Your changes are kept when detection runs again:

```powershell
python -m budgetbuddy recurring end 6          # cancelled, leave it out of the forecast
python -m budgetbuddy recurring ignore 4       # not really a regular payment
python -m budgetbuddy recurring restore 4
python -m budgetbuddy recurring amount 3 200   # use your own figure
python -m budgetbuddy recurring add "Car insurance" 650 --every yearly --next 15/03/2027 --category Insurance
python -m budgetbuddy recurring add "Bonus" 1500 --income --every yearly --next 31/03/2027
```

## Dashboard

```powershell
python -m budgetbuddy dashboard
```

opens the dashboard in your browser at a `localhost` address. It runs only on
your computer; close it with Ctrl+C in PowerShell. Tabs:

* **Overview**: joint balance, ISA total, this month's spending against the
  3 month average, regular income, and money in, spent and saved each month
* **Spending**: categories over time, the chosen month by category, biggest merchants
* **Regular payments**: everything `recurring` found, price changes, cancelled items
* **ISAs**: value, net invested and growth for each ISA
* **Needs a category**: the review queue
* **Forecast**: coming next

## Where your data lives

`C:\Users\<you>\BudgetBuddyData` by default (outside this repository):

* `budgetbuddy.db`: the SQLite database
* `raw\`: archived copies of every imported file

Set the `BUDGETBUDDY_DATA` environment variable or pass `--data-dir` to move it.
For encryption at rest, keep it on a BitLocker protected drive (an encrypted
database is planned). `.gitignore` blocks statements and databases from being
committed.

## Roadmap

1. ~~Import pipeline~~
2. ~~Categorisation and ISA values~~
3. ~~Recurring payments and subscriptions~~
4. ~~Dashboard (Streamlit, runs in your browser on your own machine)~~
5. Spending review and budgets
6. 12 month cash forecast with scenarios and lowest balance warning
7. ISA tracking: contributions against the £20,000 allowance per person per tax year

## Tests

```powershell
pytest
```

Test data in `tests/fixtures` is made up. Never put real statements there.
