/* Copyright 2025 Ledo Enterprises LLC - Don Kendall
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

/**
 * Public booking page interactivity.
 *
 * Uses Odoo's publicWidget system so that the widget initializes correctly
 * with deferred/lazy asset loading in Odoo 18.  Reads slot data from a
 * hidden data attribute rendered server-side and handles day/slot
 * selection without additional network requests.
 */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteAppointmentBooking = publicWidget.Widget.extend({
    selector: ".o_wab_calendar",
    events: {
        "click .o_wab_day_available": "_onDayClick",
        "click .o_wab_slot_btn": "_onSlotClick",
    },

    /**
     * @override
     */
    start() {
        const dataEl = this.el.querySelector("#o_wab_slot_data");
        if (!dataEl) {
            return this._super(...arguments);
        }
        this.allSlots = JSON.parse(dataEl.dataset.slots || "[]");
        this.panel = this.el.querySelector("#o_wab_slots_panel");
        this.slotsTitle = this.panel
            ? this.panel.querySelector(".o_wab_slots_title")
            : null;
        this.slotsList = this.panel
            ? this.panel.querySelector(".o_wab_slots_list")
            : null;
        this.form = this.el.querySelector("#o_wab_form");
        this.whenInput = this.el.querySelector("#o_wab_when");
        this.selectedDisplay = this.el.querySelector("#o_wab_selected_display");
        this.slotsEmpty = this.el.querySelector("#o_wab_slots_empty");

        // Build lookup: date string -> [{time, iso}]
        this.slotsByDate = {};
        for (const slot of this.allSlots) {
            if (!this.slotsByDate[slot.date]) {
                this.slotsByDate[slot.date] = [];
            }
            this.slotsByDate[slot.date].push(slot);
        }
        return this._super(...arguments);
    },

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    /**
     * Handle click on an available calendar day.
     *
     * @param {Event} ev
     */
    _onDayClick(ev) {
        const td = ev.currentTarget;
        const date = td.dataset.date;
        if (!date || !this.slotsByDate[date]) {
            return;
        }

        // Highlight selected day
        this.el.querySelectorAll(".o_wab_day_selected").forEach((el) => {
            el.classList.remove("o_wab_day_selected");
        });
        td.classList.add("o_wab_day_selected");

        // Format the date for display
        const dateObj = new Date(date + "T00:00:00");
        const dateStr = dateObj.toLocaleDateString(undefined, {
            weekday: "long",
            month: "long",
            day: "numeric",
        });

        // Populate the slots panel
        if (this.slotsTitle) {
            this.slotsTitle.textContent = dateStr;
        }
        if (this.slotsList) {
            this.slotsList.innerHTML = "";
            for (const slot of this.slotsByDate[date]) {
                const btn = this.el.ownerDocument.createElement("button");
                btn.type = "button";
                btn.className = "o_wab_slot_btn";
                btn.textContent = slot.time;
                btn.dataset.iso = slot.iso;
                btn.dataset.display = dateStr + " at " + slot.time;
                this.slotsList.appendChild(btn);
            }
        }
        if (this.panel) {
            this.panel.classList.remove("d-none");
        }
        // Hide the empty-state placeholder
        if (this.slotsEmpty) {
            this.slotsEmpty.classList.add("d-none");
        }
        // Hide the booking form until a slot is picked
        if (this.form) {
            this.form.classList.add("d-none");
        }
        // Scroll to the slots panel
        if (this.panel) {
            this.panel.scrollIntoView({behavior: "smooth", block: "nearest"});
        }
    },

    /**
     * Handle click on a time slot button.
     *
     * @param {Event} ev
     */
    _onSlotClick(ev) {
        const btn = ev.currentTarget;

        // Highlight selected slot
        if (this.panel) {
            this.panel.querySelectorAll(".o_wab_slot_btn").forEach((el) => {
                el.classList.remove("active");
            });
        }
        btn.classList.add("active");

        // Fill form hidden input
        if (this.whenInput) {
            this.whenInput.value = btn.dataset.iso;
        }
        if (this.selectedDisplay) {
            this.selectedDisplay.textContent = btn.dataset.display;
        }
        if (this.form) {
            this.form.classList.remove("d-none");
            this.form.scrollIntoView({behavior: "smooth", block: "nearest"});
        }
    },
});
