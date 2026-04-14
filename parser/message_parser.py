"""
Finance Bot Message Parser
Extracts intent, amount, category, note, tags, and date offset from Telegram messages.
"""

import re

CATEGORY_KEYWORDS = {
    "Food": ["food", "lunch", "dinner", "breakfast", "snack", "meal", "restaurant", "cafe", "chai", "tea", "coffee", "momo", "dal bhat", "tiffin", "canteen"],
    "Transport": ["petrol", "diesel", "fuel", "uber", "taxi", "bus", "bike", "ride", "fare", "auto", "grab", "ola", "pathao"],
    "Groceries": ["groceries", "grocery", "vegetables", "fruits", "supermarket", "bhatbhateni", "bigmart", "dairy", "milk", "eggs"],
    "Rent": ["rent", "house rent", "room rent", "flat"],
    "Utilities": ["electricity", "water", "internet", "wifi", "phone", "mobile", "recharge", "bill", "nea", "ntc", "ncell"],
    "Entertainment": ["movie", "netflix", "spotify", "game", "party", "outing", "drinks", "beer"],
    "Health": ["medicine", "doctor", "hospital", "pharmacy", "gym", "medical", "health", "dental"],
    "Shopping": ["clothes", "shoes", "electronics", "amazon", "daraz", "gadget", "laptop"],
    "Subscriptions": ["subscription", "premium", "membership", "annual", "monthly plan"],
    "Education": ["books", "course", "tuition", "class", "training", "udemy", "coursera"],
}

STOP_WORDS = ["spent", "on", "for", "rs", "npr", "rupees", "rp", "paid"]

ALL_CATEGORIES = [
    "food", "transport", "groceries", "rent", "utilities",
    "entertainment", "health", "shopping", "subscriptions", "education", "misc",
]


def match_category(text):
    """Find the best matching category by longest keyword match."""
    matched = "Misc"
    matched_kw = ""
    lower = text.lower()

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower and len(kw) > len(matched_kw):
                matched = cat
                matched_kw = kw

    return matched, matched_kw


