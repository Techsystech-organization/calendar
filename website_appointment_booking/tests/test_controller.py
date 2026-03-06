# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from freezegun import freeze_time
from lxml.html import fromstring

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.resource_booking.tests.common import create_test_data


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestWebsiteAppointmentBooking(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write(
            {
                "website_published": True,
                "website_slug": "test-booking",
            }
        )

    def _url_xml(self, url, data=None, timeout=10):
        """Open a URL and return its parsed lxml tree."""
        response = self.url_open(url, data, timeout=timeout)
        return fromstring(response.content)

    def _get_csrf_token(self, page):
        """Extract CSRF token from a page's hidden input."""
        inputs = page.cssselect('input[name="csrf_token"]')
        if inputs:
            return inputs[0].get("value")
        return ""

    def test_unpublished_returns_404(self):
        """Unpublished booking types are not accessible.

        Uses a slug that has never been published, since changes made in test
        methods are not visible to the HTTP server thread in HttpCase.
        """
        response = self.url_open("/book/unpublished-type")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_slug_returns_404(self):
        """Unknown slugs return 404."""
        response = self.url_open("/book/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_booking_page_renders(self):
        """Published booking page renders with calendar."""
        page = self._url_xml("/book/test-booking")
        # The page should show the booking type name
        self.assertTrue(
            page.cssselect(".o_wab_title:contains('Test resource booking type')")
        )
        # Duration pill should be present
        self.assertTrue(page.cssselect(".o_wab_meta_pill:contains('30 min')"))

    def test_booking_page_february_no_slots(self):
        """February 2021 has no available Monday/Tuesday slots (too close)."""
        page = self._url_xml("/book/test-booking")
        # February should have no available slots (within modification deadline)
        self.assertTrue(
            page.cssselect(".o_wab_empty_month:contains('No available slots')")
        )

    def test_booking_page_march_has_slots(self):
        """March 2021 should have available slots on Mondays and Tuesdays."""
        page = self._url_xml("/book/test-booking/2021/3")
        self.assertTrue(page.cssselect(".o_wab_month_label:contains('March 2021')"))
        # Should have slot data in hidden JSON element
        slot_data_el = page.cssselect("#o_wab_slot_data")
        self.assertTrue(slot_data_el)
        # Calendar table should be present
        self.assertTrue(page.cssselect(".o_wab_table"))

    def test_booking_page_navigation(self):
        """Month navigation links work."""
        page = self._url_xml("/book/test-booking/2021/3")
        # Should have a next month link
        next_links = page.cssselect('a[href*="/book/test-booking/2021/4"]')
        self.assertTrue(next_links)

    def test_confirm_creates_booking(self):
        """Successful form submission creates a confirmed booking."""
        # First load the booking page to get a session and CSRF token
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Test Visitor",
            "email": "visitor@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/test-booking/confirm", data=data, timeout=30)
        # Should redirect to success page
        self.assertIn("/book/test-booking/success", response.url)
        # Verify booking was created in backend
        booking = self.env["resource.booking"].search(
            [
                ("type_id", "=", self.rbt.id),
                ("partner_ids.email", "=", "visitor@example.com"),
            ]
        )
        self.assertTrue(booking)
        self.assertEqual(booking.state, "confirmed")
        self.assertTrue(booking.meeting_id)
        # Verify partner was created
        partner = self.env["res.partner"].search(
            [("email", "=ilike", "visitor@example.com")]
        )
        self.assertTrue(partner)
        self.assertEqual(partner.name, "Test Visitor")

    def test_confirm_missing_fields(self):
        """Submitting with missing fields redirects with error."""
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "",
            "email": "test@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/test-booking/confirm", data=data)
        self.assertIn("error=", response.url)

    def test_confirm_missing_when(self):
        """Submitting with missing datetime redirects with error."""
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Test User",
            "email": "test@example.com",
            "when": "",
        }
        response = self.url_open("/book/test-booking/confirm", data=data)
        self.assertIn("error=", response.url)

    def test_confirm_invalid_date(self):
        """Submitting with invalid datetime redirects with error."""
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Test User",
            "email": "test@example.com",
            "when": "not-a-date",
        }
        response = self.url_open("/book/test-booking/confirm", data=data)
        self.assertIn("error=", response.url)

    def test_success_page_renders(self):
        """Success page renders properly."""
        page = self._url_xml("/book/test-booking/success")
        self.assertTrue(page.cssselect("h1:contains('Booking Confirmed')"))

    def test_existing_partner_reused(self):
        """If partner with same email exists, it is reused."""
        self.env["res.partner"].create(
            {"name": "Existing User", "email": "existing@example.com"}
        )
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Existing User",
            "email": "existing@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        self.url_open("/book/test-booking/confirm", data=data, timeout=30)
        partners = self.env["res.partner"].search(
            [("email", "=ilike", "existing@example.com")]
        )
        self.assertEqual(len(partners), 1)

    def test_website_description_displayed(self):
        """Website description is shown on the booking page."""
        self.rbt.website_description = "<p>Welcome to our booking page!</p>"
        page = self._url_xml("/book/test-booking")
        self.assertTrue(page.cssselect(":contains('Welcome to our booking page!')"))

    def test_location_pill_displayed(self):
        """Location is shown as a pill on the booking page."""
        self.rbt.location = "Main office"
        page = self._url_xml("/book/test-booking")
        self.assertTrue(page.cssselect(".o_wab_meta_pill:contains('Main office')"))


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestBookingRaceCondition(HttpCase):
    """Test race condition handling with a single resource combination.

    Uses a separate class so that the combination limiting and pre-booking
    happen in ``setUpClass``, making them visible to the HTTP server thread.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write(
            {
                "website_published": True,
                "website_slug": "race-test",
            }
        )
        # Limit to 1 combination so there is a real conflict
        cls.rbt.combination_rel_ids[1:].unlink()
        # Book the only slot via backend
        when_naive = datetime(2021, 3, 1, 10, 0)
        booking = cls.env["resource.booking"].create(
            {
                "type_id": cls.rbt.id,
                "partner_ids": [(4, cls.partner.id)],
                "combination_auto_assign": True,
            }
        )
        booking.start = when_naive
        booking.action_confirm()

    def _url_xml(self, url, data=None, timeout=10):
        """Open a URL and return its parsed lxml tree."""
        response = self.url_open(url, data, timeout=timeout)
        return fromstring(response.content)

    def _get_csrf_token(self, page):
        """Extract CSRF token from a page's hidden input."""
        inputs = page.cssselect('input[name="csrf_token"]')
        if inputs:
            return inputs[0].get("value")
        return ""

    def test_confirm_race_condition(self):
        """Double-booking the same slot shows an error message."""
        page = self._url_xml("/book/race-test/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Late Visitor",
            "email": "late@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/race-test/confirm", data=data, timeout=30)
        # Should redirect back to calendar with error, not to success
        self.assertNotIn("/success", response.url)
        self.assertIn("error=", response.url)
