# Project 2: Personal Financial Intelligence System

Every budget app promises to tell you where your money goes and then buries it in a feed you never open. This is my attempt at just answering the question directly: given a checking and credit card history, where is the money actually going, what's recurring that I forgot about, what looks off, and how much could I realistically save?

## The problem

Most people can guess roughly how much they spend a month. Almost nobody can tell you why it jumped last month, which merchant is quietly eating the most money, which subscriptions are still running, or which charges were genuinely unusual versus just normal noise.

## What's in this repo

```
project2/
├── data/
│   ├── raw/            Synthetic raw transaction export, intentionally messy
│   │                   (mixed date formats, $ signs, parenthesized credits,
│   │                   duplicate "double swipe" charges) to show real
│   │                   data cleaning, not a tidy toy dataset
│   └── clean/           Cleaned, categorized, analysis-ready CSV + anomalies.csv
├── python/
│   ├── generate_data.py     Builds the synthetic raw dataset (462 transactions)
│   ├── clean_data.py        Pandas cleaning + rule-based auto-categorization
│   ├── build_database.py    Loads the cleaned data into a normalized SQLite database
│   ├── analysis.py          Full analysis: 6 dashboard answers + all 4 advanced features
│   └── build_powerbi_package.py   Builds the Power BI star-schema CSVs
├── sql/
│   ├── schema.sql            Table definitions (accounts, categories, merchants, transactions)
│   ├── queries.sql           12 queries: aggregation, JOINs, date functions,
│   │                          window functions (LAG, RANK, PERCENT_RANK)
│   └── finances.db           The SQLite database itself
├── excel/
│   └── Financial_Dashboard.xlsx   PivotTable-ready data + a live formula
│                                   dashboard (SUMIFS, AVERAGEIFS, XLOOKUP) with charts
├── powerbi/
│   ├── dim_*.csv, fact_transactions.csv   Star-schema tables ready to import
│   └── POWERBI_GUIDE.md      Step-by-step Power Query, data model, and DAX guide
├── charts/
│   └── *.png                6 charts from the Python analysis
└── README.md                 This file
```

## How the data flows

```
generate_data.py → data/raw/  →  clean_data.py (clean + categorize)  →  data/clean/
                                                        │
                        ┌──────────────┬───────────────┼───────────────┐
                        ▼               ▼               ▼               ▼
                build_database.py   analysis.py   build_excel.py   build_powerbi_package.py
                        │               │               │               │
                        ▼               ▼               ▼               ▼
                sql/finances.db    charts/*.png   excel/*.xlsx    powerbi/*.csv
```

Transactions go in one end, get cleaned and categorized, then get fed to SQL, Python analysis, Excel, and Power BI in parallel — so the same numbers show up in all four places.

## Running it yourself

Needs Python 3.11+ with `pandas`, `numpy`, `matplotlib`, and `openpyxl`
(`pip install pandas numpy matplotlib openpyxl`).

```bash
cd project2
python3 python/generate_data.py          # 1. generate raw (messy) transactions
python3 python/clean_data.py             # 2. clean + auto-categorize
python3 python/build_database.py         # 3. load into SQLite
python3 python/analysis.py               # 4. run analysis, produce charts, print findings
python3 python/build_excel.py            # 5. build the Excel dashboard
python3 python/build_powerbi_package.py  # 6. build the Power BI CSV package
```

To query the database directly: `sqlite3 sql/finances.db < sql/queries.sql`

## Dashboard questions answered

| Question | Where it's answered | Result on this dataset |
|---|---|---|
| Where does most of my money go? | Excel Dashboard, SQL Q1, `charts/01_spending_by_category.png` | **Rent and Housing**, $10,279 total (30.0% of all spending) |
| Which categories increased this month? | SQL Q2, `charts/03_category_month_change.png` | Transportation +$142, Uncategorized +$136, Food and Restaurants +$87 (July vs. June) |
| Which merchants receive the most money? | Excel Dashboard, SQL Q3, `charts/04_top_merchants.png` | **Skyline Apartments**, $10,150 (rent) |
| What subscriptions am I paying for? | Excel Dashboard, SQL Q4/Q5, `charts/05_subscriptions.png` | 8 active subscriptions, **$168.42/month** ($2,021/year) |
| Which transactions look unusual? | SQL Q6, `charts/06_anomalies.png` | 4 flagged (z-score > 2 vs. that merchant's own history) — largest: $1,249 at Best Buy |
| How much could I potentially save? | SQL Q7, Python savings recommendations | $2,021/year from subscriptions alone, before touching any spending category |

## Advanced features

All four are implemented in `python/analysis.py`:

1. **Anomaly detection** — for every merchant with at least 3 transactions, flags any charge more than 2 standard deviations above that merchant's own average. Catches a genuinely odd purchase (a one-off $1,249 laptop at Best Buy, a $480 car repair) without flagging normal variation (a $46 gas fill-up isn't weird for Chevron just because it's more than a $5 coffee).
2. **Next-month spending forecast** — a linear trend over the complete months of history, projected one month out. With only ~6 months of data this is framed as directional, not a precise number, and the output says so. Comes out to roughly **$3,887** for the month after the data ends.
3. **Financial health score (0–100)** — four equally-weighted components (25 points each): savings rate, subscription burden as a percent of income, month-to-month spending consistency, and how often anomalies show up. Scores **40.2/100** here, mostly dragged down by a savings rate of -22.9% — expenses outpacing income by roughly $950/month on average, which is exactly the kind of thing this is supposed to catch early.
4. **Personalized savings recommendations** — pulled from the actual data instead of generic advice: which subscriptions to cut and what that saves per year, which flagged anomaly to look at first, and which spending category has the biggest lever for a percentage cut.

## Data note

The dataset (455 transactions across 7 months, 46 merchants) is synthetically generated (`generate_data.py`, fixed random seed), so the project runs with zero setup and nothing private ends up on GitHub. The raw data is deliberately messy on purpose — mixed date formats, inconsistent `$`/paren formatting, a few duplicate "double-swipe" charges, and some unlabeled "POS PURCHASE" entries that stay `Uncategorized` — so `clean_data.py` is doing real cleaning work instead of starting from data that's already tidy. Merchant frequency is weighted realistically too (small recurring purchases like coffee and rideshares versus rare big travel charges), so category totals land where they should — rent dominates the total the way it actually does, rather than a couple of plane tickets throwing everything off. To point this at real transactions, swap `data/raw/transactions_raw.csv` for your own bank or credit card export in the same column format, add any new merchant patterns to `CATEGORY_RULES` in `clean_data.py`, and rerun the pipeline.

## Skills demonstrated

- **Excel:** PivotTable-ready tables, XLOOKUP, SUMIFS/AVERAGEIFS/COUNTIFS, conditional formatting, native charts
- **SQL:** aggregation, JOINs, date functions (`strftime`), window functions (LAG, RANK, DENSE_RANK, PERCENT_RANK, running totals)
- **Python/Pandas:** cleaning, rule-based categorization, anomaly detection, linear-trend forecasting, composite scoring
- **Power BI:** star-schema data modeling, Power Query transformation steps, DAX measures (including time intelligence with `DATEADD`), dashboard/slicer design
- **Statistics:** z-scores for outlier detection, coefficient of variation, linear regression
