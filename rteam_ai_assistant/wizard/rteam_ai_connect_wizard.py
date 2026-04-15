from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RteamAiConnectWizard(models.TransientModel):
    _name = "rteam.ai.connect.wizard"
    _description = "Connect to Rteam AI"

    mode = fields.Selection(
        [
            ("new", "New Connection"),
            ("rotate", "Rotate Existing Token"),
        ],
        default="new",
        required=True,
    )
    connection_id = fields.Many2one(
        "rteam.ai.connection",
        string="Connection",
        help="Existing connection being rotated. Only used in rotate mode.",
    )
    label = fields.Char(
        string="Label",
        default=lambda self: _("Default Connection"),
        help="A name to recognize this connection later (shown in the connection list).",
    )
    scope = fields.Selection(
        [
            ("read", "Read only"),
            ("read_write", "Read & write"),
        ],
        string="Scope",
        default="read",
        required=True,
    )
    generated_token = fields.Char(
        string="Your Token",
        readonly=True,
        help="Copy this token now — it is shown only once and cannot be retrieved later. "
             "Paste it into @RteamAI_bot on Telegram using the /connect command.",
    )
    bot_deep_link = fields.Char(
        string="Open Bot",
        readonly=True,
    )
    step = fields.Selection(
        [
            ("form", "Form"),
            ("result", "Result"),
        ],
        default="form",
    )

    def action_generate(self):
        self.ensure_one()
        if self.mode == "new":
            connection = self.env["rteam.ai.connection"].create({
                "name": self.label,
                "scope": self.scope,
            })
        elif self.mode == "rotate":
            if not self.connection_id:
                raise UserError(_("No connection selected to rotate."))
            connection = self.connection_id
            connection.write({"scope": self.scope})
        else:
            raise UserError(_("Unknown wizard mode."))

        token = connection._issue_token()
        bot_username = self.env["ir.config_parameter"].sudo().get_param(
            "rteam_ai_assistant.bot_username", "RteamAI_bot"
        )
        self.write({
            "connection_id": connection.id,
            "generated_token": token,
            "bot_deep_link": "https://t.me/%s?start=token_%s" % (bot_username, token),
            "step": "result",
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_open_bot(self):
        self.ensure_one()
        if not self.bot_deep_link:
            raise UserError(_("Bot link is not available. Generate a token first."))
        return {
            "type": "ir.actions.act_url",
            "url": self.bot_deep_link,
            "target": "new",
        }

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}
