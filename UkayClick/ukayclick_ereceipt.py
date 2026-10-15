class EReceipt:
    def __init__(self, transaction):
        self.__receipt_id = transaction["transaction_id"]
        self.__transaction = transaction
    def generate(self) -> str:
        sale=self.__transaction
        return f"""UKAYCLICK — E-RECEIPT
------------------------------
Transaction: {sale['transaction_id']}
Date:        {sale['timestamp']}
Customer:    {sale['customer']}

Product:     {sale['product']}
Category:    {sale['category']}
Quantity:    {sale['quantity']}
Unit Price:  ₱{sale['unit_price']:,.2f}
Amount Paid: ₱{sale.get('amount_paid', sale['total']):,.2f}
Change:      ₱{sale['change']:,.2f}
TOTAL:       ₱{sale['total']:,.2f}

Payment:     {sale['payment']}
------------------------------
Thank you for shopping at UkayClick!""".strip()
    def print_receipt(self) -> None: print(self.generate())

def receipt_text(sale): return EReceipt(sale).generate()
