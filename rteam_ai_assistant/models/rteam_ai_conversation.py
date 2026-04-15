from odoo import fields, models


class RteamAiConversation(models.Model):
    _name = "rteam.ai.conversation"
    _description = "Rteam AI Conversation Log"
    _order = "create_date desc"

    connection_id = fields.Many2one(
        "rteam.ai.connection",
        string="Connection",
        required=True,
        ondelete="cascade",
        index=True,
    )
    user_id = fields.Many2one(
        related="connection_id.user_id",
        store=True,
        index=True,
    )
    question = fields.Text(string="Question", required=True)
    answer = fields.Text(string="Answer")
    channel = fields.Selection(
        [
            ("telegram_text", "Telegram (text)"),
            ("telegram_voice", "Telegram (voice)"),
        ],
        string="Channel",
        default="telegram_text",
    )
    duration_ms = fields.Integer(string="Response Time (ms)")
    tokens_used = fields.Integer(string="Tokens Used")
    error = fields.Char(string="Error", help="Error message if the query failed.")
