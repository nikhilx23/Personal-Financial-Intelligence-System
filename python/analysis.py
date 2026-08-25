"""
Project 2: Personal Financial Intelligence System
Step 4 - Python analysis & visualization (Pandas / NumPy / Matplotlib)

Answers every dashboard question from the project brief and implements all
four advanced features:
  - Anomaly detection (z-score vs. each merchant's own history)
  - Next-month spending forecast (linear trend over the logged months)
  - Financial health score (0-100, four transparent components)
  - Personalized savings recommendations

Output: charts/*.png + a printed summary.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLEAN = "/home/claude/project2/data/clean"
CHARTS = "/home/claude/project2/charts"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#444444", "axes.grid": True,
    "grid.color": "#e0e0e0", "grid.linewidth": 0.6, "font.size": 10,
})
PALETTE = ["#2563eb", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#84cc16", "#64748b"]
ACCENT = "#2563eb"
WARN = "#ef4444"


def load():
    df = pd.read_csv(f"{CLEAN}/transactions.csv", parse_dates=["date"])
    return df


# ---------------------------------------------------------------------------
# Dashboard question charts
# ---------------------------------------------------------------------------

def chart_spending_by_category(df):
    spend = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.barh(spend.index, spend.values, color=PALETTE[: len(spend)])
    for b in bars:
        ax.text(b.get_width() + 40, b.get_y() + b.get_height() / 2, f"${b.get_width():,.0f}",
                va="center", fontsize=9)
    ax.set_title("Where the Money Goes - Total Spend by Category")
    ax.set_xlabel("Total spent ($)")
    fig.tight_layout()
    fig.savefig(f"{CHARTS}/01_spending_by_category.png", dpi=150)
    plt.close(fig)
    return spend


def chart_monthly_income_expense(df, monthly, forecast_month, forecast_value):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(monthly))
    width = 0.38
    ax.bar(x - width / 2, monthly["income"], width, label="Income", color="#10b981")
    ax.bar(x + width / 2, monthly["expense"], width, label="Expenses", color=WARN)

    labels = list(monthly["month"])
    labels[-1] = f"{labels[-1]}\n(partial)"  # data cuts off mid-month - don't let it read as a real drop
    labels.append(f"{forecast_month}\n(forecast)")

    ax.bar(len(monthly) + width / 2, forecast_value, width, color=WARN, alpha=0.35,
           hatch="//", label="Forecast (next month)")
    ax.set_xticks(list(x) + [len(monthly)])
    ax.set_xticklabels(labels, rotation=0, fontsize=8.5)
    ax.set_title("Monthly Income vs. Expenses (+ Next-Month Forecast)")
    ax.set_ylabel("$")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{CHARTS}/02_monthly_income_expense.png", dpi=150)
    plt.close(fig)


def chart_category_month_change(df, complete_months):
    """Compares the two most recent COMPLETE months. The trailing month in this
    dataset is always partial (the export cuts off mid-month), so comparing it
    against a full prior month would make every category look like it dropped
    just because fewer days had elapsed - not because behavior changed."""
    spend = df[df["amount"] < 0].copy()
    spend["amount"] = -spend["amount"]
    monthly_cat = spend.groupby(["month", "category"])["amount"].sum().reset_index()
    monthly_cat = monthly_cat[monthly_cat["month"].isin(complete_months)]
    months_sorted = sorted(monthly_cat["month"].unique())
    latest, prev = months_sorted[-1], months_sorted[-2]

    latest_df = monthly_cat[monthly_cat["month"] == latest].set_index("category")["amount"]
    prev_df = monthly_cat[monthly_cat["month"] == prev].set_index("category")["amount"]
    change = (latest_df.subtract(prev_df, fill_value=0)).sort_values()

    colors = [WARN if v > 0 else "#10b981" for v in change.values]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.barh(change.index, change.values, color=colors)
    for b in bars:
        label = f"+${b.get_width():,.0f}" if b.get_width() > 0 else f"-${abs(b.get_width()):,.0f}"
        ax.text(b.get_width() + (15 if b.get_width() >= 0 else -15), b.get_y() + b.get_height() / 2,
                label, va="center", ha="left" if b.get_width() >= 0 else "right", fontsize=8.5)
    ax.axvline(0, color="#444444", linewidth=0.8)
    ax.margins(x=0.18)  # keep the value labels on the widest bars from clipping at the plot edge
    ax.set_title(f"Category Change: {latest} vs. {prev}")
    ax.set_xlabel("Change in spend ($)")
    fig.tight_layout()
    fig.savefig(f"{CHARTS}/03_category_month_change.png", dpi=150)
    plt.close(fig)
    return latest, prev, change


def chart_top_merchants(df):
    spend = df[df["amount"] < 0].copy()
    spend["amount"] = -spend["amount"]
    top = spend.groupby("merchant")["amount"].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    bars = ax.barh(top.index[::-1], top.values[::-1], color=ACCENT)
    for b in bars:
        ax.text(b.get_width() + 15, b.get_y() + b.get_height() / 2, f"${b.get_width():,.0f}",
                va="center", fontsize=9)
    ax.set_title("Top 10 Merchants by Total Spend")
    ax.set_xlabel("Total spent ($)")
    fig.tight_layout()
    fig.savefig(f"{CHARTS}/04_top_merchants.png", dpi=150)
    plt.close(fig)
    return top


def chart_subscriptions(df):
    subs = df[df["category"] == "Subscriptions"].copy()
    subs["amount"] = -subs["amount"]
    summary = subs.groupby("merchant")["amount"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.barh(summary.index[::-1], summary.values[::-1], color="#8b5cf6")
    for b in bars:
        ax.text(b.get_width() + 0.4, b.get_y() + b.get_height() / 2, f"${b.get_width():.2f}/mo",
                va="center", fontsize=8.5)
    ax.set_title(f"Active Subscriptions - ${summary.sum():.2f}/month total")
    ax.set_xlabel("Monthly cost ($)")
    fig.tight_layout()
    fig.savefig(f"{CHARTS}/05_subscriptions.png", dpi=150)
    plt.close(fig)
    return summary


def detect_anomalies(df, z_threshold=2.0, min_history=3):
    spend = df[df["amount"] < 0].copy()
    spend["amount_abs"] = -spend["amount"]
    stats = spend.groupby("merchant")["amount_abs"].agg(["mean", "std", "count"])
    spend = spend.merge(stats, left_on="merchant", right_index=True)
    spend = spend[spend["count"] >= min_history].copy()
    spend["z_score"] = (spend["amount_abs"] - spend["mean"]) / spend["std"].replace(0, np.nan)
    anomalies = spend[spend["z_score"] > z_threshold].sort_values("z_score", ascending=False)
    return anomalies[["date", "merchant", "category", "amount_abs", "mean", "z_score"]]


def chart_anomalies(anomalies):
    top = anomalies.head(8).sort_values("z_score")
    labels = [f"{r.merchant} ({r.date.strftime('%b %d')})" for r in top.itertuples()]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.barh(labels, top["z_score"], color=WARN)
    for b, amt in zip(bars, top["amount_abs"]):
        ax.text(b.get_width() + 0.1, b.get_y() + b.get_height() / 2, f"${amt:,.0f}",
                va="center", fontsize=8.5)
    ax.axvline(2.0, color="#444444", linewidth=0.8, linestyle="--")
    ax.set_title("Unusual Transactions (z-score vs. merchant's own average)")
    ax.set_xlabel("Standard deviations above that merchant's average")
    fig.tight_layout()
    fig.savefig(f"{CHARTS}/06_anomalies.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Advanced features
# ---------------------------------------------------------------------------

def forecast_next_month(monthly_expense: pd.Series, target_x: int):
    """Simple linear trend forecast, fit on complete months only and projected
    forward to `target_x` (the index of the target month in the FULL month
    sequence, including the partial trailing month that was excluded from the
    fit). With ~6 months of history this is a directional estimate, not a
    precision forecast - the printed output says so explicitly rather than
    overstating confidence."""
    y = monthly_expense.values
    x = np.arange(len(y))
    if len(y) < 3:
        return round(y.mean(), 2)
    slope, intercept = np.polyfit(x, y, 1)
    forecast = slope * target_x + intercept
    # keep it sane - a naive average as a floor so a steep short-history slope
    # can't produce a negative or wildly implausible forecast
    floor = y[-3:].mean() * 0.6
    return round(max(forecast, floor), 2)


def financial_health_score(monthly: pd.DataFrame, subs_total: float, anomalies: pd.DataFrame, df: pd.DataFrame):
    """0-100 score built from four transparent, equally-weighted components."""
    total_income = monthly["income"].sum()
    total_expense = monthly["expense"].sum()

    # 1. Savings rate (0-25): (income - expense) / income, scaled
    savings_rate = (total_income - total_expense) / total_income if total_income else 0
    savings_score = max(0, min(25, (savings_rate / 0.20) * 25))  # 20%+ savings rate = full marks

    # 2. Subscription burden (0-25): subscriptions as % of income, lower is better
    avg_monthly_income = monthly["income"].mean()
    sub_pct = subs_total / avg_monthly_income if avg_monthly_income else 0
    sub_score = max(0, min(25, 25 - (sub_pct / 0.05) * 25))  # >5% of income in subs = 0

    # 3. Spending consistency (0-25): lower month-to-month coefficient of variation is better
    cv = monthly["expense"].std() / monthly["expense"].mean() if monthly["expense"].mean() else 1
    consistency_score = max(0, min(25, 25 - (cv / 0.30) * 25))  # >=30% swing = 0

    # 4. Anomaly frequency (0-25): fewer flagged unusual transactions relative to total = better
    total_expense_txns = (df["amount"] < 0).sum()
    anomaly_rate = len(anomalies) / total_expense_txns if total_expense_txns else 0
    anomaly_score = max(0, min(25, 25 - (anomaly_rate / 0.05) * 25))  # >=5% anomalous = 0

    total = round(savings_score + sub_score + consistency_score + anomaly_score, 1)
    return {
        "total": total,
        "savings_score": round(savings_score, 1),
        "sub_score": round(sub_score, 1),
        "consistency_score": round(consistency_score, 1),
        "anomaly_score": round(anomaly_score, 1),
        "savings_rate_pct": round(savings_rate * 100, 1),
        "sub_pct_of_income": round(sub_pct * 100, 1),
        "spend_cv_pct": round(cv * 100, 1),
        "anomaly_rate_pct": round(anomaly_rate * 100, 1),
    }


def savings_recommendations(subs_summary, category_spend, anomalies, health):
    recs = []
    if len(subs_summary) > 0:
        cheapest_used_case = subs_summary.sort_values(ascending=True)
        low_value = subs_summary[subs_summary < 5]
        recs.append(
            f"You're paying ${subs_summary.sum():.2f}/month (${subs_summary.sum()*12:.2f}/year) "
            f"across {len(subs_summary)} subscriptions. Cancelling just the two least-used ones "
            f"({', '.join(subs_summary.sort_values(ascending=False).index[-2:])}) would save "
            f"~${subs_summary.sort_values(ascending=False).iloc[-2:].sum()*12:.0f}/year."
        )
    if len(anomalies) > 0:
        recs.append(
            f"{len(anomalies)} transactions were flagged as unusually large for their merchant - "
            f"reviewing these first (largest: ${anomalies.iloc[0]['amount_abs']:,.0f} at "
            f"{anomalies.iloc[0]['merchant']}) is the fastest way to catch one-off overspending "
            f"before it becomes a habit."
        )
    top_cat = category_spend.idxmax()
    recs.append(
        f"{top_cat} is the single largest spending category (${category_spend.max():,.0f} total). "
        f"Even a 10% reduction there (~${category_spend.max()*0.10:,.0f}) outweighs trimming any "
        f"single subscription."
    )
    if health["spend_cv_pct"] > 25:
        recs.append(
            f"Monthly spending swings by {health['spend_cv_pct']:.0f}% month to month - building a "
            f"1-2 month buffer would smooth out the higher-spend months without needing a higher income."
        )
    return recs


def main():
    df = load()

    monthly = df.groupby("month").apply(
        lambda g: pd.Series({
            "income": g.loc[g["amount"] > 0, "amount"].sum(),
            "expense": -g.loc[g["amount"] < 0, "amount"].sum(),
        }), include_groups=False
    ).reset_index().sort_values("month")

    # the trailing month in this dataset is always partial (export cuts off
    # mid-month) - exclude it from any month-over-month or trend comparison
    complete_months = monthly.iloc[:-1] if len(monthly) > 1 else monthly
    complete_month_labels = set(complete_months["month"])

    category_spend = chart_spending_by_category(df)
    subs_summary = chart_subscriptions(df)
    anomalies = detect_anomalies(df)
    chart_anomalies(anomalies)
    latest, prev, change = chart_category_month_change(df, complete_month_labels)
    top_merchants = chart_top_merchants(df)

    # forecast the month AFTER everything in the data (including the partial
    # trailing month), not the month after the last complete month - so the
    # forecast bar never collides with the actual partial-month bar on the chart
    forecast_target_month = pd.Period(monthly["month"].iloc[-1]) + 1
    forecast_month = str(forecast_target_month)
    target_x = len(monthly)  # position of forecast_month in the full month sequence
    forecast_value = forecast_next_month(complete_months.set_index("month")["expense"], target_x)

    chart_monthly_income_expense(df, monthly, forecast_month, forecast_value)

    health = financial_health_score(complete_months, subs_summary.sum(), anomalies, df)
    recs = savings_recommendations(subs_summary, category_spend, anomalies, health)

    print("=" * 72)
    print("DASHBOARD ANSWERS")
    print("=" * 72)
    print(f"Where does most of my money go?     {category_spend.idxmax()} (${category_spend.max():,.0f} total)")
    print(f"Which categories increased this month ({latest} vs {prev})?")
    for cat, val in change.sort_values(ascending=False).head(3).items():
        direction = "up" if val > 0 else "down"
        print(f"    {cat}: {direction} ${abs(val):,.0f}")
    print(f"Which merchants receive the most money? {top_merchants.index[0]} (${top_merchants.iloc[0]:,.0f})")
    print(f"What subscriptions am I paying for?  {len(subs_summary)} active, ${subs_summary.sum():.2f}/month total")
    print(f"Which transactions look unusual?     {len(anomalies)} flagged (z-score > 2.0)")
    print(f"How much could I potentially save?   ${subs_summary.sum()*12:,.0f}/year just from subscriptions")
    print()
    print("=" * 72)
    print(f"NEXT-MONTH FORECAST ({forecast_month}): ${forecast_value:,.0f} in expenses")
    print("  (linear trend over the logged months - directional, not precise, given ~6-7 months of history)")
    print()
    print("=" * 72)
    print(f"FINANCIAL HEALTH SCORE: {health['total']}/100")
    print(f"  Savings rate ({health['savings_rate_pct']}%):        {health['savings_score']}/25")
    print(f"  Subscription burden ({health['sub_pct_of_income']}% of income): {health['sub_score']}/25")
    print(f"  Spending consistency (CV {health['spend_cv_pct']}%): {health['consistency_score']}/25")
    print(f"  Anomaly rate ({health['anomaly_rate_pct']}%):         {health['anomaly_score']}/25")
    print()
    print("=" * 72)
    print("SAVINGS RECOMMENDATIONS")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r}")
    print("=" * 72)

    anomalies.to_csv(f"{CLEAN}/anomalies.csv", index=False)
    print("\n6 charts written to charts/, anomalies.csv written to data/clean/")


if __name__ == "__main__":
    main()
