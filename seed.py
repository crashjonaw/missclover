"""Seed Classic + Maroon products. Idempotent — running twice updates instead of duplicating."""
from app import app
from extensions import db
from models import Product, ProductVariant


PRODUCTS = [
    dict(
        slug="classic-tote",
        name="The Classic Tote",
        design_code="classic",
        base_price_cents=35000,
        description=(
            "The starter MISS CLOVER. Cream leather, gold hardware, structured 8″×11″ silhouette "
            "with a tan-suede interior — lipstick holder, key fob, inner zip pocket."
        ),
        variants=[dict(name="Classic", sku="MC-CLS-CR", stock_qty=20, price_cents=35000)],
    ),
    dict(
        slug="maroon-tote",
        name="The Maroon Tote",
        design_code="maroon",
        base_price_cents=35000,
        description=(
            "Same silhouette in deep burgundy. Hand-dyed maroon leather, gold hardware, "
            "suede-lined interior with all the clever pockets."
        ),
        variants=[dict(name="Maroon", sku="MC-MRN-BG", stock_qty=20, price_cents=35000)],
    ),
]


def seed():
    with app.app_context():
        for spec in PRODUCTS:
            p = Product.query.filter_by(slug=spec["slug"]).first()
            if not p:
                p = Product(
                    slug=spec["slug"],
                    name=spec["name"],
                    description=spec["description"],
                    design_code=spec["design_code"],
                    base_price_cents=spec["base_price_cents"],
                )
                db.session.add(p)
                db.session.flush()
                print(f"  + Product: {p.slug}")
            else:
                p.name = spec["name"]
                p.description = spec["description"]
                p.design_code = spec["design_code"]
                p.base_price_cents = spec["base_price_cents"]
                print(f"  ~ Product: {p.slug}")

            for v_spec in spec["variants"]:
                v = ProductVariant.query.filter_by(sku=v_spec["sku"]).first()
                if not v:
                    v = ProductVariant(
                        product_id=p.id,
                        name=v_spec["name"],
                        sku=v_spec["sku"],
                        stock_qty=v_spec["stock_qty"],
                        price_cents=v_spec["price_cents"],
                    )
                    db.session.add(v)
                    print(f"    + Variant: {v.sku}")
                else:
                    v.name = v_spec["name"]
                    # keep stock as-is on re-seed
                    v.price_cents = v_spec["price_cents"]
                    print(f"    ~ Variant: {v.sku} (stock unchanged: {v.stock_qty})")

        db.session.commit()
        total = Product.query.count()
        print(f"\nSeed complete. Products in DB: {total}")


if __name__ == "__main__":
    seed()
