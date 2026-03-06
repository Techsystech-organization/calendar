# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from datetime import datetime, timezone

from dateutil.parser import isoparse
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


class WebsiteAppointmentBooking(http.Controller):
    def _get_booking_type(self, slug):
        """Look up a published booking type by its slug."""
        return (
            request.env["resource.booking.type"]
            .sudo()
            .search(
                [("website_slug", "=", slug), ("website_published", "=", True)],
                limit=1,
            )
        )

    def _create_phantom_booking(self, booking_type):
        """Create an in-memory booking for slot computation.

        Uses ``new()`` to avoid writing to the database. The phantom booking
        is configured with auto-assignment so that ``_get_available_slots``
        considers all resource combinations.
        """
        Booking = request.env["resource.booking"].sudo()
        tz = booking_type.resource_calendar_id.tz or "UTC"
        return Booking.with_context(tz=tz).new(
            {
                "type_id": booking_type.id,
                "duration": booking_type.duration,
                "combination_auto_assign": True,
            }
        )

    def _serialize_slots(self, slots, time_format):
        """Serialize slot data to a JSON-safe list of dicts.

        Each dict contains ``date``, ``time`` (display string) and ``iso``
        (full ISO 8601 value used for form submission).
        """
        result = []
        for day, times in sorted(slots.items()):
            for slot_dt in times:
                result.append(
                    {
                        "date": day.isoformat(),
                        "time": slot_dt.strftime(time_format),
                        "iso": slot_dt.isoformat(),
                    }
                )
        return result

    @http.route(
        [
            "/book/<slug>",
            "/book/<slug>/<int:year>/<int:month>",
        ],
        auth="public",
        type="http",
        website=True,
        sitemap=True,
    )
    def booking_page(self, slug, year=None, month=None, error=None, **kwargs):
        """Render the public booking page for a given booking type."""
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        phantom = self._create_phantom_booking(booking_type)
        calendar_ctx = phantom._get_calendar_context(year, month)
        lang = calendar_ctx["res_lang"]
        time_format = lang.time_format.replace(":%S", "")
        slot_data = self._serialize_slots(calendar_ctx["slots"], time_format)
        values = {
            "booking_type": booking_type,
            "slot_data": slot_data,
            "slot_data_json": json.dumps(slot_data),
            "error": error,
        }
        values.update(calendar_ctx)
        return request.render("website_appointment_booking.booking_page", values)

    @http.route(
        "/book/<slug>/confirm",
        auth="public",
        type="http",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def booking_confirm(self, slug, **kwargs):
        """Process a booking confirmation.

        Expects POST parameters ``name``, ``email`` and ``when`` (ISO 8601).
        Creates or finds the partner, creates the booking, assigns the slot
        and confirms.
        """
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        name = (kwargs.get("name") or "").strip()
        email = (kwargs.get("email") or "").strip()
        when_str = kwargs.get("when", "")
        if not name or not email or not when_str:
            return request.redirect(f"/book/{slug}?error=Please+fill+in+all+fields.")
        # Parse the submitted datetime
        try:
            when_tz_aware = isoparse(when_str)
        except (ValueError, TypeError):
            return request.redirect(f"/book/{slug}?error=Invalid+date+selected.")
        when_naive = datetime.fromtimestamp(
            when_tz_aware.timestamp(), tz=timezone.utc
        ).replace(tzinfo=None)
        # Find or create partner
        Partner = request.env["res.partner"].sudo()
        partner = Partner.search([("email", "=ilike", email)], limit=1)
        if not partner:
            partner = Partner.create({"name": name, "email": email})
        elif not partner.name or partner.name == email:
            partner.name = name
        # Create and schedule the booking inside a savepoint so that
        # a ValidationError (race condition: slot already taken) can be
        # caught without poisoning the database cursor.
        Booking = request.env["resource.booking"].sudo()
        tz = booking_type.resource_calendar_id.tz or "UTC"
        try:
            with request.env.cr.savepoint():
                booking = Booking.with_context(
                    tz=tz,
                    using_portal=True,
                    mail_create_nosubscribe=True,
                ).create(
                    {
                        "type_id": booking_type.id,
                        "partner_ids": [(4, partner.id)],
                        "combination_auto_assign": True,
                    }
                )
                booking.start = when_naive
                booking.action_confirm()
        except ValidationError:
            # Race condition: slot was taken between page load and submit
            month_str = f"{when_tz_aware:%Y/%m}"
            return request.redirect(
                f"/book/{slug}/{month_str}"
                "?error=That+slot+is+no+longer+available.+Please+choose+another."
            )
        # Store booking info in session for the success page
        request.session["last_booking"] = {
            "name": booking_type.name,
            "start": when_tz_aware.strftime("%B %d, %Y"),
            "time": when_tz_aware.strftime("%H:%M"),
            "duration": booking_type.duration,
            "location": booking_type.location or "",
        }
        return request.redirect(f"/book/{slug}/success")

    @http.route(
        "/book/<slug>/success",
        auth="public",
        type="http",
        website=True,
    )
    def booking_success(self, slug, **kwargs):
        """Thank-you page after a successful booking."""
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        last_booking = request.session.pop("last_booking", {})
        values = {
            "booking_type": booking_type,
            "last_booking": last_booking,
        }
        return request.render("website_appointment_booking.booking_success", values)
