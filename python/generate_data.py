"""
Project 2: Personal Financial Intelligence System
Step 1 - Synthetic raw data generator

Generates realistic (and intentionally messy) raw bank/credit-card transaction data,
the way it actually looks exported from a bank: raw statement descriptors with
transaction codes and city/state suffixes, inconsistent amount formatting
(including parens for credits), mixed date formats, and a handful of duplicate
"double swipe" charges. clean_data.py turns this into an analysis-ready dataset
and auto-categorizes every transaction.

Output: data/raw/transactions_raw.csv
"""

import random
import csv
from datetime import date, timedelta

random.seed(7)

OUT = "/home/claude/project2/data/raw"
START_DATE = date(2026, 2, 1)
END_DATE = date(2026, 8, 15)

# (canonical merchant name, category, min amount, max amount, raw statement descriptor templates)
MERCHANTS = [
    ("Starbucks", "Food and Restaurants", 4.25, 8.75, ["SQ *STARBUCKS #{n} SEATTLE WA", "STARBUCKS #{n}", "SQ*STARBUCKS COFFEE"]),
    ("Chipotle", "Food and Restaurants", 9.50, 16.25, ["CHIPOTLE ONLINE {n}", "CHIPOTLE MEXICAN GRILL"]),
    ("McDonald's", "Food and Restaurants", 6.10, 13.90, ["MCDONALD'S F{n}", "MCDONALDS #{n}"]),
    ("Trader Joe's", "Food and Restaurants", 32.00, 112.00, ["TRADER JOE S #{n}", "TRADER JOES {n}"]),
    ("Whole Foods Market", "Food and Restaurants", 38.00, 138.00, ["WHOLEFDS MKT #{n}", "WHOLE FOODS MARKET"]),
    ("DoorDash", "Food and Restaurants", 17.50, 46.00, ["DOORDASH*{n}", "DD *DOORDASH"]),
    ("Uber Eats", "Food and Restaurants", 14.00, 41.00, ["UBER *EATS", "UBER EATS {n}"]),
    ("Local Diner", "Food and Restaurants", 11.50, 29.00, ["THE LOCAL DINER", "LOCAL DINER #{n}"]),
    ("Chick-fil-A", "Food and Restaurants", 7.25, 15.50, ["CHICK-FIL-A #{n}", "CHICKFILA {n}"]),

    ("Skyline Apartments", "Rent and Housing", 1450.00, 1450.00, ["SKYLINE APT PAYMENT", "SKYLINE APARTMENTS RENT"]),
    ("Renters Insurance Co", "Rent and Housing", 18.40, 18.40, ["RENTERS INS PREMIUM", "RENTERSINS CO {n}"]),

    ("Uber", "Transportation", 8.20, 32.00, ["UBER   TRIP {n}", "UBER *TRIP HELP.UBER.COM"]),
    ("Lyft", "Transportation", 9.10, 28.50, ["LYFT *RIDE {n}", "LYFT   RIDE TUE"]),
    ("Shell Gas Station", "Transportation", 30.00, 65.00, ["SHELL OIL {n}", "SHELL SERVICE STATION"]),
    ("Chevron", "Transportation", 28.00, 60.00, ["CHEVRON {n}", "CHEVRON/TEXACO {n}"]),
    ("City Transit Authority", "Transportation", 60.00, 60.00, ["CITY TRANSIT AUTHORITY", "CTA MONTHLY PASS"]),
    ("AutoZone", "Transportation", 15.00, 92.00, ["AUTOZONE #{n}", "AUTOZONE INC"]),
    ("ParkWhiz", "Transportation", 5.50, 21.00, ["PARKWHIZ *PARKING", "PARKWHIZ {n}"]),

    ("Amazon", "Shopping", 12.00, 185.00, ["AMAZON.COM*{n} AMZN.COM/BILL WA", "AMZN MKTP US*{n}"]),
    ("Target", "Shopping", 20.00, 145.00, ["TARGET      #{n}", "TARGET.COM *{n}"]),
    ("Walmart", "Shopping", 15.00, 120.00, ["WAL-MART #{n}", "WALMART.COM {n}"]),
    ("Best Buy", "Shopping", 25.00, 360.00, ["BEST BUY #{n}", "BESTBUY.COM {n}"]),
    ("Nike", "Shopping", 40.00, 155.00, ["NIKE.COM {n}", "NIKE STORE #{n}"]),
    ("Old Navy", "Shopping", 20.00, 92.00, ["OLD NAVY #{n}", "OLDNAVY.COM"]),

    ("Netflix", "Subscriptions", 15.49, 15.49, ["NETFLIX.COM", "NETFLIX.COM   LOS GATOS CA"]),
    ("Spotify", "Subscriptions", 11.99, 11.99, ["SPOTIFY USA", "SPOTIFY   P{n}"]),
    ("Amazon Prime", "Subscriptions", 14.99, 14.99, ["PRIME VIDEO CHANNELS", "AMAZON PRIME*{n}"]),
    ("Adobe Creative Cloud", "Subscriptions", 54.99, 54.99, ["ADOBE  *CREATIVE CLOUD", "ADOBE CREATIVE CL"]),
    ("Anytime Fitness", "Subscriptions", 39.99, 39.99, ["ANYTIME FITNESS #{n}", "ANYTIMEFIT MEMBERSHIP"]),
    ("iCloud Storage", "Subscriptions", 2.99, 2.99, ["APPLE.COM/BILL", "ICLOUD STORAGE"]),
    ("Disney Plus", "Subscriptions", 13.99, 13.99, ["DISNEY PLUS", "DISNEYPLUS.COM"]),
    ("YouTube Premium", "Subscriptions", 13.99, 13.99, ["YOUTUBEPREMIUM", "GOOGLE *YOUTUBE PREM"]),

    ("Pacific Power Electric", "Bills", 64.00, 148.00, ["PACIFIC PWR ELEC BILL", "PACIFIC POWER {n}"]),
    ("Metro Water Utility", "Bills", 29.00, 58.00, ["METRO WATER UTIL", "METRO WATER {n}"]),
    ("Comcast Xfinity", "Bills", 79.99, 79.99, ["COMCAST CABLE COMM", "XFINITY {n}"]),
    ("Verizon Wireless", "Bills", 85.00, 85.00, ["VERIZON WIRELESS PMT", "VZWRLSS*{n}"]),
    ("State Farm Insurance", "Bills", 120.00, 120.00, ["STATE FARM INS", "STATEFARM {n}"]),

    ("Delta Airlines", "Travel", 180.00, 540.00, ["DELTA AIR {n}", "DELTA.COM {n}"]),
    ("Marriott Hotels", "Travel", 140.00, 420.00, ["MARRIOTT {n}", "MARRIOTT HOTELS #{n}"]),
    ("Airbnb", "Travel", 95.00, 380.00, ["AIRBNB   HMXY{n}", "AIRBNB * HMXY{n}"]),
    ("Enterprise Rent-A-Car", "Travel", 55.00, 220.00, ["ENTERPRISE RENT-A-CAR", "ENTERPRISE RAC #{n}"]),

    ("Federal Student Loan Servicer", "Education", 210.00, 210.00, ["FED STUDENT LOAN SVC", "FEDLOAN SERVICING"]),
    ("Udemy", "Education", 13.99, 84.99, ["UDEMY *ONLINE COURSE", "UDEMY.COM {n}"]),
    ("Coursera", "Education", 49.00, 49.00, ["COURSERA {n}", "COURSERA.ORG"]),
]

