# Power BI Guide — Personal Financial Intelligence System

As with Project 1, Power BI Desktop files (`.pbix`) are a proprietary binary
format only Power BI Desktop itself can save. This folder gives you the same
star schema Power BI would build from the raw data, plus the exact steps to
load it, model it, and recreate every KPI, chart, and drill-down.

## 1. Files in this folder

| File | Type | Description |
|---|---|---|
| `fact_transactions.csv` | Fact table | One row per transaction (455 rows), signed amount (negative = spend, positive = income) |
| `dim_accounts.csv` | Dimension | Checking / Credit Card lookup |
| `dim_categories.csv` | Dimension | The 8 spending categories + Income/Transfer/Uncategorized |
| `dim_merchants.csv` | Dimension | Every merchant, linked to its category |
| `dim_date.csv` | Dimension | One row per calendar day, for time intelligence |

## 2. Load the data (Power Query)

1. **Get Data → Folder**, point at this `powerbi/` folder, **Combine &
   Transform** to bring in all 5 CSVs at once (or import each with
   **Text/CSV** individually).
2. Set data types: `date` → **Date**; `amount` → **Decimal Number**;
   `is_weekend` → **True/False**.
3. Mark `dim_date` as a **Date table** (Table tools → Mark as Date Table →
   `date`).
4. **Close & Apply**.

## 3. Build the data model (relationships)

```
dim_accounts   (1) ───< account_id  >─── (many) fact_transactions
dim_merchants  (1) ───< merchant_id >─── (many) fact_transactions
dim_date       (1) ───< date        >─── (many) fact_transactions
dim_categories (1) ───< category_id >─── (many) dim_merchants
```

All one-to-many, filtering from the "1" side. `dim_categories` connects to
the fact table indirectly through `dim_merchants` — Power BI will propagate
the filter automatically as long as the relationship direction is "Both" on
the `dim_merchants → dim_categories` link, or you can flatten `category_name`
directly onto `dim_merchants` for simplicity (already included in this
export via the join, so either approach works).

## 4. DAX measures

Create a `_Measures` table (Model view → New Table →
`_Measures = ROW("x", 0)`, hide the `x` column), then add:

```dax
Total Income =
CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[amount] > 0 )

Total Expenses =
CALCULATE ( SUM ( fact_transactions[amount] ) * -1, fact_transactions[amount] < 0 )

Net =
[Total Income] - [Total Expenses]

Savings Rate % =
DIVIDE ( [Net], [Total Income] )

Biggest Category =
VAR CategorySpend =
    ADDCOLUMNS (
        VALUES ( dim_categories[category_name] ),
        "Spend", CALCULATE ( [Total Expenses] )
    )
RETURN
    MAXX ( TOPN ( 1, CategorySpend, [Spend], DESC ), dim_categories[category_name] )

Monthly Subscription Cost =
CALCULATE (
    [Total Expenses] / DISTINCTCOUNT ( dim_date[month_year] ),
    dim_categories[category_name] = "Subscriptions"
)

Category Spend (Prior Month) =
CALCULATE ( [Total Expenses], DATEADD ( dim_date[date], -1, MONTH ) )

Category Change vs Prior Month =
[Total Expenses] - [Category Spend (Prior Month)]

Merchant Avg Transaction =
AVERAGE ( fact_transactions[amount] ) * -1

Merchant Std Dev =
CALCULATE (
    STDEVX.P ( fact_transactions, fact_transactions[amount] * -1 )
)

Is Anomaly (z > 2) =
VAR CurrentAmount = SELECTEDVALUE ( fact_transactions[amount] ) * -1
VAR MerchantAvg = [Merchant Avg Transaction]
VAR MerchantStd = [Merchant Std Dev]
RETURN
    IF ( MerchantStd > 0 && DIVIDE ( CurrentAmount - MerchantAvg, MerchantStd ) > 2, TRUE, FALSE )

Financial Health Score =
VAR SavingsScore = MIN ( 25, MAX ( 0, DIVIDE ( [Savings Rate %], 0.20 ) * 25 ) )
VAR SubBurden = DIVIDE ( [Monthly Subscription Cost], DIVIDE ( [Total Income], 7 ) )
VAR SubScore = MIN ( 25, MAX ( 0, 25 - DIVIDE ( SubBurden, 0.05 ) * 25 ) )
RETURN
    SavingsScore + SubScore   -- extend with consistency + anomaly components as in python/analysis.py
```

## 5. Recreate the dashboard visuals

| Visual | Type | Fields |
|---|---|---|
| Total Income, Total Expenses, Net, Savings Rate % | Card | one measure per card |
| Spending by Category | Bar chart | Axis: `dim_categories[category_name]`; Values: `[Total Expenses]` |
| Monthly Income vs. Expenses | Line and clustered column | Axis: `dim_date[month_year]`; Columns: `[Total Income]`, `[Total Expenses]` |
| Category Change (This Month vs. Last) | Bar chart (diverging) | Axis: `dim_categories[category_name]`; Values: `[Category Change vs Prior Month]` |
| Top Merchants | Bar chart | Axis: `dim_merchants[merchant_name]`; Values: `[Total Expenses]`, Top N filter = 10 |
| Active Subscriptions | Table | `dim_merchants[merchant_name]` filtered to Subscriptions, `[Merchant Avg Transaction]` |
| Unusual Transactions | Table | `fact_transactions` filtered where `[Is Anomaly (z > 2)]` = TRUE |

Add slicers for `dim_date[month_year]`, `dim_categories[category_name]`, and
`dim_accounts[account_name]` at the top of the page for the interactive
drill-downs the project brief calls for — clicking a category slices every
visual on the page down to that category's merchants and monthly trend.

## 6. Advanced features in Power BI vs. Python

The next-month forecast and the full four-component financial health score
are built in `python/analysis.py` because they need a bit more control (a
floored linear regression, a transparent weighted score) than DAX measures
comfortably express inline. Power BI can still show forecasts natively:
select the monthly expense line chart → **Analytics** pane → **Forecast** →
set a few periods forward, which uses exponential smoothing on the same
monthly totals.
