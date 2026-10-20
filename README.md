# UkayClick — Thrift Store Manual Transaction System

UkayClick is a Python-based inventory and transaction management application designed for small thrift stores (ukay-ukay). Built with **Streamlit**, it helps store owners organize products, record sales and expenses, review transaction history, and understand business performance from recorded data.

The project uses **Object-Oriented Programming (OOP)** to organize core business entities and operations, and **JSON files** to persist account and business data locally.

## Key Features

### 1. Inventory Management
- Add products with a product ID, name, category, price, cost, and quantity.
- View, update, and remove products.
- Track available stock and identify low-stock products.
- Automatically deduct stock when a sale is completed.
- Restore the sold quantity when a sale record is deleted, when the corresponding product still exists.

### 2. Sales and E-Receipts
- Record sales by selecting a product and quantity.
- Record customer details and payment method.
- Validate stock availability and cash payments.
- Calculate sale totals and change.
- Select the sale date.
- Generate an electronic receipt for a completed sale.

### 3. Expense Tracking
- Record expenses with a date, category, description, and amount.
- Validate expense amounts before saving.
- View expense history and manage recorded expense entries.
- Display a confirmation after an expense is recorded.

### 4. Ledger and Transaction Management
- View sales and expense records in separate tables.
- Search across sales and expenses using details such as transaction ID, product, customer, category, and description.
- Filter sales history by date range, product, and payment method.
- Edit supported details or delete selected sales and expense records.
- Export filtered sales history to PDF.

### 5. Dashboard and Business Reports
- View sales and financial summaries.
- Review an inventory snapshot and recent transactions.
- Select a date range for dashboard summaries and sales overview.
- Compare sales revenue, expenses, and net income.
- Review product demand estimates and suggested actions.
- Rank products by units sold, from the most sold to the least sold.

### 6. User Accounts and Separate Business Data
- Register an account and log in.
- Store each account's inventory, sales, and expenses in its own data directory.
- Keep business records separated between accounts within the local application storage.

> **Storage note:** Data is stored in local JSON files. This is suitable for a small local project or prototype, but it is not a substitute for a production database or a server-side security boundary. Back up the `data/` directory regularly and do not commit real user data or credentials to a public repository.

## User Journey

1. **Create an account or log in.** The user registers a username and password or signs in to an existing account.
2. **Set up inventory.** The user adds products, sets their selling prices and quantities, and updates stock as needed.
3. **Process a sale.** The user selects a product, enters the quantity and customer/payment details, confirms the sale, and receives an e-receipt. UkayClick validates the transaction and updates stock.
4. **Record expenses.** The user enters an expense date, category, description, and amount, then completes the recording.
5. **Review the ledger.** The user searches, filters, reviews, edits, deletes, or exports transaction records.
6. **Analyze business performance.** The user checks the dashboard and reports to review sales, expenses, net income, inventory status, and product demand.
7. **Log out.** The user can end the session; records remain saved in the account's local data files for the next session.

## Object-Oriented Programming (OOP)

UkayClick uses the four commonly taught OOP principles as follows:

### Encapsulation
Classes combine related data with the methods that operate on it. For example, `Product` stores product details in attributes and provides methods such as `add_stock()`, `remove_stock()`, `update_price()`, and `update_quantity()` to control changes. `User`, `SalesTransaction`, and `Expense` also keep their data and behavior together.

### Inheritance
`SalesTransaction` and `Expense` inherit from the shared `Transaction` class in `ukayclick_sales.py`. The parent class provides a common transaction structure, while the child classes implement the details specific to sales or expenses.

### Polymorphism
Both `SalesTransaction` and `Expense` provide their own `get_amount()` implementation. The same method name returns the relevant amount for each transaction type, demonstrating method overriding.

### Abstraction
Methods such as `process_sale()` coordinate the validation, stock update, transaction saving, and receipt-data creation needed to complete a sale. `BusinessAnalyzer` provides methods for revenue, expenses, net income, inventory summaries, and product demand so that the interface does not need to contain all calculation logic itself.

## Project Structure

```text
UkayClick/
├── danduan_ukayclick_app.py       # Streamlit entry point
├── controllers/
│   └── app_controller.py          # Session state, account scope, navigation, and routing
├── views/
│   ├── login_view.py              # Login and account registration
│   ├── dashboard_view.py          # Dashboard and KPIs
│   ├── sales_view.py              # Process Sale interface
│   ├── inventory_view.py          # Inventory management interface
│   ├── ledger_view.py             # Ledger, search, record maintenance, and PDF export
│   ├── ledger_helpers.py           # Ledger PDF generation
│   ├── expenses_view.py           # Expense entry interface
│   ├── reports_view.py             # Reports and product analysis
│   └── common.py                  # Shared view helpers
├── models/
│   ├── inventory.py               # Product and InventoryManager
│   ├── sales.py                   # Transaction classes and sale workflow
│   ├── expenses.py                # Expense and ExpenseManager
│   ├── analytics.py               # BusinessAnalyzer and calculations
│   ├── auth.py                    # User and Authentication
│   └── ereceipt.py                # EReceipt generation
├── repositories/
│   └── json_repository.py         # JSON persistence and account-specific data paths
├── ukayclick_ui.py                # Shared styling and currency formatting
├── ukayclick_*.py                 # Compatibility wrappers for older imports
├── .gitignore
├── .env.example
├── ARCHITECTURE.md
├── requirements.txt
├── .streamlit/config.toml
└── data/                          # Created at runtime; ignored by Git
```

### Module Responsibilities

- **Views** render the Streamlit interface for each page.
- **Controllers** coordinate application actions, session state, account selection, and navigation.
- **Models** contain domain objects and business rules.
- **Repositories** handle JSON file persistence. The current prototype uses local JSON files rather than a database server.
- **`ukayclick_ui.py`** contains shared UI styling and currency formatting helpers.
- The root `ukayclick_*.py` modules are compatibility wrappers that preserve older import paths during the refactor.

## Installation and Running

### Requirements
- Python 3.10 or newer recommended
- pip
- A web browser

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

Replace `<your-repository-url>` and `<your-repository-folder>` with your GitHub repository URL and its local folder name.

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Run the application

```bash
streamlit run danduan_ukayclick_app.py
```

Streamlit will display a local URL in the terminal. Open that URL in your browser to use the application.

## Technology Stack

- **Language:** Python
- **User interface:** Streamlit
- **Data persistence:** JSON files
- **PDF export:** ReportLab
- **Architecture:** Modular Python modules and OOP business classes

## Notes and Limitations

- Product demand levels are rule-based estimates based on recorded units sold; they are not generated by a machine-learning model.
- The application stores data locally in JSON files. Multi-user separation is implemented through separate account directories, but the application has not been designed as a hardened multi-user web service.
- Before publishing this project, remove any sample or personal data from `data/`. Do not upload real passwords, customer details, sales records, or expense information to a public repository.

## Project Purpose

UkayClick aims to make everyday thrift-store recordkeeping more organized by bringing inventory management, sales, expenses, and business summaries together in one application. It is intended to help small store owners monitor stock, review financial activity, and make more informed decisions based on their recorded transactions.

## Additionals

Developer: Cristian Paul P Danduan