RECURRING_MONTHLY = [
    "Skyline Apartments", "Renters Insurance Co", "City Transit Authority",
    "Netflix", "Spotify", "Amazon Prime", "Adobe Creative Cloud", "Anytime Fitness",
    "iCloud Storage", "Disney Plus", "YouTube Premium", "Pacific Power Electric",
    "Metro Water Utility", "Comcast Xfinity", "Verizon Wireless", "State Farm Insurance",
    "Federal Student Loan Servicer",
]

NONRECURRING = [m for m in MERCHANTS if m[0] not in RECURRING_MONTHLY]
MERCHANT_LOOKUP = {m[0]: m for m in MERCHANTS}

# Realistic selection weights per category - frequent small purchases (food,
# transportation) should dominate transaction COUNT, while rare big-ticket
# categories (travel especially) should appear only occasionally, not compete
# with daily coffee runs on equal footing. Without this, uniform random
# selection makes "Travel" the largest spending category overall, which
# doesn't match how anyone's actual budget looks.
CATEGORY_WEIGHTS = {
    "Food and Restaurants": 3.2,
    "Transportation": 2.4,
    "Shopping": 1.6,
    "Education": 0.35,
    "Travel": 0.22,
}
NONRECURRING_WEIGHTS = [CATEGORY_WEIGHTS[m[1]] for m in NONRECURRING]

