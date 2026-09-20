# Business Sales & Inventory Management System (BSIMS)

A complete, internship-scale web application for small/medium businesses to
manage products, inventory, sales, purchases, customers, suppliers,
expenses, reporting, and a simple AI sales forecast.

## Tech Stack
- **Backend**: Python 3.12+, Django 6, Django REST Framework
- **Database**: PostgreSQL (primary), SQLite (local dev fallback)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Charts**: Chart.js
- **Machine Learning**: Pandas, NumPy, scikit-learn (Linear Regression sales forecast)
- **Auth**: Django's built-in authentication + custom role-based permissions

## Feature Checklist (all phases complete)
- [x] Authentication (login/logout, password change, profile)
- [x] Role-based access control (Admin / Manager / Employee), enforced on the backend
- [x] Dashboard — KPI cards, sales trend chart, top products, low stock, recent transactions
- [x] Product & Category management (CRUD, search/filter/sort/pagination)
- [x] Customer management (CRUD, purchase history, spend summary)
- [x] Supplier management (CRUD, supplied products, purchase history)
- [x] Purchase management (multi-item, pending → complete workflow, auto stock increase)
- [x] Sales management (POS-style, stock validation, auto stock decrease, cancel/restore)
- [x] Professional printable invoice
- [x] Inventory page + full stock movement history + manual adjustments
- [x] Expense management (category + date filters)
- [x] Reports: Sales, Product Sales, Customer, Inventory, Expense, Profit
- [x] REST API (Django REST Framework) for all core resources
- [x] AI sales forecasting (Linear Regression, historical vs. forecast chart)
- [x] Notifications (low stock / out of stock / high expense, auto-resolving)
- [x] Custom 404 / 403 / 500 error pages
- [x] Automated test suite (`python manage.py test`)
- [x] Environment-variable based secrets (`.env`), production security settings

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit values as needed (SECRET_KEY, DB settings)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then visit **http://127.0.0.1:8000** and log in with the superuser account you created.
Newly created superusers default to role `EMPLOYEE` at the database level unless you set
the role explicitly — after creating one, either:
```bash
python manage.py shell -c "from accounts.models import User; u = User.objects.get(username='YOUR_USERNAME'); u.role='ADMIN'; u.save()"
```

### Demo data (recommended for a viva/demo)
Populates ~6 months of realistic sales, products, customers, suppliers, purchases and expenses:
```bash
python manage.py seed_demo_data --months 6
```

### Using PostgreSQL instead of SQLite
Set in `.env`:
```
DB_ENGINE=postgres
DB_NAME=bsims_db
DB_USER=bsims_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### Running tests
```bash
python manage.py test
```

## User Roles
| Role | Access |
|---|---|
| **Admin** | Everything, including user management and AI Forecast |
| **Manager** | Products, categories, customers, suppliers, purchases, sales, inventory, expenses, reports |
| **Employee** | View products/inventory, manage sales, view/add customers only |

Permissions are enforced on the backend (decorators/mixins in `accounts/permissions.py`),
not just by hiding UI buttons.

## REST API
Base path: `/api/`. Browsable API login at `/api-auth/login/`.
Endpoints: `categories`, `products`, `customers`, `suppliers`, `purchases` (read-only),
`sales` (read-only), `inventory-transactions` (read-only), `expenses`, `notifications`,
plus `dashboard/summary/` for KPI JSON.

## Project Structure

```
business_management/
├── manage.py
├── config/          # settings, urls, error handlers, shared form mixin
├── accounts/        # custom user model, auth, roles, profile, permissions
├── products/        # products + categories
├── customers/
├── suppliers/
├── purchases/
├── sales/           # POS-style sales + printable invoice
├── inventory/       # stock levels + stock movement history + adjustments
├── expenses/
├── reports/         # sales/product/customer/inventory/expense/profit reports
├── forecasting/      # ML sales forecasting pipeline
├── dashboard/
├── notifications/
├── api/             # Django REST Framework serializers/viewsets
├── templates/
├── static/
├── media/
├── requirements.txt
├── .env.example
└── .gitignore
```

## Notes for Presentation / Viva
- **Stock integrity**: every stock-changing action (purchase completion, sale, manual
  adjustment) creates an `InventoryTransaction` record — a full audit trail, viewable
  under Inventory → Stock History.
- **Purchases** use a Pending → Completed workflow so stock is only affected once,
  intentionally, and can't be double-applied.
- **Sales** are POS-style: stock is checked and decremented immediately, with a clear
  "Insufficient stock" error if the requested quantity isn't available.
- **Forecasting** is a deliberately simple, explainable pipeline (aggregate → clean →
  Linear Regression → predict → visualize) rather than a black box — good for explaining
  the ML flow in a viva.
- **Notifications** are event-driven (created at the moment stock/expenses change) and
  self-resolving (a low-stock alert clears itself once stock recovers), rather than a
  polling job — reasonable for this project's scale.
