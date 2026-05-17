"""SQLAlchemy models for MISS CLOVER."""
import secrets
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


# ─── Users & addresses ───────────────────────────────────────────────────────


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    # Optional login handle — primarily for staff/admin (customers use email).
    username = db.Column(db.String(80), unique=True, index=True, nullable=True)
    # Nullable: Google-OAuth users have no local password.
    password_hash = db.Column(db.String(255), nullable=True)
    oauth_provider = db.Column(db.String(20), nullable=True)  # e.g. "google"
    is_admin = db.Column(db.Boolean, default=False, nullable=False, index=True)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(40))
    newsletter_opt_in = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    addresses = db.relationship("Address", backref="user", lazy=True, cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        if not self.password_hash:
            return False  # OAuth-only account — no local password to match
        return check_password_hash(self.password_hash, raw)

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    recipient_name = db.Column(db.String(120), nullable=False)
    line1 = db.Column(db.String(255), nullable=False)
    line2 = db.Column(db.String(255))
    postcode = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(2), default="SG", nullable=False)
    phone = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


# ─── Catalog hierarchy: Collection → Series → Product(colour) ─────────────────


class Collection(db.Model):
    """Top of the hierarchy, e.g. "Signature", "Cosy". Has its own editorial
    landing page (hero, copy) and contains one or more Series."""
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, index=True, nullable=False)   # "signature"
    name = db.Column(db.String(120), nullable=False)                           # "Signature"
    description = db.Column(db.Text)

    color_hex = db.Column(db.String(7))
    tile_eyebrow = db.Column(db.String(120))
    tile_headline = db.Column(db.String(255))
    tile_body = db.Column(db.Text)
    hero_image_path = db.Column(db.String(255))               # relative to static/img/

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    display_order = db.Column(db.Integer, default=100, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    series = db.relationship("Series", backref="collection", lazy=True,
                             cascade="all, delete-orphan",
                             order_by="Series.display_order")

    @property
    def active_series(self):
        return [s for s in self.series if s.is_active]


class Series(db.Model):
    """Middle of the hierarchy, e.g. "Clover", "Pillow". Belongs to one
    Collection and groups the colour-variant Products beneath it."""
    __tablename__ = "series"

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey("collections.id"),
                              nullable=False, index=True)
    slug = db.Column(db.String(80), index=True, nullable=False)   # "clover", "pillow"
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)

    color_hex = db.Column(db.String(7))
    tile_eyebrow = db.Column(db.String(120))
    tile_headline = db.Column(db.String(255))
    tile_body = db.Column(db.Text)
    hero_image_path = db.Column(db.String(255))

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    display_order = db.Column(db.Integer, default=100, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("collection_id", "slug", name="uq_series_collection_slug"),
    )

    # NOTE: no delete-orphan cascade — deleting a Series must not delete Products
    # (orders reference variants → products). Deleting a Collection cascades to
    # its Series only; affected Products are left with series_id = NULL.
    products = db.relationship("Product", backref="series", lazy=True,
                               order_by="Product.display_order")

    @property
    def active_products(self):
        return [p for p in self.products if p.is_active]


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, index=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    design_code = db.Column(db.String(40), unique=True, index=True)  # bare colour key: "classic", "maroon", "sand", "thyme"
    bag_type = db.Column(db.String(40), index=True, default="tote", nullable=False)  # tote, shoulderbag, crossbody, satchel... (orthogonal to series)
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=True, index=True)
    base_price_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), default="SGD", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Visual / merchandising fields — drive header nav, home tiles, and collection landing
    color_hex = db.Column(db.String(7))                   # e.g. "#F0E6D2", "#6E1A2D"
    tile_eyebrow = db.Column(db.String(120))              # Short label, e.g. "The Classic"
    tile_headline = db.Column(db.String(255))             # Marketing headline
    tile_body = db.Column(db.Text)                        # Marketing paragraph
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    display_order = db.Column(db.Integer, default=100, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    variants = db.relationship("ProductVariant", backref="product", lazy=True,
                               cascade="all, delete-orphan")
    images = db.relationship("ProductImage", backref="product", lazy=True,
                             cascade="all, delete-orphan",
                             order_by="ProductImage.sort_order")

    @property
    def collection(self):
        """Convenience hop up the hierarchy. None if the product is unassigned."""
        return self.series.collection if self.series else None

    @property
    def primary_variant(self):
        return self.variants[0] if self.variants else None

    @property
    def primary_image(self):
        return self.images[0] if self.images else None

    @property
    def primary_image_path(self) -> str:
        """Path under static/img/. Falls back to the legacy
        `products/<design_code>.jpg` convention if no images are attached."""
        if self.primary_image:
            return self.primary_image.path
        return f"products/{self.design_code}.jpg"

    @property
    def price_display(self) -> str:
        cents = self.primary_variant.price_cents if self.primary_variant else self.base_price_cents
        return f"S${cents / 100:,.2f}"


class ProductVariant(db.Model):
    __tablename__ = "product_variants"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(80), unique=True, index=True, nullable=False)
    stock_qty = db.Column(db.Integer, default=0, nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    # When stock runs out, may this colour still be bought as a pre-order?
    allow_preorder = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def in_stock(self) -> bool:
        return self.stock_qty > 0

    @property
    def is_preorder(self) -> bool:
        """Buyable but out of stock → this purchase is a pre-order."""
        return self.stock_qty <= 0 and self.allow_preorder

    @property
    def is_purchasable(self) -> bool:
        return self.stock_qty > 0 or self.allow_preorder


class ProductImage(db.Model):
    """Multiple images per product (front, interior, side detail, lifestyle, etc.).
    `path` is relative to static/img/ — e.g. "products/classic/hero.jpg"."""
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    path = db.Column(db.String(255), nullable=False)
    alt = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


# ─── Cart ────────────────────────────────────────────────────────────────────


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    session_token = db.Column(db.String(64), unique=True, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = db.relationship("CartItem", backref="cart", lazy=True, cascade="all, delete-orphan")

    @property
    def subtotal_cents(self) -> int:
        return sum(it.line_cents for it in self.items)

    @property
    def total_qty(self) -> int:
        return sum(it.qty for it in self.items)


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variants.id"), nullable=False)
    qty = db.Column(db.Integer, default=1, nullable=False)
    unit_price_cents_snapshot = db.Column(db.Integer, nullable=False)

    variant = db.relationship("ProductVariant")

    @property
    def line_cents(self) -> int:
        return self.unit_price_cents_snapshot * self.qty


# ─── Orders ──────────────────────────────────────────────────────────────────


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(40), unique=True, index=True, nullable=False)

    # Either user_id or guest_email + guest_lookup_token
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    guest_email = db.Column(db.String(255), nullable=True, index=True)
    guest_lookup_token = db.Column(db.String(64), nullable=True, index=True)

    status = db.Column(db.String(20), default="pending", nullable=False)  # pending|paid|fulfilled|cancelled
    subtotal_cents = db.Column(db.Integer, nullable=False)
    shipping_cents = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), default="SGD", nullable=False)

    shipping_address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=True)
    shipping_address = db.relationship("Address")

    hitpay_payment_request_id = db.Column(db.String(80))
    hitpay_reference = db.Column(db.String(80))
    hitpay_status = db.Column(db.String(40))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def generate_number() -> str:
        # MC-YYYY-NNNNNN where NNNNNN is a random 6-digit hex segment
        return f"MC-{datetime.utcnow().year}-{secrets.token_hex(3).upper()}"

    @staticmethod
    def generate_guest_token() -> str:
        return secrets.token_urlsafe(24)

    @property
    def buyer_email(self) -> str:
        if self.user:
            return self.user.email
        return self.guest_email or ""

    @property
    def is_guest(self) -> bool:
        return self.user_id is None


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variants.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    unit_price_cents = db.Column(db.Integer, nullable=False)
    is_preorder = db.Column(db.Boolean, default=False, nullable=False)  # snapshot at order time
    name_snapshot = db.Column(db.String(160), nullable=False)
    design_snapshot = db.Column(db.String(40))

    variant = db.relationship("ProductVariant")

    @property
    def line_cents(self) -> int:
        return self.unit_price_cents * self.qty

    @property
    def image_path(self) -> str:
        """Path to display this line item's image. Looks up the current Product
        by design_snapshot (so renaming an image still works) and falls back to
        the legacy `products/<design>.jpg` if the product was deleted."""
        if self.design_snapshot:
            p = Product.query.filter_by(design_code=self.design_snapshot).first()
            if p:
                return p.primary_image_path
            return f"products/{self.design_snapshot}.jpg"
        return "products/placeholder.jpg"


