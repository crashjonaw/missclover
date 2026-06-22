"""Mobile (390px) end-to-end layout checks for the add-to-cart → checkout flow.

Guards against the responsive regressions we hit on phones — chiefly the cart
table, which used to overflow/overlap because it never reflowed. Each test
asserts the page has no horizontal overflow and captures a screenshot.

Opt-in:  RUN_PLAYWRIGHT=1 pytest unit_test/playwright
"""
import pytest

pytestmark = pytest.mark.playwright


def _horizontal_overflow(page) -> int:
    """Pixels the document scrolls horizontally. >1 means something is wider
    than the viewport — the hallmark of mobile misalignment/overlap."""
    return page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )


def _add_to_cart(server, page, variant_id, qty=1):
    page.request.post(f"{server['url']}/cart/add",
                      form={"variant_id": variant_id, "qty": qty})


def _go(page, server, path, wait="networkidle"):
    page.goto(f"{server['url']}{path}", wait_until=wait)


def test_cart_mobile_no_overflow(live_server, page, shot_dir):
    v = live_server["variants"]
    _go(page, live_server, "/")  # establish session
    _add_to_cart(live_server, page, v["sand"], qty=2)
    _add_to_cart(live_server, page, v["thyme"], qty=1)

    _go(page, live_server, "/cart/")
    page.screenshot(path=str(shot_dir / "cart.png"), full_page=True)

    assert page.locator(".cart-table tbody tr").count() == 2
    # The fix: the table reflows into cards, so no sideways scroll.
    assert _horizontal_overflow(page) <= 1
    # Update + Remove controls are present and laid out, not clipped away.
    assert page.locator(".cart-table button:has-text('Update')").count() == 2


def test_checkout_start_mobile_no_overflow(live_server, page, shot_dir):
    v = live_server["variants"]
    _go(page, live_server, "/")
    _add_to_cart(live_server, page, v["sand"])

    _go(page, live_server, "/checkout/start")
    page.screenshot(path=str(shot_dir / "checkout_start.png"), full_page=True)

    assert _horizontal_overflow(page) <= 1
    # The three options stack but all render.
    assert page.locator(".checkout-start-card").count() == 3


def test_shipping_mobile_no_overflow(live_server, page, shot_dir):
    v = live_server["variants"]
    _go(page, live_server, "/")
    _add_to_cart(live_server, page, v["sand"])
    page.request.post(f"{live_server['url']}/checkout/start",
                      form={"action": "guest", "email": "test@example.com"})

    _go(page, live_server, "/checkout/shipping")
    page.screenshot(path=str(shot_dir / "shipping.png"), full_page=True)

    assert _horizontal_overflow(page) <= 1
    assert page.locator("input[name='recipient_name']").is_visible()
    assert page.locator("input[name='postcode']").is_visible()


def test_payment_mobile_no_overflow(live_server, page, shot_dir):
    v = live_server["variants"]
    _go(page, live_server, "/")
    _add_to_cart(live_server, page, v["sand"])
    page.request.post(f"{live_server['url']}/checkout/start",
                      form={"action": "guest", "email": "test@example.com"})
    page.request.post(f"{live_server['url']}/checkout/shipping", form={
        "recipient_name": "Test Buyer", "line1": "12 Test Street", "line2": "#04-05",
        "postcode": "123456", "phone": "91234567"})

    # Stripe.js holds a connection open, so don't wait for networkidle.
    _go(page, live_server, "/checkout/payment", wait="domcontentloaded")
    page.wait_for_timeout(1500)
    page.screenshot(path=str(shot_dir / "payment.png"), full_page=True)

    assert _horizontal_overflow(page) <= 1
    # Server-rendered chrome is present (independent of the Stripe iframe).
    assert page.locator("text=Review & pay").is_visible()
    assert page.locator("#payment-form").count() == 1
    assert page.locator(".order-summary").is_visible()
