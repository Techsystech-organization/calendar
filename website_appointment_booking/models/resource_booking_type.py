# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models


def _slugify(value):
    """Convert a string to a URL-friendly slug."""
    value = (value or "").lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value)
    return value.strip("-")


class ResourceBookingType(models.Model):
    _inherit = "resource.booking.type"

    website_published = fields.Boolean(
        copy=False,
        help="When checked, this booking type will be available on a public "
        "booking page accessible without login.",
    )
    website_slug = fields.Char(
        compute="_compute_website_slug",
        store=True,
        readonly=False,
        copy=False,
        help="URL-friendly identifier used in the public booking page URL. "
        "Auto-generated from the name, but can be customized.",
    )
    website_description = fields.Html(
        translate=True,
        sanitize_attributes=False,
        help="Introductory text displayed on the public booking page.",
    )
    website_card_image = fields.Image(
        string="Booking Card Photo",
        max_width=1024,
        max_height=1024,
        help="Photo displayed for this booking type on the public /book landing page.",
    )
    website_card_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="resource_booking_type_website_card_user_rel",
        column1="type_id",
        column2="user_id",
        string="Card Avatar Users",
        help="Users whose avatars are displayed on the public /book card.",
    )
    website_card_resource_ids = fields.Many2many(
        comodel_name="resource.resource",
        relation="resource_booking_type_website_card_resource_rel",
        column1="type_id",
        column2="resource_id",
        string="Card Avatar Resources",
        help="Resources whose avatars are displayed on the public /book card.",
    )
    website_url = fields.Char(
        string="Website URL",
        compute="_compute_website_url",
        help="Public booking page URL for this booking type.",
    )

    _sql_constraints = [
        (
            "website_slug_unique",
            "UNIQUE(website_slug)",
            "The website slug must be unique.",
        ),
    ]

    @api.depends("name")
    def _compute_website_slug(self):
        for record in self:
            if not record.website_slug and record.name:
                record.website_slug = _slugify(record.name)

    @api.depends("website_slug")
    def _compute_website_url(self):
        for record in self:
            record.website_url = f"/book/{record.website_slug}" if record.website_slug else "/book"

    def open_website_url(self):
        self.ensure_one()
        return self.env["website"].get_client_action(self.website_url)
