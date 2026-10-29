import hashlib
import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from odoo.addons.rteam_ai_assistant.wizard import rteam_ai_connect_wizard


class TestRteamAiConnectWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        # action_generate registers the token with the production Rteam AI API:
        # unmocked, every test run created an organization there.
        patcher = patch.object(
            type(self.env["rteam.ai.connect.wizard"]),
            "_register_with_rteam_ai",
            autospec=True,
        )
        self.register = patcher.start()
        self.addCleanup(patcher.stop)

    def test_01_new_connection_flow(self):
        wizard = self.env["rteam.ai.connect.wizard"].create({
            "mode": "new",
            "label": "Test Connection",
            "scope": "read",
        })
        self.assertEqual(wizard.step, "form")
        wizard.action_generate()
        self.assertEqual(wizard.step, "result")
        self.assertTrue(wizard.generated_token)
        self.assertTrue(wizard.generated_token.startswith("rtai_"))
        self.assertTrue(wizard.connection_id)
        self.assertEqual(wizard.connection_id.state, "active")
        self.assertEqual(wizard.connection_id.name, "Test Connection")
        self.assertTrue(wizard.bot_deep_link)
        self.assertIn("RteamAI_bot", wizard.bot_deep_link)

        self.register.assert_called_once()
        _wizard, connection, token_hash, api_key = self.register.call_args[0]
        self.assertEqual(connection, wizard.connection_id)
        self.assertEqual(token_hash, hashlib.sha256(wizard.generated_token.encode()).hexdigest())
        self.assertTrue(api_key)

    def test_02_rotate_flow(self):
        conn = self.env["rteam.ai.connection"].create({"name": "Existing"})
        original_token = conn._issue_token()
        original_hash = conn.token_hash

        wizard = self.env["rteam.ai.connect.wizard"].create({
            "mode": "rotate",
            "connection_id": conn.id,
            "scope": "read_write",
        })
        wizard.action_generate()
        self.assertNotEqual(conn.token_hash, original_hash)
        self.assertEqual(conn.scope, "read_write")
        self.assertEqual(conn.state, "active")
        self.assertNotEqual(wizard.generated_token, original_token)
        self.register.assert_called_once()

    def test_03_rotate_without_connection_raises(self):
        from odoo.exceptions import UserError
        wizard = self.env["rteam.ai.connect.wizard"].create({
            "mode": "rotate",
        })
        with self.assertRaises(UserError):
            wizard.action_generate()
        self.register.assert_not_called()

    def test_04_register_posts_payload_and_stores_remote_ids(self):
        conn = self.env["rteam.ai.connection"].create({"name": "Remote"})
        wizard = self.env["rteam.ai.connect.wizard"].create({
            "mode": "rotate",
            "connection_id": conn.id,
            "scope": "read",
        })
        response = MagicMock()
        response.read.return_value = json.dumps({
            "connectionId": "conn_test",
            "organizationName": "Test Org",
        }).encode("utf-8")
        with patch.object(rteam_ai_connect_wizard.urlrequest, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            # The original method, past the class-level mock from setUp.
            rteam_ai_connect_wizard.RteamAiConnectWizard._register_with_rteam_ai(
                wizard, conn, "hash_test", "key_test",
            )

        request = urlopen.call_args[0][0]
        self.assertTrue(request.full_url.endswith("/api/v1/connections/register"))
        self.assertEqual(request.get_method(), "POST")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["tokenHash"], "hash_test")
        self.assertEqual(body["odooApiKey"], "key_test")
        self.assertEqual(body["odooDatabase"], self.env.cr.dbname)
        self.assertEqual(body["odooUsername"], self.env.user.login)
        self.assertEqual(body["scope"], "read")
        self.assertEqual(conn.remote_connection_id, "conn_test")
        self.assertEqual(conn.remote_organization_name, "Test Org")
