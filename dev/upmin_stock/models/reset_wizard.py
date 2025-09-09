from odoo import models, fields
from odoo.exceptions import UserError


class ResetWizard(models.TransientModel):
    _name = "upmin_stock.reset_wizard"
    _description = "Reset Wizard"

    confirm_reset = fields.Boolean(
        string="I understand this will reset all stock balances and issuances.",
        required=True,
        default=False,
    )

    def reset_data(self):
        if not self.confirm_reset:
            raise UserError("Please confirm before resetting.")

        # load all needed models
        issuance_model = self.env["upmin_stock.issuance"]
        procurement_wizard_model = self.env["upmin_stock.procurement_wizard"]

        # delete all stock balances
        all_procurement_wizards = procurement_wizard_model.search([])
        all_procurement_wizards.unlink()

        # delete all issuances
        all_issuances = issuance_model.search([])
        all_issuances.wizard_unlink()

        return {
            "effect": {
                "fadeout": "slow",
                "message": "Stock Balances and Issuances have been reset! Please refresh the page.",
                "type": "rainbow_man",
            }
        }
