"""Admin analytics — pure SQL aggregation (no Python row loops).

Every figure is a single GROUP BY / SUM / COUNT pushed to the database and
keyed off indexed columns, so the dashboard stays fast as orders and activity
grow. All revenue is in SGD cents; the templates format with the `sgd` filter.
"""
from datetime import datetime, timedelta

from sqlalchemy import case, distinct, func

from extensions import db
from models import ActivityEvent, Order, OrderItem, Product, User

PAID_STATES = ("paid", "fulfilled")


def _cutoff(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


def overview(window_days: int = 30) -> dict:
    """Headline KPIs for the dashboard."""
    is_paid = Order.status.in_(PAID_STATES)
    since = _cutoff(window_days)

    customers = db.session.query(func.count(User.id)).filter(
        User.is_admin.is_(False)).scalar() or 0
    new_customers = db.session.query(func.count(User.id)).filter(
        User.is_admin.is_(False), User.created_at >= since).scalar() or 0
    total_orders = db.session.query(func.count(Order.id)).scalar() or 0
    paid_orders = db.session.query(func.count(Order.id)).filter(is_paid).scalar() or 0
    revenue = db.session.query(
        func.coalesce(func.sum(Order.total_cents), 0)).filter(is_paid).scalar() or 0
    paying = db.session.query(func.count(distinct(Order.user_id))).filter(
        is_paid, Order.user_id.isnot(None)).scalar() or 0

    repeat_sub = (db.session.query(Order.user_id)
                  .filter(is_paid, Order.user_id.isnot(None))
                  .group_by(Order.user_id)
                  .having(func.count(Order.id) >= 2)
                  .subquery())
    repeat_customers = db.session.query(func.count()).select_from(repeat_sub).scalar() or 0

    return {
        "customers": customers,
        "new_customers": new_customers,
        "window_days": window_days,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "revenue_cents": revenue,
        "aov_cents": (revenue // paid_orders) if paid_orders else 0,
        "paying_customers": paying,
        "repeat_customers": repeat_customers,
        "conversion_pct": round(100 * paying / customers, 1) if customers else 0.0,
    }


def funnel(window_days: int = 30) -> list[dict]:
    """Counts per funnel step in the window (drives the conversion bars)."""
    since = _cutoff(window_days)
    steps = [
        ("Product views",   ActivityEvent.PRODUCT_VIEW),
        ("Add to cart",     ActivityEvent.ADD_TO_CART),
        ("Checkout started", ActivityEvent.CHECKOUT_STARTED),
        ("Order placed",    ActivityEvent.ORDER_PLACED),
        ("Order paid",      ActivityEvent.ORDER_PAID),
    ]
    rows = dict(
        db.session.query(ActivityEvent.event_type, func.count(ActivityEvent.id))
        .filter(ActivityEvent.created_at >= since)
        .group_by(ActivityEvent.event_type).all())
    top = rows.get(ActivityEvent.PRODUCT_VIEW, 0) or 0
    return [{
        "label": label,
        "count": rows.get(et, 0) or 0,
        "pct": round(100 * (rows.get(et, 0) or 0) / top, 1) if top else 0.0,
    } for label, et in steps]


def top_products(limit: int = 10) -> list[dict]:
    """Per product: views, adds, units sold, revenue — view→buy comparison."""
    views = dict(
        db.session.query(ActivityEvent.product_id, func.count(ActivityEvent.id))
        .filter(ActivityEvent.event_type == ActivityEvent.PRODUCT_VIEW,
                ActivityEvent.product_id.isnot(None))
        .group_by(ActivityEvent.product_id).all())
    adds = dict(
        db.session.query(ActivityEvent.product_id, func.count(ActivityEvent.id))
        .filter(ActivityEvent.event_type == ActivityEvent.ADD_TO_CART,
                ActivityEvent.product_id.isnot(None))
        .group_by(ActivityEvent.product_id).all())
    sold = (db.session.query(
                Product.id, Product.name,
                func.coalesce(func.sum(OrderItem.qty), 0),
                func.coalesce(func.sum(OrderItem.qty * OrderItem.unit_price_cents), 0))
            .outerjoin(OrderItem, OrderItem.design_snapshot == Product.design_code)
            .outerjoin(Order, (Order.id == OrderItem.order_id)
                       & Order.status.in_(PAID_STATES))
            .group_by(Product.id).all())
    out = []
    for pid, name, units, rev in sold:
        out.append({
            "name": name,
            "views": views.get(pid, 0),
            "adds": adds.get(pid, 0),
            "units": int(units or 0),
            "revenue_cents": int(rev or 0),
        })
    out.sort(key=lambda r: (r["revenue_cents"], r["units"], r["views"]), reverse=True)
    return out[:limit]


def customers(limit: int = 200, sort: str = "spend") -> list[dict]:
    """Every customer with order count + lifetime spend + last order, in one
    aggregated query (no per-user follow-ups)."""
    spend = func.coalesce(func.sum(
        case((Order.status.in_(PAID_STATES), Order.total_cents), else_=0)), 0)
    paid_orders = func.coalesce(func.sum(
        case((Order.status.in_(PAID_STATES), 1), else_=0)), 0)
    rows = (db.session.query(
                User,
                func.count(Order.id).label("orders"),
                paid_orders.label("paid_orders"),
                spend.label("spend"),
                func.max(Order.created_at).label("last_order"))
            .outerjoin(Order, Order.user_id == User.id)
            .filter(User.is_admin.is_(False))
            .group_by(User.id)
            .order_by({
                "spend": spend.desc(),
                "recent": User.created_at.desc(),
                "orders": func.count(Order.id).desc(),
            }.get(sort, spend.desc()))
            .limit(limit).all())
    return [{
        "user": u,
        "orders": o,
        "paid_orders": int(po or 0),
        "spend_cents": int(sp or 0),
        "last_order": lo,
    } for u, o, po, sp, lo in rows]


def customer_detail(user_id: int) -> dict | None:
    u = db.session.get(User, user_id)
    if u is None:
        return None
    orders = (Order.query.filter_by(user_id=u.id)
              .order_by(Order.created_at.desc()).all())
    spent = sum(o.total_cents for o in orders if o.status in PAID_STATES)
    activity = (u.activity.order_by(ActivityEvent.created_at.desc()).limit(50).all())
    return {
        "user": u,
        "orders": orders,
        "orders_count": len(orders),
        "spend_cents": spent,
        "activity": activity,
    }


def recent_orders(limit: int = 12):
    return Order.query.order_by(Order.created_at.desc()).limit(limit).all()


def recent_signups(limit: int = 12):
    return (User.query.filter(User.is_admin.is_(False))
            .order_by(User.created_at.desc()).limit(limit).all())


def recent_activity(limit: int = 25):
    return (ActivityEvent.query
            .order_by(ActivityEvent.created_at.desc()).limit(limit).all())
