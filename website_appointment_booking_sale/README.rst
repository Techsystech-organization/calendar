.. image:: https://odoo-community.org/readme-banner-image
   :target: https://odoo-community.org/get-involved?utm_source=readme
   :alt: Odoo Community Association

==================================
Website Appointment Booking Sale
==================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fcalendar-lightgray.png?logo=github
    :target: https://github.com/OCA/calendar/tree/18.0/website_appointment_booking_sale
    :alt: OCA/calendar
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/calendar-18-0/calendar-18-0-website_appointment_booking_sale
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runboat-Try%20me-875A7B.png
    :target: https://runboat.odoo-community.org/builds?repo=OCA/calendar&target_branch=18.0
    :alt: Try me on Runboat

|badge1| |badge2| |badge3| |badge4| |badge5|

This module adds paid booking checkout to the **Website Appointment Booking**
module. It is an optional add-on: install it only if you want visitors to pay
before their appointment is confirmed.

Key features:

- Require upfront payment per booking type
- Fixed-price or product-list-price checkout
- Automatic sale order and checkout redirect on booking submission
- Booking confirmed only after payment is complete
- Automatic cleanup of abandoned checkout holds

**Table of contents**

.. contents::
   :local:

Installation
============

This module requires ``website_appointment_booking``, ``sale``, and
``website_sale`` to be installed.

Configuration
=============

1. Open a booking type under **Resource Bookings > Types**.
2. In the **Website** section, check **Require Upfront Payment**.
3. Select a **Payment Product** (a service-type product).
4. Set a **Payment Price** (or leave at 0 to use the product's list price).
5. Optionally set **Payment Hold Expiry Hours** (default: 24) for abandoned
   checkout cleanup.

Usage
=====

When a visitor books a paid appointment:

1. They select a time slot and fill in their contact details.
2. On submission, a ``resource.booking`` record is created in **scheduled**
   state and a sale order is generated.
3. The visitor is redirected to the website checkout flow.
4. Once payment is confirmed, the booking is automatically moved to
   **confirmed** state and calendar invitations are sent.
5. If the visitor abandons checkout, a cron job cancels the expired hold
   after the configured expiry time.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/calendar/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/calendar/issues/new?body=module:%20website_appointment_booking_sale%0Aversion:%2018.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
-------

* Ledo Enterprises LLC

Contributors
------------

- `Ledo Enterprises LLC <https://ledoweb.com>`__:

  - Don Kendall

Maintainers
-----------

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

.. |maintainer-dnplkndll| image:: https://github.com/dnplkndll.png?size=40px
    :target: https://github.com/dnplkndll
    :alt: dnplkndll

Current `maintainer <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-dnplkndll|

This module is part of the `OCA/calendar <https://github.com/OCA/calendar/tree/18.0/website_appointment_booking_sale>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
