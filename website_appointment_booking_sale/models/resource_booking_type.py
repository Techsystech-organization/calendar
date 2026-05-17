# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResourceBookingType(models.Model):
    _inherit = "resource.booking.type"

    require_upfront_payment = fields.Boolean(
        string="Require Upfront Payment",
        help="When enabled for a published booking type, public visitors must "
        "complete website checkout before their attendance is confirmed.",
    )
    payment_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Payment Product",
        domain="[('sale_ok', '=', True)]",
        help="Product used to charge the upfront booking payment during checkout.",
    )
    payment_price = fields.Monetary(
        string="Payment Price",
        currency_field="currency_id",
        help="Price charged for the upfront booking payment. If empty, the "
        "product sales price is used.",
    )
    website_payment_price = fields.Monetary(
        string="Website Payment Price",
        compute="_compute_website_payment_price",
        currency_field="currency_id",
        help="Effective upfront payment shown on the website and charged at checkout.",
    )
    payment_hold_expiry_hours = fields.Float(
        string="Checkout Hold Expiry",
        default=1.0,
        help="Hours to hold a scheduled, unpaid booking before cleanup releases "
        "the slot.",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    @api.depends("payment_price", "payment_product_id.lst_price")
    def _compute_website_payment_price(self):
        for record in self:
            record.website_payment_price = (
                record.payment_price or record.payment_product_id.lst_price
            )
