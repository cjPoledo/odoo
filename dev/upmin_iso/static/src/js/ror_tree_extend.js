/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
export class RORListController extends ListController {
  setup() {
    super.setup();
  }
  onExportRORClick() {
    this.actionService.doAction({
      type: "ir.actions.act_window",
      res_model: "upmin_iso.ror_export_wizard",
      name: "Export ROR",
      view_mode: "form",
      views: [[false, "form"]],
      target: "new",
    });
  }
}
registry.category("views").add("button_in_tree", {
  ...listView,
  Controller: RORListController,
  buttonTemplate: "button_ror.ListView.Buttons",
});
