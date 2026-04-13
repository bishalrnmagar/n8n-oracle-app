/**
 * Finance Bot Message Parser
 * Extracts intent, amount, category, note, and tags from Telegram messages.
 * Paste this into an n8n Code node after the Telegram Trigger node.
 */

const raw = $input.first().json.message.text || '';
const msg = raw.trim();
const msgLower = msg.toLowerCase();

const CATEGORY_KEYWORDS = {
  Food: ['food', 'lunch', 'dinner', 'breakfast', 'snack', 'meal', 'restaurant', 'cafe', 'chai', 'tea', 'coffee', 'momo', 'tiffin', 'canteen'],
  Transport: ['petrol', 'diesel', 'fuel', 'uber', 'taxi', 'bus', 'bike', 'ride', 'fare', 'auto', 'pathao'],
  Groceries: ['groceries', 'grocery', 'vegetables', 'fruits', 'supermarket', 'bhatbhateni', 'bigmart', 'dairy', 'milk', 'eggs'],
  Rent: ['rent'],
  Utilities: ['electricity', 'water', 'internet', 'wifi', 'phone', 'mobile', 'recharge', 'bill', 'nea', 'ntc', 'ncell'],
  Entertainment: ['movie', 'netflix', 'spotify', 'game', 'party', 'outing', 'drinks', 'beer'],
  Health: ['medicine', 'doctor', 'hospital', 'pharmacy', 'gym', 'medical', 'dental'],
  Shopping: ['clothes', 'shoes', 'electronics', 'amazon', 'daraz', 'gadget', 'laptop'],
  Subscriptions: ['subscription', 'premium', 'membership'],
  Education: ['books', 'course', 'tuition', 'class', 'training', 'udemy', 'coursera']
};

const STOP_WORDS = ['spent', 'on', 'for', 'rs', 'npr', 'to', 'at', 'with'];

function matchCategory(text) {
  const words = text.toLowerCase().split(/\s+/);
  for (const word of words) {
    for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
      if (keywords.includes(word)) return cat;
    }
  }
  return 'Misc';
}

function stripCategoryKeywords(text, category) {
  const keywords = CATEGORY_KEYWORDS[category] || [];
  return text.split(/\s+/).filter(w => !keywords.includes(w.toLowerCase())).join(' ').trim();
}

// ─── Help ────────────────────────────────────────────────────
if (/^(\/start|\/help|help)$/i.test(msgLower)) {
  return [{ json: { intent: 'help', raw_message: msg } }];
}

// ─── Delete last ─────────────────────────────────────────────
if (/\b(delete last|undo)\b/i.test(msgLower)) {
  return [{ json: { intent: 'delete_last', raw_message: msg } }];
}

// ─── Edit last ───────────────────────────────────────────────
if (/\b(edit last|change last|last was)\b/i.test(msgLower)) {
  const result = { intent: 'edit_last', raw_message: msg };

  const amountEdit = msgLower.match(/amount\s+to\s+(\d+)/);
  if (amountEdit) {
    result.edit_field = 'amount';
    result.edit_value = amountEdit[1];
    return [{ json: result }];
  }

  const catEdit = msgLower.match(/(?:was|to)\s+(\w+?)(?:\s+not\s+\w+)?$/);
  if (catEdit) {
    result.edit_field = 'category';
    result.edit_value = matchCategory(catEdit[1]);
    return [{ json: result }];
  }

  return [{ json: result }];
}

// ─── Report ──────────────────────────────────────────────────
if (/\b(report|summary|how much|total)\b/i.test(msgLower)) {
  const result = { intent: 'report', raw_message: msg };

  if (/today/.test(msgLower)) result.period = 'today';
  else if (/this week/.test(msgLower)) result.period = 'this_week';
  else if (/last month/.test(msgLower)) result.period = 'last_month';
  else if (/yesterday/.test(msgLower)) result.period = 'yesterday';
  else result.period = 'this_month';

  const catFilter = msgLower.match(/(?:on|for)\s+(\w+)/);
  if (catFilter) result.category_filter = matchCategory(catFilter[1]);

  return [{ json: result }];
}

// ─── Set budget ──────────────────────────────────────────────
const budgetMatch = msgLower.match(/set\s+budget\s+(\w+)\s+(\d+)/);
if (budgetMatch) {
  return [{ json: {
    intent: 'set_budget',
    category: matchCategory(budgetMatch[1]),
    amount: parseInt(budgetMatch[2]),
    raw_message: msg
  }}];
}

// ─── Income ──────────────────────────────────────────────────
if (/\b(received|earned|salary|income)\b/i.test(msgLower)) {
  const a = msg.match(/(\d+)/);
  if (a) {
    const source = msgLower.replace(/\d+/g, '').replace(/\b(received|got|earned|rs|npr)\b/g, '').trim();
    return [{ json: {
      intent: 'log_income',
      amount: parseInt(a[1]),
      source: source || 'unspecified',
      raw_message: msg
    }}];
  }
}

// ─── Log expense (default) ───────────────────────────────────
const tags = msg.match(/#\w+/g) || [];
const tagsStr = tags.join(',');

// Split by newlines to handle multi-line messages, then parse each line
const lines = msg.split(/\\n|\n/).map(l => l.trim()).filter(l => l);

const items = [];

for (const line of lines) {
  const lineLower = line.toLowerCase();
  const amountMatch = line.match(/(\d+)/);
  if (!amountMatch) continue;

  const lineAmount = parseInt(amountMatch[1]);

  // Remove number, tags, stop words → leftover is category hint
  const hint = lineLower
    .replace(/\d+/g, '')
    .replace(/#\w+/g, '')
    .split(/\s+/)
    .filter(w => w && !STOP_WORDS.includes(w))
    .join(' ');

  const category = matchCategory(hint);
  const note = stripCategoryKeywords(hint, category);
  items.push({ amount: lineAmount, category, note });
}

// If no items parsed from lines, treat whole message as single expense
if (items.length === 0) {
  const amountMatch = msg.match(/(\d+)/);
  if (!amountMatch) {
    return [{ json: { intent: 'unknown', raw_message: msg } }];
  }
  const remaining = msgLower
    .replace(/\d+/g, '')
    .replace(/#\w+/g, '')
    .split(/\s+/)
    .filter(w => w && !STOP_WORDS.includes(w))
    .join(' ');
  const category = matchCategory(remaining);
  const note = stripCategoryKeywords(remaining, category);
  items.push({ amount: parseInt(amountMatch[1]), category, note });
}

const total = items.reduce((sum, item) => sum + item.amount, 0);

return [{ json: {
  intent: 'log_expense',
  amount: items.length === 1 ? items[0].amount : total,
  category: items.length === 1 ? items[0].category : 'Multiple',
  note: items.length === 1 ? items[0].note : '',
  tags: tagsStr,
  total,
  items,
  raw_message: msg
}}];
