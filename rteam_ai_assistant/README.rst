Rteam AI Assistant
==================

.. |badge_license| image:: https://img.shields.io/badge/license-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge_license|

Chat with your Odoo in Telegram. AI-powered assistant via @RteamAI_bot.

Features
--------

* Connect Odoo to the Rteam AI Telegram bot with a scoped, rotatable token.
* Ask questions in natural language (text or voice) in 20+ languages.
* Read-only or read-and-write scope, chosen per connection.
* Full conversation audit trail stored in Odoo.
* Uninstall = disconnect: removing the module revokes all tokens.

Supported versions
------------------

Odoo 14, 15, 16, 17, 18, 19 — Community and Enterprise.

Installation
------------

1. Install this module from Apps.
2. Go to Settings → Rteam AI → Connect Telegram Bot.
3. Generate a token, pick a scope.
4. Click "Open @RteamAI_bot on Telegram" — the bot starts with your token pre-filled.

Configuration
-------------

* ``rteam_ai_assistant.api_endpoint`` — Rteam AI service URL. Default: ``https://api.rteam.agency``.
* ``rteam_ai_assistant.bot_username`` — Telegram bot handle without ``@``. Default: ``RteamAI_bot``.

Usage
-----

Once connected, ask the bot any question about your Odoo data:

* "How many sales orders did we close last month?"
* "Show me overdue tasks assigned to Maria."
* "Create a lead for Acme Corp, 50K EUR budget." (requires read-and-write scope)

Voice notes work the same way — transcribed and answered in seconds.

Security
--------

* Tokens are stored as SHA-256 hashes; raw tokens are displayed once at generation.
* Scope (read or read+write) is chosen per connection and enforced on the Rteam AI side.
* Each connection can be rotated or revoked at any time.
* Conversation log is stored in your own Odoo, under Rteam AI → Conversations.

Credits
-------

**Author:** Rteam (https://rteam.agency)

**Contact:** alex@rteam.top

Maintainer
----------

This module is maintained by Rteam, an Odoo consulting and software development
agency specializing in Enterprise implementations, upgrades, and custom modules.
