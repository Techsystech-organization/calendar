# Copyright 2026 Techsystech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    website_payment_required = fields.Boolean(
        string="Website Payment Required",
        copy=False,
        help="Technical flag set for public bookings waiting on website checkout.",
    )
    website_payment_expires_at = fields.Datetime(
        string="Website Payment Hold Expires At",
        copy=False,
    )
