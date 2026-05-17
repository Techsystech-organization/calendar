# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Website Appointment Booking Sale",
    "summary": "Paid booking checkout flow for website appointment booking",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Ledo Enterprises LLC, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "website_appointment_booking",
        "sale",
        "website_sale",
    ],
    "data": [
        "data/booking_payment_cron.xml",
        "templates/booking_sale.xml",
        "views/resource_booking_type_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            # Sale-specific frontend assets go here
        ],
    },
}
