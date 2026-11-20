# EC Management Backend

A Django REST Framework backend for business economics management. It provides double-entry bookkeeping, product catalog with cost sheet calculation, inventory tracking, and a high-level business operations layer (sales, purchases, expenses, payments) with automated journal entries and financial reports.

## Tech Stack

- **Python** 3.10+
- **Django** 5.2
- **Django REST Framework** 3.16
- **Authentication** — Simple JWT (`djangorestframework-simplejwt`)
- **Database** — SQLite (default; swappable via `DATABASES` setting)
- **Testing** — pytest-django, factory-boy
- **Admin UI** — django-unfold

## Architecture

The project package lives at `ec_management/`. Three apps sit at the repo root:

| App | Role |
|-----|------|
| `ec_accounts` | Double-entry bookkeeping — `Account`, `Entry`, `Line` models. Balance is enforced on every write. |
| `products` | Product catalog, cost sheets (materials + labor), `ProductItem` inventory links, `StockMovement` tracking. |
| `business` | Business-language layer for non-accountants. Configures semantic account roles and exposes sales/purchases/expenses/payments that generate journal entries automatically. |

Dependency direction: `business → ec_accounts`, `business → products`, `products → ec_accounts`.

## Getting Started

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd ec-management-backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply migrations

```bash
python manage.py migrate
```

### 4. Configure the environment

The development defaults use SQLite and allow the local frontend at
`http://localhost:5173`. Production deployments should set:

```bash
export DJANGO_SECRET_KEY='replace-me'
export DJANGO_DEBUG=false
export DJANGO_ALLOWED_HOSTS='api.example.com'
export DJANGO_CORS_ALLOWED_ORIGINS='https://app.example.com'
export DJANGO_CSRF_TRUSTED_ORIGINS='https://app.example.com'
```

Comma-separate multiple hosts or origins. No environment file loader is
required; provide variables through the shell or deployment platform.

### 5. Create a user

```bash
python manage.py createsuperuser
```

This user can sign in to `/admin/` and obtain API tokens.

### 6. Start the development server

```bash
python manage.py runserver
```

The API is available at `http://localhost:8000/api/`.

## Authentication

All product, accounting, business, setup, and report endpoints require a JWT
access token. The token endpoints are public:

```
POST /api/auth/token/         — obtain access + refresh tokens
POST /api/auth/token/refresh/ — refresh an access token
```

Access tokens expire after **60 minutes**.

Send the access token on every data request:

```http
Authorization: Bearer <access-token>
```

## API Reference

All routes are prefixed `/api/`.

### Accounting

| Method | Path | Description |
|--------|------|-------------|
| GET / POST | `/accounting/accounts/` | List / create accounts |
| GET / PUT / PATCH / DELETE | `/accounting/accounts/{id}/` | Retrieve / update / delete an account |
| GET / POST | `/accounting/entries/` | List / create journal entries |
| GET / PUT / PATCH / DELETE | `/accounting/entries/{id}/` | Retrieve / update / delete an entry |
| POST | `/accounting/entries/{id}/void/` | Void an entry |

Journal reads include a nullable `source` object for business-generated entries,
for example `{"type": "sale", "id": 12}`. Such entries must be changed through
their business endpoint. On journal PATCH, omitting `lines` preserves them;
providing `lines` replaces the line set atomically.

### Products

| Method | Path | Description |
|--------|------|-------------|
| CRUD | `/products/materials/` | Direct materials |
| CRUD | `/products/labors/` | Direct labor rates |
| CRUD | `/products/costsheets/` | Cost sheets |
| POST | `/products/costsheets/{id}/calculate/` | Recompute cost sheet totals |
| CRUD | `/products/products/` | Products |
| GET | `/products/products/{id}/stock/` | Current stock level + movement history |
| GET / POST | `/products/stock-adjustments/` | List / create manual stock adjustments |

Cost sheets accept `material_lines` and `labor_lines`. Each line contains a
material/labor ID and positive `qty`; line IDs, line totals, and sheet totals
are read-only. Omitting either collection on PATCH preserves it and sending an
empty collection clears it. Referenced catalog records return `409 Conflict`
instead of cascading history.

### Business Operations

| Method | Path | Description |
|--------|------|-------------|
| GET / POST / PATCH | `/business/setup/` | Configure the `BusinessConfig` singleton |
| GET / POST | `/business/sales/` | List / create sales |
| POST | `/business/sales/{id}/void/` | Void a sale |
| GET / POST | `/business/purchases/` | List / create purchases |
| POST | `/business/purchases/{id}/void/` | Void a purchase |
| GET / POST | `/business/expenses/` | List / create expenses |
| POST | `/business/expenses/{id}/void/` | Void an expense |
| GET / POST | `/business/payments/` | List / create payments |
| POST | `/business/payments/{id}/void/` | Void a payment |

### Reports

All report endpoints accept optional `?start=YYYY-MM-DD&end=YYYY-MM-DD` query params.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/business/reports/summary/` | Revenue, expenses, net profit, cash / receivable / payable balances |
| GET | `/business/reports/profit-loss/` | Per-account revenue and expense breakdown |
| GET | `/business/reports/inventory/` | Per-product stock level and value |

## Business Setup

Before using business operations, initialize the singleton. POST only needs the
company identity; it creates and maps the standard chart of accounts:

```http
POST /api/business/setup/
Content-Type: application/json

{
  "company_name": "Acme Corp",
  "currency": "USD"
}
```

`GET /api/business/setup/` returns `404` until setup exists. Use PATCH with
account IDs to remap semantic roles later. Repeating POST updates company name
and currency but does not reset those remappings. Calling a business operation
without setup returns `400`.

Transaction amounts and quantities must be positive. Optional payment links are
directional: received payments may link to sales and payments made may link to
purchases. Voiding is idempotency-protected and repeated attempts return `400`.

## Report behavior

Summary and profit-and-loss monetary values are decimal strings such as
`"123.45"`. Inventory `unit_cost` and `stock_value` are also decimal strings;
`current_stock` remains an integer. Reports exclude voided journal entries,
honor inclusive `start`/`end` filters, and retain the existing average inbound
cost stock estimate. Sales do not automatically post cost of goods sold.

## Running Tests

```bash
# All tests
pytest

# Single app
pytest ec_management/ec_accounts/test_api.py

# Single test
pytest ec_management/ec_accounts/test_api.py::TestEntryAPI::test_create_balanced_entry
```

Test fixtures (`api_client`, `business_config`) and model factories (`AccountFactory`, `ProductFactory`, etc.) are defined in `conftest.py` at the repo root.
