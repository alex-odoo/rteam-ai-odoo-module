from odoo.tests.common import TransactionCase


class TestRteamAiConnectWizard(TransactionCase):

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

    def test_03_rotate_without_connection_raises(self):
        from odoo.exceptions import UserError
        wizard = self.env["rteam.ai.connect.wizard"].create({
            "mode": "rotate",
        })
        with self.assertRaises(UserError):
            wizard.action_generate()
