# Expense Splitter API

A REST API to split bills among friends and compute the **minimum number of transactions** needed to settle all debts — like a backend for Splitwise.

**Live Demo:** `https://expense-splitter-api.onrender.com/docs`
---
Note: If accessing the live API link, please allow 30-45 seconds for the free-tier hosting instance to wake up from a cold start." Interviewers are completely used to this and appreciate the heads-up.
## Architecture

```
expense-splitter/
├── app/
│   ├── main.py                  # FastAPI app, router registration
│   ├── models/
│   │   └── database.py          # MySQL connection pool, table creation
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   ├── groups.py            # CRUD for groups
│   │   ├── members.py           # CRUD for members
│   │   ├── expenses.py          # Add/list/delete expenses with split validation
│   │   └── settlements.py       # GET /settle — runs debt minimisation
│   └── services/
│       └── settlement.py        # Greedy algorithm (O(n log n))
├── Dockerfile
├── render.yaml
└── requirements.txt
```

---

## The Algorithm — Debt Minimisation

**Problem:** N people have expenses. After computing net balances, find the minimum number of bank transfers to settle all debts.

**Approach:** Greedy two-pointer using max-heaps.

1. Compute each person's net balance (paid − owed)
2. Split into creditors (positive balance) and debtors (negative balance)
3. At each step: pair the **largest creditor** with the **largest debtor**
4. Transfer `min(credit, debt)` — one of them hits zero and is eliminated
5. Repeat until all balances are zero

**Complexity:** O(n log n) — dominated by heap operations

**Example:**
```
Alice paid ₹300, Bob paid ₹0, Charlie paid ₹0 (equal split ₹100 each)
Net: Alice +200, Bob -100, Charlie -100

Step 1: Bob pays Alice ₹100  → Alice +100, Bob 0  ✓
Step 2: Charlie pays Alice ₹100 → Alice 0, Charlie 0 ✓

Result: 2 transactions (optimal)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/groups/` | Create a group |
| GET | `/groups/` | List all groups |
| GET | `/groups/{id}` | Get group details |
| DELETE | `/groups/{id}` | Delete group |
| POST | `/groups/{id}/members` | Add member to group |
| GET | `/groups/{id}/members` | List members |
| DELETE | `/groups/{id}/members/{mid}` | Remove member |
| POST | `/groups/{id}/expenses` | Add expense with splits |
| GET | `/groups/{id}/expenses` | List all expenses |
| DELETE | `/groups/{id}/expenses/{eid}` | Delete expense |
| GET | `/groups/{id}/settle` | **Get minimum settlement plan** |
| GET | `/groups/{id}/balances` | Get each member's net balance |

Full interactive docs available at `/docs` (Swagger UI).

---

## Local Setup

```bash
# 1. Clone and install
git clone https://github.com/vishvjain-vj/expense-splitter
cd expense-splitter
pip install -r requirements.txt

# 2. Create MySQL database
mysql -u root -p -e "CREATE DATABASE expense_splitter;"

# 3. Set environment variables
cp .env.example .env
# Edit .env with your MySQL credentials

# 4. Run
uvicorn app.main:app --reload

# 5. Open docs
# http://localhost:8000/docs
```

---

## Deploy on Render (Free)

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your repo
4. Add environment variables: `DB_HOST`, `DB_USER`, `DB_PASSWORD`
5. For the database: Render → New → MySQL (free tier) or use [PlanetScale](https://planetscale.com) (free MySQL in cloud)
6. Deploy — Render uses the `Dockerfile` automatically

---

## Example Usage

```bash
# Create a group
curl -X POST http://localhost:8000/groups/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Goa Trip", "description": "June 2025"}'

# Add members
curl -X POST http://localhost:8000/groups/1/members \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Add expense (Alice paid ₹300, split equally among 3)
curl -X POST http://localhost:8000/groups/1/expenses \
  -d '{
    "paid_by": 1,
    "description": "Hotel",
    "amount": 300,
    "splits": [
      {"member_id": 1, "share": 100},
      {"member_id": 2, "share": 100},
      {"member_id": 3, "share": 100}
    ]
  }'

# Get settlement plan
curl http://localhost:8000/groups/1/settle
# → {"transactions": [{"from": "Bob", "to": "Alice", "amount": 100}, ...]}
```

---

## Tech Stack

- **FastAPI** — REST API framework with auto Swagger docs
- **MySQL** — persistent storage with connection pooling
- **Pydantic v2** — request validation and serialisation
- **Docker** — containerised, non-root, multi-stage build
- **Render** — free cloud deployment
