from odoo.tests.common import TransactionCase


class TestRteamAiConnection(TransactionCase):

    def test_01_create_defaults(self):
        conn = self.env["rteam.ai.connection"].create({})
        self.assertEqual(conn.state, "draft")
        self.assertEqual(conn.scope, "read")
        self.assertEqual(conn.api_endpoint, "https://api.rteam.agency")
        self.assertEqual(conn.user_id, self.env.user)

    def test_02_issue_token_marks_active(self):
        conn = self.env["rteam.ai.connection"].create({})
        token = conn._issue_token()
        self.assertTrue(token.startswith("rtai_"))
        self.assertEqual(conn.state, "active")
        self.assertEqual(conn.token_last4, token[-4:])
        self.assertTrue(conn.token_hash)
        self.assertEqual(len(conn.token_hash), 64)

    def test_03_revoke(self):
        conn = self.env["rteam.ai.connection"].create({})
        conn._issue_token()
        conn.action_revoke()
        self.assertEqual(conn.state, "revoked")
        self.assertFalse(conn.token_hash)

    def test_04_bot_deep_link_only_when_active(self):
        conn = self.env["rteam.ai.connection"].create({})
        self.assertFalse(conn.bot_deep_link)
        conn._issue_token()
        self.assertTrue(conn.bot_deep_link)
        self.assertIn("RteamAI_bot", conn.bot_deep_link)
        conn.action_revoke()
        self.assertFalse(conn.bot_deep_link)

    def test_05_unique_token_hash(self):
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        conn1 = self.env["rteam.ai.connection"].create({})
        conn1._issue_token()
        conn2 = self.env["rteam.ai.connection"].create({})
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            conn2.write({"token_hash": conn1.token_hash})
            self.env.flush_all()
