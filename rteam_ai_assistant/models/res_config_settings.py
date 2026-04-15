from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rteam_ai_api_endpoint = fields.Char(
        string="Rteam AI API Endpoint",
        config_parameter="rteam_ai_assistant.api_endpoint",
        default="https://rteam.agency",
        help="Base URL of the Rteam AI service.",
    )
    rteam_ai_bot_username = fields.Char(
        string="Telegram Bot Username",
        config_parameter="rteam_ai_assistant.bot_username",
        default="RteamAI_bot",
        help="Telegram username of the Rteam AI bot (without the @).",
    )

    def action_open_rteam_ai_connect_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Connect to Rteam AI",
            "res_model": "rteam.ai.connect.wizard",
            "view_mode": "form",
            "target": "new",
        }