ANOMALIES = [
    # (merchant, amount, description)
    ("Best Buy", 1249.00, "one-off laptop replacement"),
    ("Delta Airlines", 612.00, "last-minute flight"),
    ("AutoZone", 480.00, "unexpected car repair"),
    ("Marriott Hotels", 540.00, "extended stay"),
    ("Amazon", 340.00, "large one-time purchase"),
]


def daterange_days(start, end):
    return (end - start).days


def messy_date(d: date) -> str:
    fmt = random.choice(["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y"])
    return d.strftime(fmt)


def messy_amount(amount: float, is_credit: bool = False) -> str:
    """Bank exports mix plain, dollar-signed, and parenthesized-credit formats."""
    r = random.random()
    if is_credit:
        # credits/refunds are typically POSITIVE inflows; sometimes shown in parens by convention
        if r < 0.3:
            return f"(${amount:,.2f})"
        return f"{amount:,.2f}"
    if r < 0.15:
        return f"${amount:,.2f}"
    if r < 0.20:
        return f" {amount:,.2f} "
    return f"{amount:.2f}"


def random_day_in_month(year, month, day_hint=None):
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    day = day_hint if day_hint and day_hint <= last_day else random.randint(1, last_day)
    return date(year, month, day)


def month_iter(start, end):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def main():
    rows = []
    txn_counter = 1000
    account_choices = ["Checking ...4821", "Credit Card ...9033"]

    recurring_day = {name: random.randint(1, 27) for name in RECURRING_MONTHLY}

    for year, month in month_iter(START_DATE, END_DATE):
        # --- recurring monthly bills / subscriptions ---
        for name in RECURRING_MONTHLY:
            merchant, category, lo, hi, templates = MERCHANT_LOOKUP[name]
            d = random_day_in_month(year, month, recurring_day[name])
            if d < START_DATE or d > END_DATE:
                continue
            amount = round(random.uniform(lo, hi), 2) if lo != hi else lo
            # utilities vary a little month to month; fixed-fee subs/rent do not
            if name in ("Pacific Power Electric", "Metro Water Utility"):
                amount = round(random.uniform(lo, hi), 2)
            txn_counter += 1
            descriptor = random.choice(templates).format(n=random.randint(100, 999))
            rows.append({
                "transaction_id": f"TXN{txn_counter}",
                "date": messy_date(d),
                "account": random.choice(account_choices),
                "description_raw": descriptor,
                "amount": messy_amount(amount),
                "txn_type": "Payment",
            })

        # --- everyday discretionary spending (variable count per month) ---
        n_txns = random.randint(38, 55)
        for _ in range(n_txns):
            merchant, category, lo, hi, templates = random.choices(NONRECURRING, weights=NONRECURRING_WEIGHTS, k=1)[0]
            d = date(year, month, random.randint(1, 28))
            if d < START_DATE or d > END_DATE:
                continue
            amount = round(random.uniform(lo, hi), 2)
            txn_counter += 1
            descriptor = random.choice(templates).format(n=random.randint(100, 999))
            rows.append({
                "transaction_id": f"TXN{txn_counter}",
                "date": messy_date(d),
                "account": random.choice(account_choices),
                "description_raw": descriptor,
                "amount": messy_amount(amount),
                "txn_type": "Purchase",
            })

        # --- paycheck income (biweekly-ish: twice a month) ---
        for pay_day in (random.randint(1, 14), random.randint(15, 28)):
            d = date(year, month, pay_day)
            if d < START_DATE or d > END_DATE:
                continue
            txn_counter += 1
            rows.append({
                "transaction_id": f"TXN{txn_counter}",
                "date": messy_date(d),
                "account": "Checking ...4821",
                "description_raw": random.choice(["ACME CORP PAYROLL DEP", "ACME CORP DIRECT DEP"]),
                "amount": messy_amount(round(random.uniform(1980, 2120), 2)),
                "txn_type": "Deposit",
            })

        # --- occasional Venmo / e-transfer inflow ---
        if random.random() < 0.4:
            d = date(year, month, random.randint(1, 28))
            if START_DATE <= d <= END_DATE:
                txn_counter += 1
                rows.append({
                    "transaction_id": f"TXN{txn_counter}",
                    "date": messy_date(d),
                    "account": "Checking ...4821",
                    "description_raw": "VENMO   TRANSFER IN",
                    "amount": messy_amount(round(random.uniform(20, 140), 2)),
                    "txn_type": "Transfer",
                })

        # --- occasional refund/credit ---
        if random.random() < 0.25:
            d = date(year, month, random.randint(1, 28))
            if START_DATE <= d <= END_DATE:
                txn_counter += 1
                rows.append({
                    "transaction_id": f"TXN{txn_counter}",
                    "date": messy_date(d),
                    "account": random.choice(account_choices),
                    "description_raw": "AMAZON.COM REFUND",
                    "amount": messy_amount(round(random.uniform(10, 60), 2), is_credit=True),
                    "txn_type": "Refund",
                })

        # --- a couple of unlabeled generic POS transactions (uncategorizable on purpose) ---
        for _ in range(random.randint(0, 2)):
            d = date(year, month, random.randint(1, 28))
            if START_DATE <= d <= END_DATE:
                txn_counter += 1
                rows.append({
                    "transaction_id": f"TXN{txn_counter}",
                    "date": messy_date(d),
                    "account": random.choice(account_choices),
                    "description_raw": random.choice(["POS PURCHASE", "DEBIT CARD PURCHASE", "MISC MERCHANT {}".format(random.randint(1000,9999))]),
                    "amount": messy_amount(round(random.uniform(8, 60), 2)),
                    "txn_type": "Purchase",
                })

    # --- inject anomalies, one per a handful of distinct months ---
    anomaly_months = random.sample(list(month_iter(START_DATE, END_DATE)), k=min(5, len(list(month_iter(START_DATE, END_DATE)))))
    for (year, month), (name, amount, _note) in zip(anomaly_months, ANOMALIES):
        merchant, category, lo, hi, templates = MERCHANT_LOOKUP[name]
        d = date(year, month, random.randint(1, 28))
        if not (START_DATE <= d <= END_DATE):
            continue
        txn_counter += 1
        descriptor = random.choice(templates).format(n=random.randint(100, 999))
        rows.append({
            "transaction_id": f"TXN{txn_counter}",
            "date": messy_date(d),
            "account": random.choice(account_choices),
            "description_raw": descriptor,
            "amount": messy_amount(amount),
            "txn_type": "Purchase",
        })

    # --- inject a handful of exact duplicate charges ("double swipe") ---
    for _ in range(7):
        dup = dict(random.choice(rows))
        rows.append(dup)

    random.shuffle(rows)

    with open(f"{OUT}/transactions_raw.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["transaction_id", "date", "account", "description_raw", "amount", "txn_type"])
        w.writeheader()
        w.writerows(rows)

    print(f"Generated {len(rows)} raw transaction rows -> {OUT}/transactions_raw.csv")


if __name__ == "__main__":
    main()
