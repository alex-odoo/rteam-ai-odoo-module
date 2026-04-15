# Rteam AI — Odoo Module

Official Odoo module that connects any Odoo instance to **[@RteamAI_bot](https://t.me/RteamAI_bot)** — an AI assistant that lets you chat with your ERP in Telegram (text or voice, 20+ languages).

**Learn more:** [rteam.agency/en/ai-bot](https://rteam.agency/en/ai-bot)

## Supported versions

This repository ships the `rteam_ai_assistant` module for:

| Branch | Odoo version | Edition |
|--------|--------------|---------|
| `14.0` | Odoo 14      | Community + Enterprise |
| `15.0` | Odoo 15      | Community + Enterprise |
| `16.0` | Odoo 16      | Community + Enterprise |
| `17.0` | Odoo 17      | Community + Enterprise |
| `18.0` | Odoo 18      | Community + Enterprise |
| `19.0` | Odoo 19      | Community + Enterprise |

Each branch is independently installable and tested on the matching Odoo release.

## Install from Apps

The easiest way: install [Rteam AI Assistant](https://apps.odoo.com) from the official Odoo Apps store.

## Install from source

```bash
# Pick the branch matching your Odoo version (example: v19)
git clone --branch 19.0 https://github.com/alex-odoo/rteam-ai-odoo-module.git
cp -r rteam-ai-odoo-module/rteam_ai_assistant /path/to/odoo/addons/
# Restart Odoo, then update the app list and install "Rteam AI Assistant"
```

## How it works

This module is a thin client. It:

1. Adds a **Rteam AI** menu and a **Settings → Rteam AI** configuration page.
2. Generates scoped API tokens (read-only or read+write).
3. Deep-links you into @RteamAI_bot with the token pre-filled.
4. Exposes the conversation log under **Rteam AI → Conversations**.

All AI logic, Odoo schema detection, query planning, and voice processing happen on the Rteam AI service (`api.rteam.agency`) — not in this module. Removing the module automatically revokes all tokens.

## Pricing

The module is free and LGPL-3. The Rteam AI service has a free tier (20 queries/day, 1 user, read-only) that works forever — no credit card needed. Paid tiers unlock unlimited queries, write actions, voice input, multi-user, and custom workflows. See [rteam.agency/en/ai-bot](https://rteam.agency/en/ai-bot).

## Development

```bash
# Run module tests on Odoo 19
odoo-bin -d test_db --test-enable -i rteam_ai_assistant --stop-after-init
```

## License

LGPL-3. See [LICENSE](LICENSE).

## Maintainer

**Rteam** — Odoo consulting and software development agency.
[rteam.agency](https://rteam.agency) · alex@rteam.top
