import hashlib
import logging
import secrets

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class RteamAiConnection(models.Model):
    _name = "rteam.ai.connection"
    _description = "Rteam AI Connection"
    _order = "create_date desc"

    name = fields.Char(
        string="Label",
        required=True,
        default=lambda self: _("Default Connection"),
    )
    user_id = fields.Many2one(
        "res.users",
        string="Owner",
        required=True,
        default=lambda self: self.env.user,
        ondelete="cascade",
    )
    token_last4 = fields.Char(
        string="Token (last 4)",
        readonly=True,
        help="Last 4 characters of the token, for identification only. "
             "The full token is never stored in Odoo after generation.",
    )
    token_hash = fields.Char(
        string="Token Hash",
        readonly=True,
        help="SHA-256 hash of the issued token. Used to verify incoming "
             "webhook requests from the Rteam AI service.",
    )
    api_endpoint = fields.Char(
        string="API Endpoint",
        required=True,
        default="https://api.rteam.agency",
        help="Base URL of the Rteam AI service. Change only if you run a "
             "self-hosted Rteam AI instance.",
    )
    remote_connection_id = fields.Char(
        string="Remote ID",
        readonly=True,
        help="Identifier of this connection on the Rteam AI service. "
             "Populated after the token is registered with our backend.",
    )
    remote_organization_name = fields.Char(
        string="Remote Organization",
        readonly=True,
        help="Organization name under which this connection is tracked on the Rteam AI service.",
    )
    bot_deep_link = fields.Char(
        string="Bot Deep Link",
        compute="_compute_bot_deep_link",
        help="Telegram deep link to start @RteamAI_bot with this connection token pre-filled.",
    )
    scope = fields.Selection(
        [
            ("read", "Read only"),
            ("read_write", "Read & write"),
        ],
        string="Scope",
        default="read",
        required=True,
        help="Read only: the assistant can answer questions but cannot modify records. "
             "Read & write: the assistant can also create and update records on your behalf.",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("revoked", "Revoked"),
        ],
        string="Status",
        default="draft",
        required=True,
        readonly=True,
    )
    last_used = fields.Datetime(string="Last Used", readonly=True)
    quota_used_today = fields.Integer(string="Queries Today", readonly=True)
    quota_limit = fields.Integer(
        string="Daily Limit",
        readonly=True,
        help="Daily query limit enforced by the Rteam AI service based on your subscription tier.",
    )

    _sql_constraints = [
        (
            "token_hash_uniq",
            "unique(token_hash)",
            "A connection with this token already exists.",
        ),
    ]

    @api.depends("token_last4", "state")
    def _compute_bot_deep_link(self):
        for record in self:
            if record.state == "active" and record.token_last4:
                record.bot_deep_link = (
                    "https://t.me/RteamAI_bot?start=connect_%s" % record.id
                )
            else:
                record.bot_deep_link = False

    def _issue_token(self):
        """Generate a fresh token, store its hash and last 4 chars, return the full token once."""
        self.ensure_one()
        raw_token = "rtai_" + secrets.token_urlsafe(32)
        self.write({
            "token_hash": hashlib.sha256(raw_token.encode()).hexdigest(),
            "token_last4": raw_token[-4:],
            "state": "active",
        })
        return raw_token

    def action_revoke(self):
        for record in self:
            if record.state == "revoked":
                continue
            record.write({
                "state": "revoked",
                "token_hash": False,
            })
            _logger.info("Rteam AI connection %s revoked by user %s", record.id, self.env.user.id)

    def action_rotate(self):
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active connections can be rotated."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Rotate Token"),
            "res_model": "rteam.ai.connect.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_connection_id": self.id,
                "default_mode": "rotate",
            },
        }
