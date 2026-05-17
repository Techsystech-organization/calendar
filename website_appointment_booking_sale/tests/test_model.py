# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.resource_booking.tests.common import create_test_data


@tagged("post_install", "-at_install")
class TestResourceBookingTypeSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)

    def test_upfront_payment_fields_can_be_configured(self):
        """Published booking types can require checkout with product pricing."""
        product = self.env["product.product"].create(
            {
                "name": "Booking Deposit",
                "type": "service",
                "sale_ok": True,
                "list_price": 50.0,
            }
        )
        self.rbt.write(
            {
                "website_published": True,
                "require_upfront_payment": True,
                "payment_product_id": product.id,
                "payment_price": 25.0,
                "payment_hold_expiry_hours": 0.5,
            }
        )
        self.assertTrue(self.rbt.require_upfront_payment)
        self.assertEqual(self.rbt.payment_product_id, product)
        self.assertEqual(self.rbt.payment_price, 25.0)
        self.assertEqual(self.rbt.website_payment_price, 25.0)
        self.rbt.payment_price = 0.0
        self.assertEqual(self.rbt.website_payment_price, 50.0)
        self.assertEqual(self.rbt.payment_hold_expiry_hours, 0.5)

    def _create_scheduled_payment_booking(self):
        product = self.env["product.product"].create(
            {
                "name": "Booking Deposit",
                "type": "service",
                "sale_ok": True,
                "list_price": 50.0,
            }
        )
        self.rbt.write(
            {
                "website_published": True,
                "require_upfront_payment": True,
                "payment_product_id": product.id,
                "payment_price": 25.0,
            }
        )
        booking = self.env["resource.booking"].create(
            {
                "type_id": self.rbt.id,
                "partner_ids": [(4, self.partner.id)],
                "combination_auto_assign": False,
                "combination_id": self.rbcs[0].id,
            }
        )
        booking.start = fields.Datetime.to_datetime("2021-03-01 10:00:00")
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": 1.0,
                "product_uom": product.uom_id.id,
                "price_unit": 25.0,
            }
        )
        booking.write(
            {
                "website_payment_required": True,
                "website_payment_sale_order_id": order.id,
                "website_payment_expires_at": fields.Datetime.now() + timedelta(hours=1),
            }
        )
        return booking, order

    def test_sale_confirmation_confirms_paid_booking(self):
        """A checkout-confirmed sale order confirms the linked booking attendance."""
        booking, order = self._create_scheduled_payment_booking()
        self.assertEqual(booking.state, "scheduled")
        order.action_confirm()
        self.assertEqual(booking.state, "confirmed")
        self.assertFalse(booking.website_payment_required)

    def test_expired_checkout_cleanup_releases_slot(self):
        """Abandoned checkout cancels the booking hold so the slot is released."""
        booking, order = self._create_scheduled_payment_booking()
        booking.website_payment_expires_at = fields.Datetime.now() - timedelta(minutes=1)
        self.env["resource.booking"]._cron_cleanup_expired_website_payment_bookings()
        self.assertEqual(booking.state, "canceled")
        self.assertEqual(order.state, "cancel")
