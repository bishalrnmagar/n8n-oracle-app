/**
 * Finance Bot Message Parser
 * Extracts intent, amount, category, note, tags, and date offset from Telegram messages.
 *
 * n8n usage:  Paste the parseMessage() body into a Code node.
 * Standalone: Run `node message_parser.js` to execute the test suite at the bottom.
 */

const CATEGORY_KEYWORDS = {
  Food: ['food', 'lunch', 'dinner', 'breakfast', 'snack', 'meal', 'restaurant', 'cafe', 'chai', 'tea', 'coffee', 'momo', 'dal bhat', 'tiffin', 'canteen'],
  Transport: ['petrol', 'diesel', 'fuel', 'uber', 'taxi', 'bus', 'bike', 'ride', 'fare', 'auto', 'grab', 'ola', 'pathao'],
  Groceries: ['groceries', 'grocery', 'vegetables', 'fruits', 'supermarket', 'bhatbhateni', 'bigmart', 'dairy', 'milk', 'eggs'],
  Rent: ['rent', 'house rent', 'room rent', 'flat'],
  Utilities: ['electricity', 'water', 'internet', 'wifi', 'phone', 'mobile', 'recharge', 'bill', 'nea', 'ntc', 'ncell'],
  Entertainment: ['movie', 'netflix', 'spotify', 'game', 'party', 'outing', 'drinks', 'beer'],
  Health: ['medicine', 'doctor', 'hospital', 'pharmacy', 'gym', 'medical', 'health', 'dental'],
  Shopping: ['clothes', 'shoes', 'electronics', 'amazon', 'daraz', 'gadget', 'laptop'],
  Subscriptions: ['subscription', 'premium', 'membership', 'annual', 'monthly plan'],
  Education: ['books', 'course', 'tuition', 'class', 'training', 'udemy', 'coursera'],
};

const STOP_WORDS = ['spent', 'on', 'for', 'rs', 'npr', 'rupees', 'rp', 'paid'];

const ALL_CATEGORIES = ['food', 'transport', 'groceries', 'rent', 'utilities', 'entertainment', 'health', 'shopping', 'subscriptions', 'education', 'misc'];

function matchCategory(text) {
  let matched = 'Misc';
  let matchedKw = '';
  const lower = text.toLowerCase();

  for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const kw of keywords) {
      if (lower.includes(kw) && kw.length > matchedKw.length) {
        matched = cat;
        matchedKw = kw;
      }
    }
  }

  return { category: matched, keyword: matchedKw };
}