def parse_message(raw):
    text = (raw or "").strip()
    lower = text.lower()

    # ---- Classify intent ----
    intent = "unknown"

    if re.match(r"^/?(?:start|help)$", text, re.IGNORECASE):
        intent = "help"
    elif re.search(r"\b(delete\s*last|remove\s*last|undo|cancel\s*last)\b", text, re.IGNORECASE):
        intent = "delete_last"
    elif re.search(r"\b(edit\s*last|change\s*last|correct\s*last|last\s*was)\b", text, re.IGNORECASE):
        intent = "edit_last"
    elif re.search(r"\b(report|summary|how\s*much|total|spent\s*today)\b", text, re.IGNORECASE):
        intent = "report"
    elif re.search(r"\bset\s+budget\b", text, re.IGNORECASE):
        intent = "set_budget"
    elif re.search(r"\b(received|earned|salary|income)\b", text, re.IGNORECASE) and re.search(r"\d", text):
        intent = "log_income"
    elif re.search(r"\d", text):
        intent = "log_expense"

    # ---- Detect date offset ----
    date_offset = 0
    if re.search(r"\byesterday\b", lower):
        date_offset = 1
    else:
        days_ago = re.search(r"(\d+)\s*days?\s*ago", lower)
        if days_ago:
            date_offset = int(days_ago.group(1))

    # ---- Parse log_expense ----
    amount = 0
    category = "Misc"
    note = ""
    tags = []

    if intent == "log_expense":
        num_match = re.search(r"\d+(?:\.\d{1,2})?", text)
        amount = float(num_match.group(0)) if num_match else 0

        tag_matches = re.findall(r"#\w+", text)
        if tag_matches:
            tags = tag_matches

        cleaned = text
        cleaned = re.sub(r"\byesterday\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\d+\s*days?\s*ago", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\d+(?:\.\d{1,2})?", "", cleaned)
        cleaned = re.sub(r"#\w+", "", cleaned)
        stop_pattern = r"\b(" + "|".join(STOP_WORDS) + r")\b"
        cleaned = re.sub(stop_pattern, "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        category, matched_kw = match_category(cleaned)

        if matched_kw:
            idx = cleaned.lower().index(matched_kw)
            note = (cleaned[:idx] + cleaned[idx + len(matched_kw) :]).strip()
            note = re.sub(r"\s+", " ", note)
        else:
            note = cleaned

    # ---- Parse log_income ----
    source = ""
    if intent == "log_income":
        num_match = re.search(r"\d+(?:\.\d{1,2})?", text)
        amount = float(num_match.group(0)) if num_match else 0
        source = re.sub(r"\d+", "", lower)
        source = re.sub(r"\b(received|got|earned|rs|npr)\b", "", source).strip()
        source = source or "unspecified"

    # ---- Parse edit_last ----
    edit_amount = None
    edit_category = None

    if intent == "edit_last":
        amt_match = re.search(r"(?:amount\s*(?:to\s*)?|to\s+)(\d+(?:\.\d{1,2})?)", text, re.IGNORECASE)
        if amt_match:
            edit_amount = float(amt_match.group(1))

        cat_match = re.search(r"(?:was|to)\s+(\w+)", text, re.IGNORECASE)
        if cat_match:
            possible_cat = cat_match.group(1).lower()
            if possible_cat in ALL_CATEGORIES:
                edit_category = possible_cat.capitalize()

        if edit_amount is None and edit_category is None:
            num_match = re.search(r"\d+(?:\.\d{1,2})?", text)
            if num_match:
                edit_amount = float(num_match.group(0))

    # ---- Parse set_budget ----
    budget_category = None
    budget_amount = None
    if intent == "set_budget":
        budget_match = re.search(r"set\s+budget\s+(\w+)\s+(\d+)", lower)
        if budget_match:
            budget_category, _ = match_category(budget_match.group(1))
            budget_amount = int(budget_match.group(2))

    # ---- Parse report ----
    period = "this_month"
    category_filter = None
    if intent == "report":
        if "today" in lower:
            period = "today"
        elif "this week" in lower or "this_week" in lower:
            period = "this_week"
        elif "last month" in lower or "last_month" in lower:
            period = "last_month"
        elif "yesterday" in lower:
            period = "yesterday"

        cat_filter = re.search(r"(?:on|for)\s+(\w+)", lower)
        if cat_filter:
            category_filter, _ = match_category(cat_filter.group(1))

    return {
        "intent": intent,
        "amount": amount,
        "category": category,
        "note": note,
        "tags": tags,
        "date_offset": date_offset,
        "edit_amount": edit_amount,
        "edit_category": edit_category,
        "source": source,
        "budget_category": budget_category,
        "budget_amount": budget_amount,
        "period": period,
        "category_filter": category_filter,
        "raw_message": text,
    }


# ─── Quick test ─────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        "120 food",
        "spent 500 on petrol",
        "chai 40",
        "uber 250 to office",
        "500 dinner with friends #client",
        "15000 rent",
        "120 food yesterday",
        "500 petrol 2 days ago",
        "groceries 1200 3 days ago #weekly",
        "delete last",
        "remove last",
        "undo",
        "cancel last",
        "edit last amount to 150",
        "last was transport not food",
        "change last to groceries",
        "correct last 200",
        "report today",
        "report this month",
        "how much on food this month",
        "total this week",
        "set budget food 5000",
        "received 50000 salary",
        "earned 2000 freelance",
        "help",
        "/start",
        "random text no number",
    ]

    print(f"{'MESSAGE':<45} {'INTENT':<15} PARSED")
    print("-" * 100)

    for t in tests:
        r = parse_message(t)
        detail = ""
        if r["intent"] == "log_expense":
            detail = f"amt={r['amount']} cat={r['category']} note=\"{r['note']}\" tags={','.join(r['tags'])} dateOffset={r['date_offset']}"
        elif r["intent"] == "log_income":
            detail = f"amt={r['amount']} source=\"{r['source']}\""
        elif r["intent"] == "edit_last":
            detail = f"editAmt={r['edit_amount']} editCat={r['edit_category']}"
        elif r["intent"] == "report":
            detail = f"period={r['period']} catFilter={r['category_filter']}"
        elif r["intent"] == "set_budget":
            detail = f"cat={r['budget_category']} amt={r['budget_amount']}"

        print(f"{t:<45} {r['intent']:<15} {detail}")
