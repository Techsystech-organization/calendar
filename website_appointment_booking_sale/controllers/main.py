# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.website_appointment_booking.controllers.main import (
    WebsiteAppointmentBooking,
)


class WebsiteAppointmentBookingSale(WebsiteAppointmentBooking):
    def _create_payment_sale_order(self, booking, partner, booking_type):
        product = booking_type.payment_product_id
        if not product:
            raise ValidationError(
                "This booking type requires a payment product before checkout can be used."
            )
        website = request.website
        order = website.sale_get_order(force_create=True)
        order = order.sudo()
        order.write(
            {
                "partner_id": partner.id,
                "partner_invoice_id": partner.id,
                "partner_shipping_id": partner.id,
                "website_id": website.id,
                "order_line": [Command.clear()],
            }
        )
        price_unit = booking_type.website_payment_price
        request.env["sale.order.line"].sudo().create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": 1.0,
                "product_uom": product.uom_id.id,
                "price_unit": price_unit,
                "name": (
                    product.get_product_multiline_description_sale()
                    or product.display_name
                ),
            }
        )
        expiry_hours = booking_type.payment_hold_expiry_hours or 1.0
        booking.write(
            {
                "website_payment_required": True,
                "website_payment_sale_order_id": order.id,
                "website_payment_expires_at": fields.Datetime.to_string(
                    fields.Datetime.now() + timedelta(hours=expiry_hours)
                ),
            }
        )
        request.session["sale_order_id"] = order.id
        request.session["last_booking"] = self._prepare_last_booking_session(
            booking_type, booking.start
        )
        return order

    def _finalize_booking(self, booking, booking_type, partner, selected_tz, selected_combination):
        """Override to add paid checkout flow before confirming."""
        if booking_type.require_upfront_payment:
            try:
                self._create_payment_sale_order(booking, partner, booking_type)
            except ValidationError as error:
                booking.action_cancel()
                query = self._build_selection_query(
                    selected_tz, selected_combination, error=str(error)
                )
                return request.redirect(f"/book/{booking_type.website_slug}{query}")
            return request.redirect("/shop/checkout")
        return super()._finalize_booking(
            booking, booking_type, partner, selected_tz, selected_combination
        )
