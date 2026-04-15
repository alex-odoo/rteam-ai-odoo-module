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
        default="https://rteam.agency",
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

    @api.depends("state")
    def _compute_bot_deep_link(self):
        """Plain bot URL for already-bound users.

        The one-time handshake deep link (with raw token) is only produced
        inside the wizard at generation time and is never stored. Once the
        user's Telegram account is bound to this Odoo, the bot recognises
        them by telegramId — no payload needed.
        """
        bot_username = self.env["ir.config_parameter"].sudo().get_param(
            "rteam_ai_assistant.bot_username", "RteamAI_bot"
        )
        for record in self:
            if record.state == "active":
                record.bot_deep_link = "https://t.me/%s" % bot_username
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

    def action_open_bot(self):
        self.ensure_one()
        if self.state != "active" or not self.bot_deep_link:
            raise UserError(_("Generate a token first to get the Telegram deep link."))
        return {
            "type": "ir.actions.act_url",
            "url": self.bot_deep_link,
            "target": "new",
        }

    @api.model
    def _cleanup_orphan_drafts(self):
        """Delete draft connections that never received a token.

        Drafts exist only as a transient state between `create()` and
        `_issue_token()`. Any draft surviving a session means the handshake
        rolled back mid-flight (or the record was created manually via the
        Connections list). They are never usable, so clean them up eagerly.
        """
        self.sudo().search([
            ("state", "=", "draft"),
            ("token_hash", "=", False),
        ]).unlink()

    @api.model
    def action_home(self):
        """Smart landing: open dashboard if user has an active connection,
        else open the onboarding wizard.

        Bound to the top-level "Rteam AI" menu item so the whole module has
        a single, context-aware entry point.
        """
        self._cleanup_orphan_drafts()

        active = self.sudo().search([
            ("user_id", "=", self.env.user.id),
            ("state", "=", "active"),
        ], limit=1)

        if active:
            view = self.env.ref("rteam_ai_assistant.view_rteam_ai_connection_dashboard")
            return {
                "type": "ir.actions.act_window",
                "name": "Rteam AI",
                "res_model": "rteam.ai.connection",
                "res_id": active.id,
                "view_mode": "form",
                "views": [(view.id, "form")],
                "target": "current",
            }

        return {
            "type": "ir.actions.act_window",
            "name": "Connect to Rteam AI",
            "res_model": "rteam.ai.connect.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_mode": "new"},
        }
