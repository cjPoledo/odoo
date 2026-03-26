/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";

const UPMIN_ISO_PREFIX = "upmin_iso.";
const originalOnDeleteRecord = ListRenderer.prototype.onDeleteRecord;

patch(ListRenderer.prototype, "upmin_iso.confirm_delete", {
    async onDeleteRecord(record) {
        const model = this.props.list && this.props.list.resModel;

        if (!model || !model.startsWith(UPMIN_ISO_PREFIX)) {
            return originalOnDeleteRecord.call(this, record);
        }
        let confirmed = false;
        await new Promise((resolve) => {
            this.env.services.dialog.add(ConfirmationDialog, {
                body: "Are you sure you want to remove this item?",
                confirm: () => { confirmed = true; resolve(); },
                cancel: () => resolve(),
            });
        });
        if (confirmed) {
            return originalOnDeleteRecord.call(this, record);
        }
    },
});
