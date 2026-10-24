"""Inventory management module — several collaborating classes (the hardest CUT).

Classes:
    Product    — an immutable catalogue item with a SKU and unit price.
    Inventory  — tracks stock levels per SKU with reservations and reorder points.
    Order      — a customer order built from order lines, with discounts.
    Warehouse  — coordinates Inventory and Orders (place, fulfil, cancel).
"""


class InventoryError(Exception):
    """Base exception for inventory errors."""


class UnknownProductError(InventoryError, KeyError):
    """Raised when a SKU is not registered."""


class OutOfStockError(InventoryError):
    """Raised when there is not enough available stock."""


class OrderStateError(InventoryError):
    """Raised when an order operation is invalid for the order's current status."""


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class Product:
    """A catalogue item. SKUs are case-insensitive and stored upper-case."""

    __slots__ = ("sku", "name", "price")

    def __init__(self, sku, name, price):
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("sku must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise TypeError("price must be numeric")
        if price < 0:
            raise ValueError("price cannot be negative")
        object.__setattr__(self, "sku", sku.strip().upper())
        object.__setattr__(self, "name", name.strip())
        object.__setattr__(self, "price", round(float(price), 2))

    def __setattr__(self, key, value):
        raise AttributeError("Product is immutable")

    def __eq__(self, other):
        return isinstance(other, Product) and self.sku == other.sku

    def __hash__(self):
        return hash(self.sku)

    def __repr__(self):
        return f"Product({self.sku!r}, {self.name!r}, {self.price})"


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

class Inventory:
    """Stock levels per product, with reserved quantities and reorder points."""

    def __init__(self):
        self._products = {}   # sku -> Product
        self._on_hand = {}    # sku -> int
        self._reserved = {}   # sku -> int
        self._reorder_at = {}  # sku -> int

    def _key(self, sku):
        key = sku.strip().upper() if isinstance(sku, str) else sku
        if key not in self._products:
            raise UnknownProductError(sku)
        return key

    @staticmethod
    def _check_qty(qty):
        if isinstance(qty, bool) or not isinstance(qty, int):
            raise TypeError("quantity must be an int")
        if qty <= 0:
            raise ValueError("quantity must be positive")

    def add_product(self, product, quantity=0, reorder_at=0):
        """Register a product with an initial quantity and reorder point."""
        if not isinstance(product, Product):
            raise TypeError("product must be a Product")
        if product.sku in self._products:
            raise InventoryError(f"duplicate sku: {product.sku}")
        if quantity < 0 or reorder_at < 0:
            raise ValueError("quantity and reorder_at cannot be negative")
        self._products[product.sku] = product
        self._on_hand[product.sku] = quantity
        self._reserved[product.sku] = 0
        self._reorder_at[product.sku] = reorder_at

    def get_product(self, sku):
        return self._products[self._key(sku)]

    def restock(self, sku, qty):
        """Increase on-hand stock."""
        self._check_qty(qty)
        key = self._key(sku)
        self._on_hand[key] += qty

    def available(self, sku):
        """On-hand stock that is not reserved."""
        key = self._key(sku)
        return self._on_hand[key] - self._reserved[key]

    def on_hand(self, sku):
        return self._on_hand[self._key(sku)]

    def reserve(self, sku, qty):
        """Reserve stock for an order. Raises OutOfStockError if not enough is available."""
        self._check_qty(qty)
        key = self._key(sku)
        if self.available(key) < qty:
            raise OutOfStockError(
                f"{key}: requested {qty}, available {self.available(key)}"
            )
        self._reserved[key] += qty

    def release(self, sku, qty):
        """Release a previous reservation."""
        self._check_qty(qty)
        key = self._key(sku)
        if qty > self._reserved[key]:
            raise InventoryError(f"{key}: cannot release more than reserved")
        self._reserved[key] -= qty

    def ship(self, sku, qty):
        """Ship reserved stock: removes it from both reserved and on-hand."""
        self._check_qty(qty)
        key = self._key(sku)
        if qty > self._reserved[key]:
            raise InventoryError(f"{key}: cannot ship more than reserved")
        self._reserved[key] -= qty
        self._on_hand[key] -= qty

    def needs_reorder(self):
        """Return sorted SKUs whose available stock is at or below the reorder point."""
        return sorted(
            sku for sku in self._products
            if self.available(sku) <= self._reorder_at[sku]
        )

    def total_value(self):
        """Total value of on-hand stock."""
        return round(
            sum(self._products[s].price * self._on_hand[s] for s in self._products), 2
        )

    def __contains__(self, sku):
        return isinstance(sku, str) and sku.strip().upper() in self._products

    def __len__(self):
        return len(self._products)


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class Order:
    """A customer order. Status flow: draft -> placed -> fulfilled, or -> cancelled."""

    DRAFT = "draft"
    PLACED = "placed"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"

    BULK_THRESHOLD = 10       # units of one line that trigger the bulk discount
    BULK_DISCOUNT = 0.05      # 5% off that line
    MAX_COUPON = 0.5          # coupons can take off at most 50%

    _next_id = 1

    def __init__(self, customer):
        if not isinstance(customer, str) or not customer.strip():
            raise ValueError("customer must be a non-empty string")
        self.customer = customer.strip()
        self.order_id = Order._next_id
        Order._next_id += 1
        self.status = Order.DRAFT
        self._lines = {}  # sku -> [product, qty]
        self._coupon = 0.0

    def _require(self, *statuses):
        if self.status not in statuses:
            raise OrderStateError(
                f"order {self.order_id} is {self.status}, expected one of {statuses}"
            )

    def add_line(self, product, qty):
        """Add qty units of product. Adding the same product again increases its quantity."""
        self._require(Order.DRAFT)
        if not isinstance(product, Product):
            raise TypeError("product must be a Product")
        Inventory._check_qty(qty)
        if product.sku in self._lines:
            self._lines[product.sku][1] += qty
        else:
            self._lines[product.sku] = [product, qty]

    def remove_line(self, sku):
        self._require(Order.DRAFT)
        key = sku.strip().upper()
        if key not in self._lines:
            raise UnknownProductError(sku)
        del self._lines[key]

    def apply_coupon(self, fraction):
        """Apply a percentage coupon (0 < fraction <= MAX_COUPON) to the subtotal."""
        self._require(Order.DRAFT)
        if not 0 < fraction <= Order.MAX_COUPON:
            raise ValueError(f"coupon must be in (0, {Order.MAX_COUPON}]")
        self._coupon = fraction

    @property
    def lines(self):
        """Return [(sku, qty), ...] sorted by sku."""
        return sorted((sku, qty) for sku, (_, qty) in self._lines.items())

    def line_total(self, sku):
        product, qty = self._lines[sku.strip().upper()]
        total = product.price * qty
        if qty >= Order.BULK_THRESHOLD:
            total *= 1 - Order.BULK_DISCOUNT
        return round(total, 2)

    def subtotal(self):
        return round(sum(self.line_total(sku) for sku in self._lines), 2)

    def total(self):
        return round(self.subtotal() * (1 - self._coupon), 2)

    def __len__(self):
        return len(self._lines)


# ---------------------------------------------------------------------------
# Warehouse
# ---------------------------------------------------------------------------

class Warehouse:
    """Coordinates an Inventory with customer Orders."""

    def __init__(self, inventory=None):
        self.inventory = inventory if inventory is not None else Inventory()
        self._orders = {}  # order_id -> Order

    def place_order(self, order):
        """Reserve stock for every line and mark the order as placed.

        All-or-nothing: if any line cannot be reserved, earlier reservations
        are released and OutOfStockError is raised.
        """
        if not isinstance(order, Order):
            raise TypeError("order must be an Order")
        order._require(Order.DRAFT)
        if len(order) == 0:
            raise OrderStateError("cannot place an empty order")

        reserved = []
        try:
            for sku, qty in order.lines:
                self.inventory.reserve(sku, qty)
                reserved.append((sku, qty))
        except InventoryError:
            for sku, qty in reserved:
                self.inventory.release(sku, qty)
            raise

        order.status = Order.PLACED
        self._orders[order.order_id] = order
        return order.order_id

    def fulfil(self, order_id):
        """Ship every line of a placed order."""
        order = self.get_order(order_id)
        order._require(Order.PLACED)
        for sku, qty in order.lines:
            self.inventory.ship(sku, qty)
        order.status = Order.FULFILLED

    def cancel(self, order_id):
        """Cancel a placed order and release its reservations."""
        order = self.get_order(order_id)
        order._require(Order.PLACED)
        for sku, qty in order.lines:
            self.inventory.release(sku, qty)
        order.status = Order.CANCELLED

    def get_order(self, order_id):
        if order_id not in self._orders:
            raise InventoryError(f"unknown order id: {order_id}")
        return self._orders[order_id]

    def orders_by_status(self, status):
        """Return order ids with the given status, in ascending order."""
        return sorted(oid for oid, o in self._orders.items() if o.status == status)

    def revenue(self):
        """Total value of fulfilled orders."""
        return round(
            sum(o.total() for o in self._orders.values() if o.status == Order.FULFILLED), 2
        )
