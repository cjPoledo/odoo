from odoo import models, fields


class ResetWizard(models.TransientModel):
    _name = "upmin_stock.reset_wizard"
    _description = "Reset Wizard"

    def reset_data(self):
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
                "message": "Issuances have been reset!",
                "type": "rainbow_man",
            }
        }