# ─── Password reset ──────────────────────────────────────────────────────────


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User")


# ─── Activity / commerce-funnel analytics ────────────────────────────────────


class ActivityEvent(db.Model):
    """One row per meaningful customer action — the growth/insight backbone.

    Deliberately schema-light: `event_type` is an open string and `meta` is
    JSON, so new funnel steps can be tracked without a migration. Both a
    signed-in `user_id` and an anonymous `anon_id` (cart session token) are
    captured so the pre-signup funnel is visible and can be stitched to the
    account on sign-up. `product_id` lets us compare what shoppers *view*
    vs. *buy*; `order_id` ties revenue events back to the sale.

    Indexed on every column the admin analytics group/filter by so the
    aggregates stay fast as volume grows.
    """
    __tablename__ = "activity_events"

    # Canonical funnel event types (free-form, but use these for consistency).
    REGISTER = "register"
    LOGIN = "login"
    LOGOUT = "logout"
    PRODUCT_VIEW = "product_view"
    COLLECTION_VIEW = "collection_view"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT_STARTED = "checkout_started"
    ORDER_PLACED = "order_placed"
    ORDER_PAID = "order_paid"
    ORDER_CANCELLED = "order_cancelled"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    anon_id = db.Column(db.String(64), nullable=True, index=True)   # cart session token pre-signup
    event_type = db.Column(db.String(40), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True, index=True)
    value_cents = db.Column(db.Integer, nullable=True)              # revenue for paid events
    meta = db.Column(db.JSON, nullable=True)
    ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship("User", backref=db.backref(
        "activity", lazy="dynamic", cascade="all, delete-orphan"))
    product = db.relationship("Product")
    order = db.relationship("Order")
