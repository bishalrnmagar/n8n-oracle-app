# Finance Tracker Telegram Bot

A personal finance tracking bot on Telegram. Send natural language messages like `120 food` or `spent 500 on petrol` and the bot parses the amount, detects the category, and logs it to PostgreSQL. Supports corrections, deletions, past-date entries, and budget tracking.

## Architecture

```
User (Telegram) → Telegram Bot API → n8n Webhook
                                        ↓
                                  Parse Message
                                  (Code Node)
                                        ↓
                                  Route by Intent
                              ┌─────────┼──────────────┐
                              ↓         ↓              ↓
                         Log Expense  Correction    Help/Fallback
                              ↓         ↓
                         PostgreSQL (read/write/update)
                              ↓
                         Send Confirmation via Telegram
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Bot | Telegram Bot API |
| Automation | n8n (self-hosted) |
| Database | PostgreSQL 16 |
| Hosting | Oracle Cloud Always Free Tier (ARM) |
| Reverse Proxy | Caddy 2 (auto SSL) |
| Containerization | Docker + Docker Compose |
| IaC | Terraform (OCI provider) |
| CI/CD | GitHub Actions |

## Message Formats

### Log Expense
```
120 food
spent 500 on petrol
chai 40
500 dinner with friends #client
120 food yesterday
500 petrol 2 days ago
```

### Edit / Delete
```
delete last
undo
edit last amount to 150
last was transport not food
```

### Other
```
help
/start
```

## Categories

Food, Transport, Groceries, Rent, Utilities, Entertainment, Health, Shopping, Subscriptions, Education, Misc (fallback)

## Project Structure

```
.
├── docker/
│   ├── docker-compose.yml      # n8n + PostgreSQL + Caddy
│   ├── Caddyfile               # Reverse proxy config
│   ├── .env.example            # Environment template
│   ├── setup.sh                # Server setup script
│   └── db-init/
│       └── init-finance-db.sql # Database schema
├── infra/
│   ├── compute.tf              # OCI VM instance
│   ├── network.tf              # VCN, subnet, security list
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Terraform outputs
│   ├── providers.tf            # OCI provider config
│   ├── cloud-init.yaml         # VM bootstrap script
│   └── terraform.tfvars.example
├── n8n-workflows/
│   └── AI Finance Manager.json # Main n8n workflow
├── parser/
│   ├── message_parser.js       # JS parser (for n8n Code node)
│   └── message_parser.py       # Python parser (standalone/testing)
└── .github/workflows/
    ├── ci.yml                  # Code quality checks
    └── ai-review.yml           # AI code review on PRs
```

## Database Schema

PostgreSQL tables in the `finance` database:

- **users** — Telegram user mapping (`telegram_id` → internal UUID)
- **transactions** — All expenses with soft-delete support
- **categories** — Per-user category keywords (with system defaults)
- **income** — Income entries
- **budgets** — Monthly budget limits per category
- **recurring** — Auto-logged recurring expenses
- **user_settings** — Per-user preferences

## Setup

### 1. Infrastructure (Terraform)

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Fill in your OCI credentials, tokens, and passwords
terraform init
terraform apply
```

### 2. Server (Docker)

SSH into the VM (Terraform outputs the IP):

```bash
ssh ubuntu@<your-vm-ip>
cd ~/finance-bot
cp .env.example .env
# Fill in your passwords
docker compose up -d
```

### 3. n8n Workflow

1. Open `https://<your-subdomain>.duckdns.org`
2. Import `n8n-workflows/AI Finance Manager.json`
3. Update credential IDs for Postgres and Telegram nodes:
   ```bash
   sed -i 's/YOUR_POSTGRES_CREDENTIAL_ID/<your-id>/g; s/YOUR_TELEGRAM_CREDENTIAL_ID/<your-id>/g' AI\ Finance\ Manager.json
   ```
4. Activate the workflow

### 4. Telegram Bot

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Set the webhook:
   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<subdomain>.duckdns.org/webhook/telegram
   ```

## CI/CD

### Code Quality (`ci.yml`)

Runs on every push/PR to `main`:
- **Secrets scan** — TruffleHog checks for leaked credentials
- **JSON lint** — Validates n8n workflow JSON
- **JS lint** — ESLint on parser code
- **Python lint** — Ruff check + format
- **Terraform validate** — `fmt -check` + `validate`
- **SQL check** — Runs init script against a test Postgres instance
- **Safety check** — Verifies no `.tfstate`, `.env`, `.pem` files are tracked

### AI Code Review (`ai-review.yml`)

Runs on every PR — uses Claude to review for security issues, workflow correctness, and edge cases.

**Setup:** Add `ANTHROPIC_API_KEY` to your repo secrets:
> Settings → Secrets and variables → Actions → New repository secret

## Cost

$0/month — runs entirely on Oracle Cloud Always Free Tier.

## License

MIT
