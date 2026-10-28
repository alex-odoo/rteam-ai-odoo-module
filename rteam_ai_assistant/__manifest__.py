{
    "name": "AI Analytic Assistant",
    "summary": (
        "AI-powered assistant for Odoo via @RteamAI_bot on Telegram. "
        "Ask questions in natural language, get answers from your ERP. "
        "Voice input, multilingual. Works on Odoo 14-20, Community and Enterprise."
    ),
    "version": "20.0.1.2.1",
    "category": "Productivity",
    "author": "Rteam",
    "maintainer": "Rteam",
    "website": "https://rteam.agency/en/ai-bot",
    "support": "alex@rteam.top",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
        "mail",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "data/ir_config_parameter_data.xml",
        "views/rteam_ai_connection_views.xml",
        "views/rteam_ai_dashboard_views.xml",
        "wizard/rteam_ai_connect_wizard_views.xml",
        "views/rteam_ai_menus.xml",
        'security/ir.access.csv',
    ],
    "images": [
        "static/description/banner.png",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
