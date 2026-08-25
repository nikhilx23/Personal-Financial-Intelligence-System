"""
Project 2: Personal Financial Intelligence System
Step 6 - Power BI package

Same approach as Project 1: Power BI Desktop (.pbix) is a proprietary format
only Power BI Desktop can save, so this produces an analysis-ready star schema
of CSVs plus a step-by-step guide (POWERBI_GUIDE.md) to load, model, and
recreate the dashboard with DAX.

Output: powerbi/*.csv (fact + dimension tables) and powerbi/POWERBI_GUIDE.md
"""

import pandas as pd

CLEAN = "/home/claude/project2/data/clean"
PBI = "/home/claude/project2/powerbi"


def main():
    txns = pd.read_csv(f"{CLEAN}/transactions.csv")

    dim_accounts = pd.DataFrame({"account_name": sorted(txns["account"].unique())})
    dim_accounts.insert(0, "account_id", range(1, len(dim_accounts) + 1))

    dim_categories = pd.DataFrame({"category_name": sorted(txns["category"].unique())})
    dim_categories.insert(0, "category_id", range(1, len(dim_categories) + 1))

    merchant_cat = txns[["merchant", "category"]].drop_duplicates()
    dim_merchants = merchant_cat.merge(dim_categories, left_on="category", right_on="category_name")
    dim_merchants = dim_merchants[["merchant", "category_id"]].rename(columns={"merchant": "merchant_name"})
    dim_merchants.insert(0, "merchant_id", range(1, len(dim_merchants) + 1))

    all_dates = pd.to_datetime(txns["date"])
    date_range = pd.date_range(all_dates.min(), all_dates.max(), freq="D")
    dim_date = pd.DataFrame({"date": date_range})
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.strftime("%B")
    dim_date["month_year"] = dim_date["date"].dt.strftime("%Y-%m")
    dim_date["day_of_week"] = dim_date["date"].dt.strftime("%A")
    dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5

    fact = txns.merge(dim_accounts, left_on="account", right_on="account_name")
    fact = fact.merge(dim_merchants, left_on="merchant", right_on="merchant_name")
    fact_transactions = fact[[
        "transaction_id", "date", "account_id", "merchant_id", "description_raw",
        "amount", "txn_type",
    ]]

    dim_accounts.to_csv(f"{PBI}/dim_accounts.csv", index=False)
    dim_categories.to_csv(f"{PBI}/dim_categories.csv", index=False)
    dim_merchants.to_csv(f"{PBI}/dim_merchants.csv", index=False)
    dim_date.to_csv(f"{PBI}/dim_date.csv", index=False)
    fact_transactions.to_csv(f"{PBI}/fact_transactions.csv", index=False)

    print("Power BI star-schema CSVs written to powerbi/:")
    for name, df in [("dim_accounts", dim_accounts), ("dim_categories", dim_categories),
                      ("dim_merchants", dim_merchants), ("dim_date", dim_date),
                      ("fact_transactions", fact_transactions)]:
        print(f"  {name}.csv  ({len(df)} rows)")


if __name__ == "__main__":
    main()
