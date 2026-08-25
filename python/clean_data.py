"""
Project 2: Personal Financial Intelligence System
Step 2 - Data cleaning & automatic categorization (Pandas)

Reads the messy raw transaction export and produces an analysis-ready CSV:
- standardizes date formats to YYYY-MM-DD
- parses amount strings ($ signs, stray whitespace, parenthesized credits) to floats
- derives a signed amount (negative = money out, positive = money in) from txn_type
- removes exact duplicate "double swipe" charges
- auto-categorizes every transaction into a clean merchant name + spending category
  using rule-based keyword matching against transaction descriptors (order matters -
  more specific patterns like "Amazon Prime" are checked before the generic "Amazon"
  pattern so a subscription doesn't get miscategorized as general shopping)

Output: data/clean/transactions.csv
"""

import re
import pandas as pd

RAW = "/home/claude/project2/data/raw"
CLEAN = "/home/claude/project2/data/clean"

# Ordered (regex, clean_merchant, category) rules - first match wins, so more
# specific patterns (subscriptions that share a brand with a general retailer)
# are listed before their broader counterparts.
CATEGORY_RULES = [
    (r"PAYROLL|DIRECT DEP", "Acme Corp Payroll", "Income"),
    (r"VENMO", "Venmo Transfer", "Transfer"),

    (r"STARBUCKS", "Starbucks", "Food and Restaurants"),
    (r"CHIPOTLE", "Chipotle", "Food and Restaurants"),
    (r"MCDONALD", "McDonald's", "Food and Restaurants"),
    (r"TRADER JOE", "Trader Joe's", "Food and Restaurants"),
    (r"WHOLEFDS|WHOLE FOODS", "Whole Foods Market", "Food and Restaurants"),
    (r"DOORDASH", "DoorDash", "Food and Restaurants"),
    (r"UBER\s*\*?EATS", "Uber Eats", "Food and Restaurants"),
    (r"LOCAL DINER", "Local Diner", "Food and Restaurants"),
    (r"CHICK[\s\-]?FIL[\s\-]?A|CHICKFILA", "Chick-fil-A", "Food and Restaurants"),

    (r"SKYLINE APT|SKYLINE APARTMENTS", "Skyline Apartments", "Rent and Housing"),
    (r"RENTERS\s*INS", "Renters Insurance Co", "Rent and Housing"),

    (r"\bUBER\b", "Uber", "Transportation"),
    (r"\bLYFT\b", "Lyft", "Transportation"),
    (r"SHELL", "Shell Gas Station", "Transportation"),
    (r"CHEVRON", "Chevron", "Transportation"),
    (r"CITY TRANSIT|CTA MONTHLY", "City Transit Authority", "Transportation"),
    (r"AUTOZONE", "AutoZone", "Transportation"),
    (r"PARKWHIZ", "ParkWhiz", "Transportation"),

    (r"PRIME VIDEO|AMAZON PRIME", "Amazon Prime", "Subscriptions"),
    (r"AMAZON|AMZN", "Amazon", "Shopping"),
    (r"\bTARGET\b", "Target", "Shopping"),
    (r"WAL-?MART", "Walmart", "Shopping"),
    (r"BEST\s*BUY|BESTBUY", "Best Buy", "Shopping"),
    (r"\bNIKE\b", "Nike", "Shopping"),
    (r"OLD\s*NAVY", "Old Navy", "Shopping"),

    (r"NETFLIX", "Netflix", "Subscriptions"),
    (r"SPOTIFY", "Spotify", "Subscriptions"),
    (r"ADOBE", "Adobe Creative Cloud", "Subscriptions"),
    (r"ANYTIME\s*FIT", "Anytime Fitness", "Subscriptions"),
    (r"APPLE\.COM/BILL|ICLOUD", "iCloud Storage", "Subscriptions"),
    (r"DISNEY", "Disney Plus", "Subscriptions"),
    (r"YOUTUBE\s*PREM", "YouTube Premium", "Subscriptions"),

    (r"PACIFIC\s*P(W|OW)R", "Pacific Power Electric", "Bills"),
    (r"METRO WATER", "Metro Water Utility", "Bills"),
    (r"COMCAST|XFINITY", "Comcast Xfinity", "Bills"),
    (r"VERIZON|VZWRLSS", "Verizon Wireless", "Bills"),
    (r"STATE\s*FARM", "State Farm Insurance", "Bills"),

    (r"DELTA AIR|DELTA\.COM", "Delta Airlines", "Travel"),
    (r"MARRIOTT", "Marriott Hotels", "Travel"),
    (r"AIRBNB", "Airbnb", "Travel"),
    (r"ENTERPRISE", "Enterprise Rent-A-Car", "Travel"),

    (r"FED.*STUDENT LOAN|FEDLOAN", "Federal Student Loan Servicer", "Education"),
    (r"UDEMY", "Udemy", "Education"),
    (r"COURSERA", "Coursera", "Education"),
]
COMPILED_RULES = [(re.compile(pat, re.IGNORECASE), merch, cat) for pat, merch, cat in CATEGORY_RULES]


def categorize(descriptor: str) -> tuple[str, str]:
    for pattern, merchant, category in COMPILED_RULES:
        if pattern.search(descriptor):
            return merchant, category
    return "Unknown Merchant", "Uncategorized"


def parse_amount(raw: str) -> float:
    s = str(raw).strip()
    is_paren_credit = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    s = s.replace("$", "").replace(",", "").strip()
    value = float(s)
    return value  # sign is derived from txn_type separately, not from parens


def parse_messy_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="mixed")


def main():
    df = pd.read_csv(f"{RAW}/transactions_raw.csv", dtype=str)

    df["description_raw"] = df["description_raw"].str.strip()
    df["account"] = df["account"].str.strip()
    df["date"] = parse_messy_date(df["date"])
    df["amount_abs"] = df["amount"].apply(parse_amount)

    # sign convention: money out (Purchase/Payment) is negative, money in
    # (Deposit/Refund/Transfer) is positive
    outflow_types = {"Purchase", "Payment"}
    df["amount"] = df.apply(
        lambda r: -r["amount_abs"] if r["txn_type"] in outflow_types else r["amount_abs"],
        axis=1,
    )
    df = df.drop(columns=["amount_abs"])

    cat_results = df["description_raw"].apply(categorize)
    df["merchant"] = cat_results.apply(lambda t: t[0])
    df["category"] = cat_results.apply(lambda t: t[1])

    # a handful of genuinely unlabeled POS transactions stay Uncategorized on purpose -
    # that's realistic and gets called out explicitly in the analysis, not silently dropped

    before = len(df)
    df = df.drop_duplicates(
        subset=["date", "account", "description_raw", "amount", "txn_type"]
    ).reset_index(drop=True)
    removed = before - len(df)

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_expense"] = df["amount"] < 0
    df["is_income"] = df["category"] == "Income"

    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(f"{CLEAN}/transactions.csv", index=False)

    print(f"Removed {removed} exact-duplicate transactions, {len(df)} remain")
    print("\nCategory breakdown:")
    print(df["category"].value_counts())
    n_uncat = (df["category"] == "Uncategorized").sum()
    print(f"\n{n_uncat} transactions ({n_uncat/len(df)*100:.1f}%) left Uncategorized (generic POS entries with no identifiable merchant)")


if __name__ == "__main__":
    main()