function parseMessage(raw) {
  const text = (raw || '').trim();
  const lower = text.toLowerCase();

  // ---- Classify intent ----
  let intent = 'unknown';

  if (/^\/?(?:start|help)$/i.test(text)) {
    intent = 'help';
  } else if (/\b(delete\s*last|remove\s*last|undo|cancel\s*last)\b/i.test(text)) {
    intent = 'delete_last';
  } else if (/\b(edit\s*last|change\s*last|correct\s*last|last\s*was)\b/i.test(text)) {
    intent = 'edit_last';
  } else if (/\b(report|summary|how\s*much|total|spent\s*today)\b/i.test(text)) {
    intent = 'report';
  } else if (/\b(set\s+budget)\b/i.test(text)) {
    intent = 'set_budget';
  } else if (/\b(received|earned|salary|income)\b/i.test(text) && /\d/.test(text)) {
    intent = 'log_income';
  } else if (/\d/.test(text)) {
    intent = 'log_expense';
  }

  // ---- Detect date offset ----
  let dateOffset = 0;
  const yesterdayMatch = lower.match(/\byesterday\b/);
  const daysAgoMatch = lower.match(/(\d+)\s*days?\s*ago/);
  if (yesterdayMatch) {
    dateOffset = 1;
  } else if (daysAgoMatch) {
    dateOffset = parseInt(daysAgoMatch[1], 10);
  }

  // ---- Parse log_expense ----
  let amount = 0;
  let category = 'Misc';
  let note = '';
  let tags = [];

  if (intent === 'log_expense') {
    const numMatch = text.match(/\d+(?:\.\d{1,2})?/);
    amount = numMatch ? parseFloat(numMatch[0]) : 0;

    const tagMatches = text.match(/#\w+/g);
    if (tagMatches) tags = tagMatches;

    let cleaned = text
      .replace(/\byesterday\b/gi, '')
      .replace(/\d+\s*days?\s*ago/gi, '')
      .replace(/\d+(?:\.\d{1,2})?/g, '')
      .replace(/#\w+/g, '')
      .replace(new RegExp('\\b(' + STOP_WORDS.join('|') + ')\\b', 'gi'), '')
      .replace(/\s+/g, ' ')
      .trim();

    const { category: cat, keyword: matchedKw } = matchCategory(cleaned);
    category = cat;

    if (matchedKw) {
      const idx = cleaned.toLowerCase().indexOf(matchedKw);
      note = (cleaned.substring(0, idx) + cleaned.substring(idx + matchedKw.length))
        .replace(/\s+/g, ' ')
        .trim();
    } else {
      note = cleaned;
    }
  }

  // ---- Parse log_income ----
  let source = '';
  if (intent === 'log_income') {
    const numMatch = text.match(/\d+(?:\.\d{1,2})?/);
    amount = numMatch ? parseFloat(numMatch[0]) : 0;
    source = lower
      .replace(/\d+/g, '')
      .replace(/\b(received|got|earned|rs|npr)\b/g, '')
      .trim() || 'unspecified';
  }

  // ---- Parse edit_last ----
  let editAmount = null;
  let editCategory = null;

  if (intent === 'edit_last') {
    const amtMatch = text.match(/(?:amount\s*(?:to\s*)?|to\s+)(\d+(?:\.\d{1,2})?)/i);
    if (amtMatch) editAmount = parseFloat(amtMatch[1]);

    const catMatch = text.match(/(?:was|to)\s+(\w+)/i);
    if (catMatch) {
      const possibleCat = catMatch[1].toLowerCase();
      if (ALL_CATEGORIES.includes(possibleCat)) {
        editCategory = possibleCat.charAt(0).toUpperCase() + possibleCat.slice(1);
      }
    }

    if (!editAmount && !editCategory) {
      const numMatch = text.match(/\d+(?:\.\d{1,2})?/);
      if (numMatch) editAmount = parseFloat(numMatch[0]);
    }
  }

  // ---- Parse set_budget ----
  let budgetCategory = null;
  let budgetAmount = null;
  if (intent === 'set_budget') {
    const budgetMatch = lower.match(/set\s+budget\s+(\w+)\s+(\d+)/);
    if (budgetMatch) {
      budgetCategory = matchCategory(budgetMatch[1]).category;
      budgetAmount = parseInt(budgetMatch[2], 10);
    }
  }

  // ---- Parse report ----
  let period = 'this_month';
  let categoryFilter = null;
  if (intent === 'report') {
    if (/today/.test(lower)) period = 'today';
    else if (/this\s*week/.test(lower)) period = 'this_week';
    else if (/last\s*month/.test(lower)) period = 'last_month';
    else if (/yesterday/.test(lower)) period = 'yesterday';

    const catFilter = lower.match(/(?:on|for)\s+(\w+)/);
    if (catFilter) categoryFilter = matchCategory(catFilter[1]).category;
  }

  return {
    intent,
    amount,
    category,
    note,
    tags,
    dateOffset,
    editAmount,
    editCategory,
    source,
    budgetCategory,
    budgetAmount,
    period,
    categoryFilter,
    rawMessage: text,
  };
}

// ─── n8n Code Node wrapper ──────────────────────────────────
// Uncomment the block below when pasting into an n8n Code node:
//
// const msg = $input.first().json.message;
// const result = parseMessage(msg.text);
// const esc = (s) => (s || '').replace(/'/g, "''");
// const tagsLiteral = result.tags.length > 0
//   ? '{' + result.tags.map(t => '"' + t + '"').join(',') + '}'
//   : '{}';
//
// return [{ json: {
//   chatId: msg.chat.id,
//   telegramId: msg.from.id,
//   firstName: esc(msg.from.first_name || ''),
//   username: esc(msg.from.username || ''),
//   originalMessage: esc(result.rawMessage),
//   intent: result.intent,
//   amount: result.amount,
//   category: result.category,
//   note: esc(result.note),
//   tagsLiteral,
//   dateOffset: result.dateOffset,
//   editAmount: result.editAmount,
//   editCategory: result.editCategory,
//   editQuery: '',  // build dynamically for edit intent
// }}];

// ─── Quick test ─────────────────────────────────────────────
if (typeof require !== 'undefined' && require.main === module) {
  const tests = [
    '120 food',
    'spent 500 on petrol',
    'chai 40',
    'uber 250 to office',
    '500 dinner with friends #client',
    '15000 rent',
    '120 food yesterday',
    '500 petrol 2 days ago',
    'groceries 1200 3 days ago #weekly',
    'delete last',
    'remove last',
    'undo',
    'cancel last',
    'edit last amount to 150',
    'last was transport not food',
    'change last to groceries',
    'correct last 200',
    'report today',
    'report this month',
    'how much on food this month',
    'total this week',
    'set budget food 5000',
    'received 50000 salary',
    'earned 2000 freelance',
    'help',
    '/start',
    'random text no number',
  ];

  console.log('%-45s %-15s %s', 'MESSAGE', 'INTENT', 'PARSED');
  console.log('-'.repeat(100));

  for (const t of tests) {
    const r = parseMessage(t);
    let detail = '';
    switch (r.intent) {
      case 'log_expense':
        detail = `amt=${r.amount} cat=${r.category} note="${r.note}" tags=${r.tags.join(',')} dateOffset=${r.dateOffset}`;
        break;
      case 'log_income':
        detail = `amt=${r.amount} source="${r.source}"`;
        break;
      case 'edit_last':
        detail = `editAmt=${r.editAmount} editCat=${r.editCategory}`;
        break;
      case 'report':
        detail = `period=${r.period} catFilter=${r.categoryFilter}`;
        break;
      case 'set_budget':
        detail = `cat=${r.budgetCategory} amt=${r.budgetAmount}`;
        break;
      default:
        detail = '';
    }
    console.log('%-45s %-15s %s', t, r.intent, detail);
  }
}

module.exports = { parseMessage, matchCategory, CATEGORY_KEYWORDS };
