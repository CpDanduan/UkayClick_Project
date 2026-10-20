from collections import defaultdict
from datetime import date
from repositories.json_repository import load_transactions, load_expenses

class BusinessAnalyzer:
    def __init__(self, transactions=None, expenses=None):
        self.__transactions = transactions if transactions is not None else load_transactions()
        self.__expenses = expenses if expenses is not None else load_expenses()

    def calculate_revenue(self) -> float: return sum(float(x["total"]) for x in self.__transactions)
    def calculate_expenses(self) -> float: return sum(float(x["amount"]) for x in self.__expenses)
    def calculate_net_income(self) -> float: return self.calculate_revenue() - self.calculate_expenses()
    def get_sales_summary(self) -> dict:
        today = date.today().isoformat()
        total = self.calculate_revenue(); count = len(self.__transactions)
        today_sales = sum(float(x["total"]) for x in self.__transactions if x["timestamp"].startswith(today))
        return {"today_sales": today_sales, "total_sales": total, "total_expenses": self.calculate_expenses(),
                "net_cash_flow": self.calculate_net_income(), "transaction_count": count,
                "average_sale": total / count if count else 0}
    def analyze_demand(self, inventory) -> list:
        sold = defaultdict(int)
        for t in self.__transactions: sold[t["item_id"]] += int(t["quantity"])
        results=[]
        for item in inventory:
            units=sold[item.item_id]
            level="High" if units>=10 else ("Medium" if units>=5 else "Low")
            results.append({"Item ID":item.item_id,"Product":item.name,"Current Stock":item.quantity,
                            "Units Sold":units,"Demand Estimate":level,
                            "Suggested Action":"Consider restocking" if level=="High" else ("Monitor" if level=="Medium" else "Review sales")})
        return results
    def get_product_sales_summary(self) -> list:
        """Return total units sold for each product, ordered highest to lowest."""
        sold = defaultdict(int)
        names = {}

        for transaction in self.__transactions:
            item_id = transaction.get("item_id", "")
            sold[item_id] += int(transaction.get("quantity", 0))
            names[item_id] = transaction.get("product", item_id)

        results = [
            {"Product": names[item_id], "Units Sold": quantity}
            for item_id, quantity in sold.items()
        ]

        return sorted(results, key=lambda item: item["Units Sold"], reverse=True)

    def inventory_summary(self, inventory) -> dict:
        return {"total_quantity":sum(p.quantity for p in inventory), "unique_items":len(inventory),
                "low_stock":sum(1 for p in inventory if p.quantity<=2),
                "inventory_value":sum(p.get_stock_value() for p in inventory)}
