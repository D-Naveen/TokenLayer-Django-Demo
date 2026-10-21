# TokenLayer — Django + SQLite Demo

A polished, interactive demonstration of the TokenLayer real-world asset tokenization workflow described in the supplied 34-page task PDF.

## What is included

- Role-based demo accounts: Platform Admin, Issuer, Investor, Compliance Officer and Custodian.
- Dashboard, asset registry and asset creation form with optional document upload.
- Issuer asset submission and compliance approve/reject workflow.
- Token configuration: token name/symbol/type, supply, price, minimum purchase, transferability and lock-up.
- Simulated smart-contract deployment with a generated demo reference.
- Demo token minting and supply checks.
- Marketplace, simulated investment, payment confirmation, token allocation and investor portfolio.
- Audit log for important user actions.
- Django admin console and SQLite database.
- Responsive interface designed for desktop and mobile.

## Important demo limitation

This is a **demo/sandbox**, not a production financial platform. Contract deployment, KYC/AML, payment, compliance, custody, settlement and token transfers are simulated. There is no blockchain connection, real payment gateway, external identity verification, real-money investment, or legal/regulatory validation. The sample assets and yields are fictional. Do not use real personal or financial data. The included development secret key and `DEBUG=True` are for local demo use only.

## Requirements

- Python 3.10+
- pip

## Run on Windows

Open Command Prompt or the VS Code terminal in the project folder:

```bat
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Then open **http://127.0.0.1:8000/**.

If `py` is unavailable, use `python` in place of `py` for creating the virtual environment.

## Demo logins

All demo accounts use password **`Demo@123`**.

| Role | Username |
|---|---|
| Platform Admin | `admin` |
| Issuer | `issuer` |
| Investor | `investor` |
| Compliance Officer | `compliance` |
| Custodian | `custodian` |

The login page has buttons that fill the demo credentials automatically.

## Recommended end-to-end walkthrough

1. Sign in as `issuer` and open **Asset registry**.
2. Open the sample draft **Deccan Logistics Hub** and select **Submit for review**.
3. Sign out, sign in as `compliance`, open the submitted asset, then approve it.
4. Sign in as `issuer`, open the approved asset and configure its token.
5. Simulate contract deployment, then mint tokens.
6. Open **Marketplace** as `investor`, select a live asset and confirm a demo investment.
7. Open **My portfolio** and **Audit trail** to verify the simulated allocation and recorded actions.
8. Sign in as `admin` to inspect the Django admin console.

Seeded live sample assets are already available in Marketplace so the investor flow can also be demonstrated immediately.

## Project structure

```text
 tokenlayer_demo/
 ├── manage.py
 ├── requirements.txt
 ├── README.md
 ├── tokenlayer/
 │   ├── settings.py
 │   ├── urls.py
 │   └── wsgi.py
 └── core/
     ├── models.py          # Profiles, assets, tokens, investments, audit logs
     ├── views.py           # Workflow and role-aware views
     ├── admin.py
     ├── management/commands/seed_demo.py
     ├── templates/core/    # Pages and role workflows
     └── static/core/       # Responsive CSS and JavaScript
```

## Reset demo data

To start fresh, stop the server, delete `db.sqlite3` and the generated `core/migrations/0001_initial.py` only if you intend to regenerate migrations, then run the setup commands again. Normally, keep the migration file and simply delete `db.sqlite3`, then run `python manage.py migrate` and `python manage.py seed_demo`.
