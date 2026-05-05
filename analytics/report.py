"""Format analysis results into Telegram-friendly messages."""

from analysis import (
    get_weekly_expenses,
    category_breakdown,
    overspend_alerts,
    spending_trends,
    savings_rate,
    _week_range,
)


def format_currency(amount):
    return f"NPR {amount:,.0f}"


def build_weekly_report(user_id):
    """Build full weekly analytics report string."""
    start, end = _week_range()
    sections = []

    header = (
        f"📊 *Weekly Finance Report*\n"
        f"_{start.strftime('%b %d')} — {end.strftime('%b %d, %Y')}_\n"
    )
    sections.append(header)

    # --- Category Breakdown ---
    weekly_exp = get_weekly_expenses(user_id)
    breakdown = category_breakdown(weekly_exp)

    if not breakdown.empty:
        total = float(breakdown["amount"].sum())
        lines = ["*Category Breakdown:*"]
        for _, row in breakdown.iterrows():
            bar_len = int(row["pct"] / 5)
            bar = "█" * bar_len
            lines.append(
                f"  {row['category']:<14} {format_currency(row['amount']):>12}  "
                f"({row['pct']}%) {bar}"
            )
        lines.append(f"  {'─' * 36}")
        lines.append(f"  {'Total':<14} {format_currency(total):>12}")
        sections.append("\n".join(lines))
    else:
        sections.append("_No expenses recorded this week._")

    # --- Trends ---
    trends = spending_trends(user_id)
    trend_lines = ["*Week-over-Week Trends:*"]

    if trends["change_pct"] is not None:
        arrow = "📈" if trends["change_pct"] > 0 else "📉"
        sign = "+" if trends["change_pct"] > 0 else ""
        trend_lines.append(
            f"  {arrow} Total: {format_currency(trends['this_week_total'])} "
            f"({sign}{trends['change_pct']}% vs last week)"
        )
    else:
        trend_lines.append(
            f"  Total: {format_currency(trends['this_week_total'])} (no prior week data)"
        )

    big_changes = []
    for ct in trends["by_category"]:
        if ct["prev_week"] > 0:
            pct = (ct["this_week"] - ct["prev_week"]) / ct["prev_week"] * 100
            if abs(pct) >= 30:
                big_changes.append((ct["category"], pct))

    if big_changes:
        trend_lines.append("  Notable shifts:")
        for cat, pct in sorted(big_changes, key=lambda x: abs(x[1]), reverse=True)[:5]:
            sign = "+" if pct > 0 else ""
            emoji = "⬆️" if pct > 0 else "⬇️"
            trend_lines.append(f"    {emoji} {cat}: {sign}{pct:.0f}%")

    sections.append("\n".join(trend_lines))

    # --- Overspend Alerts ---
    alerts = overspend_alerts(user_id)
    if alerts:
        alert_lines = ["*Budget Alerts:*"]
        for a in alerts:
            if a["severity"] == "over":
                emoji = "🚨"
                over_by = a["spent"] - a["limit"]
                alert_lines.append(
                    f"  {emoji} *{a['category']}*: {format_currency(a['spent'])} / "
                    f"{format_currency(a['limit'])} ({a['pct']}%) — "
                    f"over by {format_currency(over_by)}"
                )
            else:
                emoji = "⚠️"
                remaining = a["limit"] - a["spent"]
                alert_lines.append(
                    f"  {emoji} {a['category']}: {format_currency(a['spent'])} / "
                    f"{format_currency(a['limit'])} ({a['pct']}%) — "
                    f"{format_currency(remaining)} left"
                )
        sections.append("\n".join(alert_lines))

    # --- Savings Rate ---
    sr = savings_rate(user_id)
    savings_lines = ["*Monthly Savings Rate:*"]
    if sr["rate"] is not None:
        emoji = "✅" if sr["rate"] >= 20 else ("⚠️" if sr["rate"] >= 0 else "🚨")
        savings_lines.append(f"  Income:   {format_currency(sr['income'])}")
        savings_lines.append(f"  Expenses: {format_currency(sr['expenses'])}")
        savings_lines.append(f"  {emoji} Savings: {format_currency(sr['savings'])} ({sr['rate']}%)")
    else:
        savings_lines.append("  _No income recorded this month — cannot compute rate._")

    sections.append("\n".join(savings_lines))

    return "\n\n".join(sections)
