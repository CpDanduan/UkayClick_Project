from repositories.json_repository import load_inventory, save_inventory

class Product:
    def __init__(self, item_id: str, name: str, category: str, price: float, cost: float, quantity: int):
        self.__item_id = item_id
        self.__name = name
        self.__category = category
        self.__price = float(price)
        self.__cost = float(cost)
        self.__quantity = int(quantity)

    @property
    def item_id(self): return self.__item_id
    @property
    def name(self): return self.__name
    @property
    def category(self): return self.__category
    @property
    def price(self): return self.__price
    @property
    def cost(self): return self.__cost
    @property
    def quantity(self): return self.__quantity

    def add_stock(self, quantity: int) -> None:
        if quantity > 0: self.__quantity += quantity

    def remove_stock(self, quantity: int) -> bool:
        if quantity <= 0 or quantity > self.__quantity: return False
        self.__quantity -= quantity
        return True

    def update_price(self, price: float) -> None:
        if price > 0: self.__price = float(price)

    def update_quantity(self, quantity: int) -> None:
        if quantity >= 0: self.__quantity = int(quantity)

    def is_available(self) -> bool: return self.__quantity > 0
    def get_stock_value(self) -> float: return self.__price * self.__quantity

    def to_dict(self):
        return {"item_id": self.item_id, "name": self.name, "category": self.category,
                "price": round(self.price, 2), "quantity": self.quantity, "cost": round(self.cost, 2)}

class InventoryManager:
    def __init__(self):
        self.__products = [Product(x["item_id"], x["name"], x["category"], x["price"], x.get("cost", 0), x["quantity"]) for x in load_inventory()]

    def _save(self): save_inventory([p.to_dict() for p in self.__products])
    def get_products(self): return list(self.__products)
    def add_product(self, product: Product) -> bool:
        self.__products.append(product); self._save(); return True
    def remove_product(self, item_id: str) -> bool:
        old = len(self.__products); self.__products = [p for p in self.__products if p.item_id != item_id]
        if len(self.__products) == old: return False
        self._save(); return True
    def update_product(self, product: Product) -> bool:
        for i, p in enumerate(self.__products):
            if p.item_id == product.item_id:
                self.__products[i] = product; self._save(); return True
        return False
    def find_product(self, item_id: str):
        return next((p for p in self.__products if p.item_id == item_id), None)
    def get_inventory_value(self) -> float: return sum(p.get_stock_value() for p in self.__products)
    def get_low_stock(self): return [p for p in self.__products if p.quantity <= 2]
    def next_item_id(self):
        nums = [int(p.item_id[2:]) for p in self.__products if p.item_id.startswith("UK")]
        return f"UK{(max(nums or [0]) + 1):04d}"
