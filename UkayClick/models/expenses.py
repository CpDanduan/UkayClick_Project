from datetime import datetime
from repositories.json_repository import load_expenses, save_expenses
from models.sales import Transaction

class Expense(Transaction):
    def __init__(self, expense_id: str, date_time: datetime, category: str, description: str, amount: float):
        super().__init__(expense_id, date_time)
        self.__expense_id = expense_id
        self.__category = category
        self.__description = description.strip() or category
        self.__amount = float(amount)
    def validate(self) -> bool: return self.__amount > 0
    def get_amount(self) -> float: return round(self.__amount, 2)
    def to_dict(self):
        return {"timestamp": self._date_time.strftime("%Y-%m-%d %H:%M:%S"), "expense_id": self.__expense_id,
                "category": self.__category, "description": self.__description, "amount": self.get_amount()}

class ExpenseManager:
    def record_expense(self, category, description, amount, expense_date=None):
        if float(amount) <= 0: return False, "Expense must be greater than ₱0.00."
        expenses = load_expenses()
        current_time = datetime.now()
        selected_date = expense_date or current_time.date()
        expense_datetime = datetime.combine(selected_date, current_time.time())
        expense = Expense(f"EX{len(expenses)+1:05d}", expense_datetime, category, description, amount)
        if not expense.validate(): return False, "Invalid expense."
        expenses.append(expense.to_dict()); save_expenses(expenses)
        return True, "Expense recorded."
