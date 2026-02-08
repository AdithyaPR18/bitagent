# BitAgent - Bitcoin-Native AI Agent Operating System

> AI agents that autonomously manage Lightning wallets, pay for API access via the L402 protocol, build on-chain reputation, and make intelligent spending decisions — all powered by Bitcoin.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![React](https://img.shields.io/badge/React-18-61dafb?logo=react)
![Bitcoin](https://img.shields.io/badge/Bitcoin-Lightning-f7931a?logo=bitcoin)
![Stacks](https://img.shields.io/badge/Stacks-Clarity-5546ff)
![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-f89939?logo=scikit-learn)

---

## What Is This?

BitAgent is a full-stack platform demonstrating **machine-to-machine payments** using Bitcoin Lightning Network. An AI agent:

1. **Gets a task** — "What's the weather in New Haven?"
2. **Calls an API** — receives `402 Payment Required` + a Lightning invoice
3. **Decides whether to pay** — evaluates budget, priority, and price
4. **Pays via Lightning** — sends satoshis, gets cryptographic proof
5. **Receives data** — presents proof, gets the weather data
6. **Builds reputation** — payment history recorded on-chain via Stacks/Clarity

All of this happens **autonomously** — no human in the loop.

## Demo

```
Task: "What's the weather in New Haven?" (priority: high)
  🤔 Routing query to /api/weather/new-haven
  🔍 Calling API...
  🤔 Received 402 Payment Required — price: 10 sats
  🤔 Payment approved: 10 sats (priority: high, budget: OK)
  ⚡ Paid 10 sats via Lightning (balance: 9990)
  ✅ Data received successfully!

Task: "ETH price" (priority: low)
  🤔 Routing query to /api/stocks/ETH
  🔍 Calling API...
  🤔 Received 402 Payment Required — price: 15 sats
  ❌ Declined: 15 sats exceeds low priority threshold of 10 sats
```

The agent **paid** for high-priority weather data but **declined** a low-priority stock query that was too expensive. Autonomous economic reasoning.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Dashboard                        │
│  Balance · Payments · Reputation · Task History          │
│  WebSocket ←──── real-time updates                       │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / WS
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ L402     │  │ Mock     │  │ ML Models            │  │
│  │ Midware  │  │ APIs     │  │ · Dynamic Pricing    │  │
│  │          │◄─┤ Weather  │  │ · Credit Scoring     │  │
│  │ Invoice  │  │ Stocks   │  └──────────────────────┘  │
│  │ Macaroon │  │ News     │                              │
│  │ Verify   │  └──────────┘  ┌──────────────────────┐  │
│  └──────────┘                │ AI Agent             │  │
│                              │ · Wallet             │  │
│  ┌──────────────────────┐    │ · Decision Maker     │  │
│  │ Stacks/Clarity       │    │ · Query Router       │  │
│  │ Reputation Contract  │◄───┤ · Task Executor      │  │
│  └──────────────────────┘    └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  Lightning Network   │
              │  (Mock / LND Node)   │
              └─────────────────────┘
```

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python3 app.py
# API on http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard on http://localhost:5173
```

### Run the Demo

```bash
# With the backend running:
cd scripts
python3 demo.py
```

Or open the dashboard and click **"Run Full Demo"** to watch it live.

## L402 Protocol

L402 leverages HTTP `402 Payment Required` — a status code reserved since 1997 but never standardized until now.

```
Client                              Server
  │                                    │
  │  GET /api/weather/new-haven        │
  │ ──────────────────────────────────>│
  │                                    │
  │  402 Payment Required              │
  │  WWW-Authenticate: L402            │
  │    macaroon="<signed_token>"       │
  │    invoice="lnbc100n1..."          │
  │ <──────────────────────────────────│
  │                                    │
  │  [Pay Lightning invoice → preimage]│
  │                                    │
  │  GET /api/weather/new-haven        │
  │  Authorization: L402 mac:preimage  │
  │ ──────────────────────────────────>│
  │                                    │
  │  200 OK + weather data             │
  │ <──────────────────────────────────│
```

**Macaroons** are cryptographic tokens (HMAC-signed JSON) that encode payment metadata: which endpoint, how much was paid, when it expires. They're tamper-proof — only the server can create them.

## ML Models

### Dynamic Pricing (Gradient Boosting Regressor)

Predicts optimal price per API call in real-time.

| Feature | Description |
|---------|-------------|
| `hour_sin`, `hour_cos` | Cyclic time encoding (peak vs off-peak) |
| `server_load` | Current server utilization (0–1) |
| `cache_age` | Seconds since data was last refreshed |
| `user_total_calls` | Agent's historical API call count |
| `user_avg_payment` | Agent's average payment amount |
| `endpoint_complexity` | Compute cost of the endpoint (1–5) |

**Performance:** MAE = 0.87 sats, R² = 0.97 (trained on 10K synthetic samples)

### Credit Scoring (Logistic Regression + Gradient Boosting)

Two models: (1) predict credit score 0–100, (2) predict payment likelihood.

| Score Range | Tier | API Discount |
|------------|------|-------------|
| 81–100 | Gold | 30% off |
| 61–80 | Silver | 20% off |
| 31–60 | Bronze | 10% off |
| 0–30 | Unrated | No discount |

## Smart Contract (Stacks/Clarity)

On-chain reputation tracking at `backend/blockchain/reputation.clar`:

```clarity
;; Score = 40% success rate + 30% volume + 30% spending
(define-public (record-payment (agent-id ...) (amount-sats uint) ...)
  ;; Updates score, logs payment, recalculates tier
)

(define-read-only (get-discount-tier (agent-id ...))
  ;; Returns discount percentage based on reputation
)
```

The contract is ready to deploy on Stacks testnet. The backend includes a mock client that mirrors the on-chain logic for demo purposes.

## Agent Decision-Making

The agent evaluates every payment against four criteria:

```
1. BALANCE    — Can I afford it?
2. BUDGET     — Am I under my hourly spending limit?
3. PRIORITY   — Is the price reasonable for this task's importance?
                 low: ≤10 sats | normal: ≤30 | high: ≤70 | critical: ≤200
4. RESERVE    — Am I running low? (conserve for critical tasks)
```

## API Endpoints

| Endpoint | Auth | Price | Description |
|----------|------|-------|-------------|
| `GET /api/weather/{city}` | L402 | 10 sats | Weather data |
| `GET /api/stocks/{symbol}` | L402 | 15 sats | Stock/crypto prices |
| `GET /api/news/` | L402 | 8 sats | News headlines |
| `POST /agent/task` | — | — | Execute agent task |
| `GET /agent/status` | — | — | Agent status & wallet |
| `GET /ml/pricing/predict` | — | — | Dynamic price prediction |
| `GET /ml/credit/score` | — | — | Credit score assessment |
| `GET /reputation/{id}` | — | — | On-chain reputation |
| `WS /ws` | — | — | Real-time updates |

## Project Structure

```
bitagent/
├── backend/
│   ├── app.py                     # FastAPI main app
│   ├── config.py                  # Settings & environment
│   ├── l402/
│   │   ├── middleware.py          # L402 protocol (@l402_required decorator)
│   │   ├── invoice.py             # Lightning invoice creation & settlement
│   │   └── verification.py        # Macaroon signing & verification
│   ├── api/
│   │   ├── weather.py             # Mock weather API (L402-gated)
│   │   ├── stocks.py              # Mock stock API (L402-gated)
│   │   └── news.py                # Mock news API (L402-gated)
│   ├── agent/
│   │   ├── langchain_agent.py     # AI agent with autonomous payment
│   │   ├── wallet.py              # Lightning wallet management
│   │   └── decision_maker.py      # Pay/don't-pay evaluation logic
│   ├── ml/
│   │   ├── dynamic_pricing.py     # Gradient Boosting price predictor
│   │   ├── credit_scoring.py      # Credit score + will-pay predictor
│   │   └── training_data.py       # Synthetic data generation (10K samples)
│   └── blockchain/
│       ├── reputation.clar        # Stacks/Clarity smart contract
│       └── stacks_client.py       # On-chain reputation client
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── AgentDashboard.tsx  # Main dashboard with all panels
│       │   ├── PaymentStream.tsx   # Real-time Lightning payment feed
│       │   ├── ReputationCard.tsx  # On-chain reputation visualization
│       │   └── ApiCallHistory.tsx  # Agent task log with action details
│       └── hooks/
│           └── useWebSocket.ts    # Auto-reconnecting WebSocket hook
├── scripts/
│   ├── demo.py                    # Full lifecycle demo script
│   └── train_models.py            # Train & evaluate ML models
└── README.md
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9+, FastAPI, uvicorn |
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Recharts |
| ML | scikit-learn (Gradient Boosting, Logistic Regression) |
| Lightning | LND REST API (mock for demo) |
| Blockchain | Stacks / Clarity smart contracts |
| Real-time | WebSocket |

## Configuration

Copy `.env.example` to `backend/.env`:

```env
USE_MOCK_LIGHTNING=true   # Set false + configure LND for real payments
USE_MOCK_LLM=true         # Set false + add OPENAI_API_KEY for real LLM routing
LND_REST_HOST=https://localhost:8080
STACKS_API_URL=http://localhost:3999
```

## License

MIT
