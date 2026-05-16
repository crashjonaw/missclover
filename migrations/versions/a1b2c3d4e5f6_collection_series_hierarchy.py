"""collection / series hierarchy

Adds Collection + Series tables, Product.series_id FK, and migrates the four
existing products into the Signature→Clover and Cosy→Pillow hierarchy:

  tote_design_1/classic  -> Signature/Clover  design_code=classic  bag_type=tote
  tote_design_1/maroon   -> Signature/Clover  design_code=maroon   bag_type=tote
  tote_design_2/classic  -> Cosy/Pillow       design_code=sand     bag_type=shoulderbag
  tote_design_2/emerald  -> Cosy/Pillow       design_code=thyme    bag_type=shoulderbag

Slugs and SKUs are rewritten so a subsequent `python seed.py` upserts cleanly
onto the same rows (Product matched by slug, Variant by sku — stock preserved).
order_items.design_snapshot is rewritten too (0 rows today; future-proof).

Revision ID: a1b2c3d4e5f6
Revises: 8c7f52bc6d06
Create Date: 2026-05-16

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '8c7f52bc6d06'
branch_labels = None
depends_on = None


# old slash-prefixed design_code -> (series_slug, design_code, bag_type, slug,
#                                    name, old_sku, new_sku)
_MAP = {
    "tote_design_1/classic": ("clover",  "classic", "tote",        "classic-clover-tote", "Classic Clover Tote", "MC-CLS-CR", "MC-CLV-CL"),
    "tote_design_1/maroon":  ("clover",  "maroon",  "tote",        "maroon-clover-tote",  "Maroon Clover Tote",  "MC-MRN-BG", "MC-CLV-MR"),
    "tote_design_2/classic": ("pillow",  "sand",    "shoulderbag", "sand-pillow",         "Sand Pillow",         "MC-T2-CLS", "MC-PLW-SD"),
    "tote_design_2/emerald": ("pillow",  "thyme",   "shoulderbag", "thyme-pillow",        "Thyme Pillow",        "MC-T2-EMR", "MC-PLW-TH"),
}

# reverse mapping for downgrade: bare design_code -> old slash design_code + old sku
_REV = {v[1]: (old, v[6], v[5]) for old, v in _MAP.items()}


def upgrade():
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color_hex", sa.String(length=7), nullable=True),
        sa.Column("tile_eyebrow", sa.String(length=120), nullable=True),
        sa.Column("tile_headline", sa.String(length=255), nullable=True),
        sa.Column("tile_body", sa.Text(), nullable=True),
        sa.Column("hero_image_path", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("collections", schema=None) as b:
        b.create_index(b.f("ix_collections_slug"), ["slug"], unique=True)

    op.create_table(
        "series",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color_hex", sa.String(length=7), nullable=True),
        sa.Column("tile_eyebrow", sa.String(length=120), nullable=True),
        sa.Column("tile_headline", sa.String(length=255), nullable=True),
        sa.Column("tile_body", sa.Text(), nullable=True),
        sa.Column("hero_image_path", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("collection_id", "slug", name="uq_series_collection_slug"),
    )
    with op.batch_alter_table("series", schema=None) as b:
        b.create_index(b.f("ix_series_collection_id"), ["collection_id"], unique=False)
        b.create_index(b.f("ix_series_slug"), ["slug"], unique=False)

    with op.batch_alter_table("products", schema=None) as b:
        b.add_column(sa.Column("series_id", sa.Integer(), nullable=True))
        b.create_index(b.f("ix_products_series_id"), ["series_id"], unique=False)
        b.create_foreign_key("fk_products_series_id", "series", ["series_id"], ["id"])

    # ── Data migration ────────────────────────────────────────────────────────
    conn = op.get_bind()
    now = datetime.utcnow()

    conn.execute(sa.text(
        "INSERT INTO collections (slug, name, description, color_hex, tile_eyebrow,"
        " tile_body, is_active, is_featured, display_order, created_at) VALUES"
        " ('signature','Signature','The structured leather edit.','#F0E6D2',"
        "  'Signature','Structured leather, gold hardware, made for the everyday.',1,1,10,:n),"
        " ('cosy','Cosy','Soft, padded, made to slouch into.','#D8C3A5',"
        "  'Cosy','Padded, quilted, quietly comfortable.',1,1,20,:n)"
    ), {"n": now})

    sig = conn.execute(sa.text("SELECT id FROM collections WHERE slug='signature'")).scalar()
    cosy = conn.execute(sa.text("SELECT id FROM collections WHERE slug='cosy'")).scalar()

    conn.execute(sa.text(
        "INSERT INTO series (collection_id, slug, name, color_hex, tile_eyebrow,"
        " is_active, is_featured, display_order, created_at) VALUES"
        " (:sig,'clover','Clover','#F0E6D2','The Clover',1,1,10,:n),"
        " (:cosy,'pillow','Pillow','#D8C3A5','The Pillow',1,1,10,:n)"
    ), {"sig": sig, "cosy": cosy, "n": now})

    series_ids = {
        "clover": conn.execute(sa.text(
            "SELECT id FROM series WHERE collection_id=:c AND slug='clover'"),
            {"c": sig}).scalar(),
        "pillow": conn.execute(sa.text(
            "SELECT id FROM series WHERE collection_id=:c AND slug='pillow'"),
            {"c": cosy}).scalar(),
    }

    for old_code, (s_slug, code, bag, slug, name, old_sku, new_sku) in _MAP.items():
        conn.execute(sa.text(
            "UPDATE products SET series_id=:sid, design_code=:code, bag_type=:bag,"
            " slug=:slug, name=:name WHERE design_code=:old"
        ), {"sid": series_ids[s_slug], "code": code, "bag": bag,
            "slug": slug, "name": name, "old": old_code})
        conn.execute(sa.text(
            "UPDATE product_variants SET sku=:new WHERE sku=:old"
        ), {"new": new_sku, "old": old_sku})
        conn.execute(sa.text(
            "UPDATE order_items SET design_snapshot=:code WHERE design_snapshot=:old"
        ), {"code": code, "old": old_code})


def downgrade():
    conn = op.get_bind()
    for code, (old_code, new_sku, old_sku) in _REV.items():
        conn.execute(sa.text(
            "UPDATE products SET design_code=:old WHERE design_code=:code"
        ), {"old": old_code, "code": code})
        conn.execute(sa.text(
            "UPDATE product_variants SET sku=:old WHERE sku=:new"
        ), {"old": old_sku, "new": new_sku})
        conn.execute(sa.text(
            "UPDATE order_items SET design_snapshot=:old WHERE design_snapshot=:code"
        ), {"old": old_code, "code": code})

    with op.batch_alter_table("products", schema=None) as b:
        b.drop_constraint("fk_products_series_id", type_="foreignkey")
        b.drop_index(b.f("ix_products_series_id"))
        b.drop_column("series_id")

    with op.batch_alter_table("series", schema=None) as b:
        b.drop_index(b.f("ix_series_slug"))
        b.drop_index(b.f("ix_series_collection_id"))
    op.drop_table("series")

    with op.batch_alter_table("collections", schema=None) as b:
        b.drop_index(b.f("ix_collections_slug"))
    op.drop_table("collections")
