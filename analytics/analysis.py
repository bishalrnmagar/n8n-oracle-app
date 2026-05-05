"""
Weekly finance analysis: category breakdown, overspend alerts,
spending trends, and savings rate.
"""

import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from db import query_df
from config import TIMEZONE

TZ = ZoneInfo(TIMEZONE)


def _now():
    return datetime.now(TZ)


def _week_range():
    """Return (start, end) for the past 7 days."""
    end = _now().date()
    start = end - timedelta(days=6)
    return start, end


def _month_range():
    """Return (start, end) for current month."""
    now = _now().date()
    start = now.replace(day=1)
    return start, now


def get_weekly_expenses(user_id):
    start, end = _week_range()
    return query_df(
        """
        SELECT date, amount, category
        FROM transactions
        WHERE user_id = %s AND status = 'active'
          AND date BETWEEN %s AND %s
        ORDER BY date
        """,
        (user_id, start, end),
    )


def get_monthly_expenses(user_id):
    start, end = _month_range()
    return query_df(
        """
        SELECT date, amount, category
        FROM transactions
        WHERE user_id = %s AND status = 'active'
          AND date BETWEEN %s AND %s
        ORDER BY date
        """,
        (user_id, start, end),
    )


def get_prev_week_expenses(user_id):
    end = _now().date() - timedelta(days=7)
    start = end - timedelta(days=6)
    return query_df(
        """
        SELECT date, amount, category
        FROM transactions
        WHERE user_id = %s AND status = 'active'
          AND date BETWEEN %s AND %s
        """,
        (user_id, start, end),
    )


def get_monthly_income(user_id):
    start, end = _month_range()
    return query_df(
        """
        SELECT date, amount, source
        FROM income
        WHERE user_id = %s AND date BETWEEN %s AND %s
        """,
        (user_id, start, end),
    )


def get_budgets(user_id):
    return query_df(
        """
        SELECT category, monthly_limit, alert_at_percent
        FROM budgets
        WHERE user_id = %s
        """,
        (user_id,),
    )


def category_breakdown(expenses_df):
    """Group by category, return sorted breakdown."""
    if expenses_df.empty:
        return pd.DataFrame(columns=["category", "amount", "pct"])
    grouped = expenses_df.groupby("category")["amount"].sum().reset_index()
    total = grouped["amount"].sum()
    grouped["pct"] = (grouped["amount"] / total * 100).round(1)
    return grouped.sort_values("amount", ascending=False).reset_index(drop=True)


def overspend_alerts(user_id):
    """Check monthly spend vs budgets, return list of alerts."""
    monthly = get_monthly_expenses(user_id)
    budgets = get_budgets(user_id)

    if monthly.empty or budgets.empty:
        return []

    spent_by_cat = monthly.groupby("category")["amount"].sum()
    alerts = []

    for _, row in budgets.iterrows():
        cat = row["category"]
        limit = float(row["monthly_limit"])
        threshold = float(row["alert_at_percent"])
        spent = float(spent_by_cat.get(cat, 0))
        pct_used = (spent / limit * 100) if limit > 0 else 0

        if pct_used >= 100:
            alerts.append({
                "category": cat,
                "spent": spent,
                "limit": limit,
                "pct": round(pct_used, 1),
                "severity": "over",
            })
        elif pct_used >= threshold:
            alerts.append({
                "category": cat,
                "spent": spent,
                "limit": limit,
                "pct": round(pct_used, 1),
                "severity": "warning",
            })

    return alerts


def spending_trends(user_id):
    """Compare this week vs last week total and by category."""
    this_week = get_weekly_expenses(user_id)
    prev_week = get_prev_week_expenses(user_id)

    this_total = float(this_week["amount"].sum()) if not this_week.empty else 0
    prev_total = float(prev_week["amount"].sum()) if not prev_week.empty else 0

    if prev_total > 0:
        change_pct = round((this_total - prev_total) / prev_total * 100, 1)
    else:
        change_pct = None

    this_by_cat = (
        this_week.groupby("category")["amount"].sum()
        if not this_week.empty
        else pd.Series(dtype=float)
    )
    prev_by_cat = (
        prev_week.groupby("category")["amount"].sum()
        if not prev_week.empty
        else pd.Series(dtype=float)
    )

    cat_trends = []
    all_cats = set(this_by_cat.index) | set(prev_by_cat.index)
    for cat in sorted(all_cats):
        curr = float(this_by_cat.get(cat, 0))
        prev = float(prev_by_cat.get(cat, 0))
        cat_trends.append({"category": cat, "this_week": curr, "prev_week": prev})

    return {
        "this_week_total": this_total,
        "prev_week_total": prev_total,
        "change_pct": change_pct,
        "by_category": cat_trends,
    }


def savings_rate(user_id):
    """Calculate monthly savings rate = (income - expenses) / income."""
    income_df = get_monthly_income(user_id)
    expenses_df = get_monthly_expenses(user_id)

    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0
    total_expenses = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0

    savings = total_income - total_expenses
    rate = round((savings / total_income * 100), 1) if total_income > 0 else None

    return {
        "income": total_income,
        "expenses": total_expenses,
        "savings": savings,
        "rate": rate,
    }
