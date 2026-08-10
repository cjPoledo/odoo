/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";

const originalGetCellTitle = ListRenderer.prototype.getCellTitle;

patch(ListRenderer.prototype, "upmin_iso.html_tooltip_strip", {
    getCellTitle(column, record) {
        const title = originalGetCellTitle.call(this, column, record);
        if (this.fields[column.name].type === "html" && title) {
            const div = document.createElement("div");
            div.innerHTML = String(title);
            return div.textContent || div.innerText || "";
        }
        return title;
    },
});
