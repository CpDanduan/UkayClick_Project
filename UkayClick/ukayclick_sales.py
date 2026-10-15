from datetime import datetime
from ukayclick_storage import load_transactions, save_transactions
from ukayclick_inventory import Product

class Transaction:
    def __init__(self, transaction_id: str, date_time: datetime):
        self._transaction_id = transaction_id
        self._date_time = date_time

    def get_amount(self) -> float:
        raise NotImplementedError

class SalesTransaction(Transaction):
    def __init__(self, transaction_id: str, date_time: datetime, customer: str, product: Product,
                 quantity: int, amount_paid: float, payment_method: str):
        super().__init__(transaction_id, date_time)
        self.__customer = customer.strip() or "Walk-in"
        self.__product = product
        self.__quantity = int(quantity)
        self.__unit_price = product.price
        self.__total = self.__unit_price * self.__quantity
        self.__amount_paid = float(amount_paid)
        self.__payment_method = payment_method
        self.__change = self.calculate_change()

    def calculate_total(self) -> float: return round(self.__total, 2)
    def calculate_change(self) -> float:
        paid = self.__amount_paid if self.__payment_method == "Cash" else self.__total
        return round(paid - self.__total, 2)
    def get_amount(self) -> float: return self.calculate_total()
    def complete_sale(self) -> bool:
        if self.__quantity <= 0 or not self.__product.is_available() or self.__quantity > self.__product.quantity: return False
        if self.__payment_method == "Cash" and self.__amount_paid < self.__total: return False
        if not self.__product.remove_stock(self.__quantity): return False
        return True
    def get_receipt_data(self) -> dict:
        return {"timestamp": self._date_time.strftime("%Y-%m-%d %H:%M:%S"), "transaction_id": self._transaction_id,
                "item_id": self.__product.item_id, "product": self.__product.name, "category": self.__product.category,
                "quantity": self.__quantity, "unit_price": round(self.__unit_price, 2), "total": self.calculate_total(),
                "customer": self.__customer, "payment": self.__payment_method, "amount_paid": round(self.__amount_paid, 2),
                "change": self.__change}

    @staticmethod
    def next_id():
        transactions = load_transactions()
        return f"TX{len(transactions)+1:05d}"

    def save(self):
        transactions = load_transactions(); transactions.append(self.get_receipt_data()); save_transactions(transactions)


def process_sale(inventory_manager, item_id, quantity, customer, payment, customer_payment, sale_date=None):
    product = inventory_manager.find_product(item_id)
    if product is None: return False, "Product not found."
    quantity = int(quantity)
    if quantity <= 0 or quantity > product.quantity: return False, "Invalid quantity."
    amount_paid = float(customer_payment) if payment == "Cash" else product.price * quantity
    # Preserve the current time while allowing the user to choose the sale's calendar date.
    current_time = datetime.now()
    if sale_date is not None:
        sale_datetime = datetime.combine(sale_date, current_time.time())
    else:
        sale_datetime = current_time
    sale = SalesTransaction(SalesTransaction.next_id(), sale_datetime, customer, product, quantity, amount_paid, payment)
    if payment == "Cash" and sale.calculate_change() < 0: return False, f"Insufficient payment. Amount needed: ₱{sale.calculate_total():,.2f}"
    if not sale.complete_sale(): return False, "Unable to complete sale."
    inventory_manager.update_product(product)
    sale.save()
    return True, sale.get_receipt_data()
