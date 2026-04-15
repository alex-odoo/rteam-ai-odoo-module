import hashlib
import json
import logging
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REGISTER_TIMEOUT = 15
API_KEY_NAME_PREFIX = "Rteam AI Assistant"


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
        default=lambda self: self._default_label(),
        help="A name to recognize this connection later (shown in the connection list).",
    )

    @api.model
    def _default_label(self):
        company = self.env.user.company_id.name if self.env.user.company_id else None
        return company or "Telegram Bot"
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
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        api_key = self._generate_odoo_api_key(token_hash)
        self._register_with_rteam_ai(connection, token_hash, api_key)

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

    def _generate_odoo_api_key(self, token_hash):
        """Issue a scoped Odoo API key for the current user.

        The key is created via the standard `res.users.apikeys._generate` API
        (Odoo 17+) and is what the Rteam AI backend will use to authenticate
        XML-RPC calls on the user's behalf. The key is shown only at creation
        and is stored hashed by Odoo — we forward the raw value to our API
        once, then it is encrypted at rest on our side and never returned.
        """
        name = "%s (%s)" % (API_KEY_NAME_PREFIX, token_hash[:12])
        apikeys = self.env["res.users.apikeys"]
        try:
            try:
                return apikeys._generate("rpc", name, False)
            except TypeError:
                return apikeys._generate("rpc", name)
        except Exception as exc:
            _logger.exception("Failed to generate Odoo API key for user %s", self.env.user.id)
            raise UserError(_(
                "Could not create an Odoo API key for the Rteam AI connection: %s\n\n"
                "On Odoo 17+ this should work out of the box. On older versions the "
                "apikeys module may require activation.",
            ) % exc) from exc

    def _register_with_rteam_ai(self, connection, token_hash, api_key):
        api_endpoint = (
            self.env["ir.config_parameter"].sudo().get_param(
                "rteam_ai_assistant.api_endpoint", "https://rteam.agency"
            ).rstrip("/")
        )

        icp = self.env["ir.config_parameter"].sudo()
        odoo_url = icp.get_param("web.base.url") or ""
        odoo_database = self.env.cr.dbname
        odoo_user_login = self.env.user.login
        company = self.env.user.company_id.name if self.env.user.company_id else None

        payload = {
            "tokenHash": token_hash,
            "odooUrl": odoo_url,
            "odooDatabase": odoo_database,
            "odooUsername": odoo_user_login,
            "odooApiKey": api_key,
            "odooCompany": company,
            "odooUser": odoo_user_login,
            "scope": self.scope,
        }

        body = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(
            url="%s/api/v1/connections/register" % api_endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "rteam_ai_assistant/19.0 (Odoo module)",
            },
            method="POST",
        )

        try:
            with urlrequest.urlopen(req, timeout=REGISTER_TIMEOUT) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            _logger.error(
                "Rteam AI register failed: HTTP %s — %s", exc.code, raw[:500],
            )
            raise UserError(_(
                "Rteam AI service rejected the registration (HTTP %s).\n\n"
                "Please try again in a minute. If the issue persists, contact support@rteam.agency.",
            ) % exc.code) from exc
        except URLError as exc:
            _logger.error("Rteam AI register network error: %s", exc)
            raise UserError(_(
                "Could not reach the Rteam AI service (%s).\n\n"
                "Check your server's outbound internet access and try again.",
            ) % exc.reason) from exc

        remote_id = data.get("connectionId")
        remote_org = data.get("organizationName")
        if remote_id:
            connection.write({
                "remote_connection_id": remote_id,
                "remote_organization_name": remote_org or False,
                "last_used": fields.Datetime.now(),
            })

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
