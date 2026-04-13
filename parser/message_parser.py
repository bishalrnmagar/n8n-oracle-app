"""
Finance Bot Message Parser
Extracts intent, amount, category, note, and tags from Telegram messages.
"""

CATEGORY_KEYWORDS = {
    "Food": ["food", "lunch", "dinner", "breakfast", "snack", "meal", "restaurant", "cafe", "chai", "tea", "coffee", "momo", "tiffin", "canteen"],
    "Transport": ["petrol", "diesel", "fuel", "uber", "taxi", "bus", "bike", "ride", "fare", "auto", "pathao"],
    "Groceries": ["groceries", "grocery", "vegetables", "fruits", "supermarket", "bhatbhateni", "bigmart", "dairy", "milk", "eggs"],
    "Rent": ["rent"],
    "Utilities": ["electricity", "water", "internet", "wifi", "phone", "mobile", "recharge", "bill", "nea", "ntc", "ncell"],
    "Entertainment": ["movie", "netflix", "spotify", "game", "party", "outing", "drinks", "beer"],
    "Health": ["medicine", "doctor", "hospital", "pharmacy", "gym", "medical", "dental"],
    "Shopping": ["clothes", "shoes", "electronics", "amazon", "daraz", "gadget", "laptop"],
    "Subscriptions": ["subscription", "premium", "membership"],
    "Education": ["books", "course", "tuition", "class", "training", "udemy", "coursera"],
}

STOP_WORDS = ["spent", "on", "for", "rs", "npr", "to", "at", "with"]


def match_category(text):
    words = text.lower().split()
    for word in words:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if word in keywords:
                return cat
    return "Misc"


def strip_category_keywords(text, category):
    keywords = CATEGORY_KEYWORDS.get(category, [])
    words = text.split()
    return " ".join(w for w in words if w.lower() not in keywords).strip()


def parse_message(raw):
    import re

    msg = raw.strip()
    msg_lower = msg.lower()

    # Help
    if re.match(r"^(/start|/help|help)$", msg_lower):
        return {"intent": "help", "raw_message": msg}

    # Delete last
    if re.search(r"\b(delete last|undo)\b", msg_lower):
        return {"intent": "delete_last", "raw_message": msg}

    # Edit last
    if re.search(r"\b(edit last|change last|last was)\b", msg_lower):
        result = {"intent": "edit_last", "raw_message": msg}

        amount_edit = re.search(r"amount\s+to\s+(\d+)", msg_lower)
        if amount_edit:
            result["edit_field"] = "amount"
            result["edit_value"] = amount_edit.group(1)
            return result

        cat_edit = re.search(r"(?:was|to)\s+(\w+?)(?:\s+not\s+\w+)?$", msg_lower)
        if cat_edit:
            result["edit_field"] = "category"
            result["edit_value"] = match_category(cat_edit.group(1))
            return result

        return result

    # Report
    if re.search(r"\b(report|summary|how much|total)\b", msg_lower):
        result = {"intent": "report", "raw_message": msg}

        if "today" in msg_lower:
            result["period"] = "today"
        elif "this week" in msg_lower:
            result["period"] = "this_week"
        elif "last month" in msg_lower:
            result["period"] = "last_month"
        elif "yesterday" in msg_lower:
            result["period"] = "yesterday"
        else:
            result["period"] = "this_month"

        cat_filter = re.search(r"(?:on|for)\s+(\w+)", msg_lower)
        if cat_filter:
            result["category_filter"] = match_category(cat_filter.group(1))

        return result

    # Set budget
    budget_match = re.search(r"set\s+budget\s+(\w+)\s+(\d+)", msg_lower)
    if budget_match:
        return {
            "intent": "set_budget",
            "category": match_category(budget_match.group(1)),
            "amount": int(budget_match.group(2)),
            "raw_message": msg,
        }

    # Income
    if re.search(r"\b(received|earned|salary|income)\b", msg_lower):
        amount_match = re.search(r"(\d+)", msg)
        if amount_match:
            source = re.sub(r"\d+", "", msg_lower)
            source = re.sub(r"\b(received|got|earned|rs|npr)\b", "", source).strip()
            return {
                "intent": "log_income",
                "amount": int(amount_match.group(1)),
                "source": source or "unspecified",
                "raw_message": msg,
            }

    # Log expense (default)
    amount_match = re.search(r"(\d+)", msg)
    if not amount_match:
        return {"intent": "unknown", "raw_message": msg}

    amount = int(amount_match.group(1))

    tags = re.findall(r"#\w+", msg)
    tags_str = ",".join(tags)

    remaining = re.sub(r"\d+", "", msg_lower)
    remaining = re.sub(r"#\w+", "", remaining)
    remaining = " ".join(w for w in remaining.split() if w not in STOP_WORDS).strip()

    category = match_category(remaining)
    note = strip_category_keywords(remaining, category)

    return {
        "intent": "log_expense",
        "amount": amount,
        "category": category,
        "note": note,
        "tags": tags_str,
        "raw_message": msg,
    }


# ─── Quick test ───────────────────────────────────────────────

if __name__ == "__main__":
    test_messages = [
        "120 food",
        "petrol 500",
        "chai 40",
        "uber 250 to office",
        "500 dinner with friends #client",
        "15000 rent",
        "delete last",
        "undo",
        "edit last amount to 150",
        "last was transport not food",
        "report today",
        "how much on food this month",
        "set budget food 5000",
        "received 50000 salary",
        "help",
        "/start",
        "random text no number",
    ]

    for m in test_messages:
        result = parse_message(m)
        print(f"{m:40s} → {result}")
