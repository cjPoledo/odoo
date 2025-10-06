{
    "name": "ISO",
    "author": "Clent Japhet Poledo",
    "version": "1.0",
    "summary": "Tools for managing ISO-related documents",
    "application": True,
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/office.xml",
        "views/review_period.xml",
        "views/audit_period.xml",
        "views/audit_info.xml",
        "views/ror.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "upmin_iso/static/src/js/ror_tree_extend.js",
            "upmin_iso/static/src/xml/ror_list_button.xml",
            "upmin_iso/static/src/scss/ror_button.scss",
        ],
    },
    "icon": "upmin_iso/static/description/logo.jpeg",
    "license": "Other proprietary",
}
