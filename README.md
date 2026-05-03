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

### 4. Create a superuser (for `/admin/`)

```bash
python manage.py createsuperuser
```

### 5. Start the development server

```bash
python manage.py runserver
```

The API is available at `http://localhost:8000/api/`.

## Authentication

All endpoints are public by default (no `DEFAULT_PERMISSION_CLASSES` set). JWT tokens are available if you need to lock things down:

```
POST /api/auth/token/         — obtain access + refresh tokens
POST /api/auth/token/refresh/ — refresh an access token
```

Access tokens expire after **60 minutes**.

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

Before using any business operation endpoint, configure the `BusinessConfig` singleton by posting account IDs that map to semantic roles:

```http
POST /api/business/setup/
Content-Type: application/json

{
  "company_name": "Acme Corp",
  "currency": "USD",
  "cash_account": 1,
  "receivable_account": 2,
  "payable_account": 3,
  "revenue_account": 4,
  "inventory_account": 5,
  "expense_account": 6
}
```

Calling any service (`create_sale`, etc.) without a configured `BusinessConfig` returns `400`.

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
