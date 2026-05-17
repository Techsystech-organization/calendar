When a visitor books a paid appointment:

1. They select a time slot and fill in their contact details.
2. On submission, a ``resource.booking`` record is created in **scheduled**
state and a sale order is generated.
3. The visitor is redirected to the website checkout flow.
4. Once payment is confirmed, the booking is automatically moved to
**confirmed** state and calendar invitations are sent.
5. If the visitor abandons checkout, a cron job cancels the expired hold
after the configured expiry time.
