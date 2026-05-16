# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time
from lxml.html import fromstring

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.resource_booking.tests.common import create_test_data


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestPaidWebsiteAppointmentBooking(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.payment_product = cls.env["product.product"].create(
            {
                "name": "Booking Deposit Product",
                "type": "service",
                "sale_ok": True,
                "list_price": 60.0,
            }
        )
        cls.rbt.write(
            {
                "website_published": True,
                "website_slug": "paid-booking",
                "location": "Main office",
                "require_upfront_payment": True,
                "payment_product_id": cls.payment_product.id,
                "payment_price": 25.0,
            }
        )

    def _url_xml(self, url, data=None, timeout=10):
        response = self.url_open(url, data, timeout=timeout)
        return fromstring(response.content)

    def _get_csrf_token(self, page):
        inputs = page.cssselect('input[name="csrf_token"]')
        if inputs:
            return inputs[0].get("value")
        return ""

    def test_paid_booking_price_is_visible_on_card_and_booking_page(self):
        landing_page = self._url_xml("/book")
        cards = [
            card
            for card in landing_page.cssselect(".o_wab_booking_card")
            if card.cssselect('a[href="/book/paid-booking"]')
        ]
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertTrue(card.cssselect(".o_wab_payment_price:contains('Upfront payment')"))
        self.assertTrue(card.cssselect(".o_wab_payment_price:contains('25')"))

        booking_page = self._url_xml("/book/paid-booking/2021/3")
        self.assertTrue(
            booking_page.cssselect(".o_wab_meta_pill.o_wab_payment_price:contains('25')")
        )
        self.assertTrue(
            booking_page.cssselect(":contains('This booking requires an upfront payment')")
        )
        self.assertTrue(booking_page.cssselect(".o_wab_submit_btn:contains('Checkout')"))

    def test_paid_booking_uses_booking_type_price_for_checkout_order(self):
        page = self._url_xml("/book/paid-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Paid Visitor",
            "email": "paid-visitor@example.com",
            "phone": "+1 555-0123",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/paid-booking/confirm", data=data, timeout=30)
        self.assertIn("/shop/", response.url)
        booking = self.env["resource.booking"].search(
            [
                ("type_id", "=", self.rbt.id),
                ("partner_ids.email", "=", "paid-visitor@example.com"),
            ],
            limit=1,
        )
        self.assertTrue(booking)
        self.assertEqual(booking.state, "scheduled")
        self.assertTrue(booking.website_payment_required)
        self.assertEqual(booking.website_payment_sale_order_id.order_line.price_unit, 25.0)

    def test_paid_booking_confirmation_template_is_installed(self):
        view = self.env.ref(
            "website_appointment_booking_sale.paid_booking_shop_confirmation"
        )
        self.assertIn("Booking Scheduled", view.arch_db)
        self.assertIn("your booking has been scheduled", view.arch_db)
        self.assertIn('text-bg-success', view.arch_db)
        self.assertIn("Booked", view.arch_db)
        self.assertIn("o_wab_paid_booking_card", view.arch_db)
        self.assertIn("View details", view.arch_db)
        self.assertIn("website_sale.payment_confirmation_status", view.arch_db)
        self.assertNotIn("//h3[contains(., 'Thank you for your order.')]", view.arch_db)
