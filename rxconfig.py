import os

import reflex as rx

config = rx.Config(
    app_name="k8sops",
    api_url=os.getenv("API_URL", "http://localhost:8000"),
    tailwind={
        "theme": {
            "extend": {},
        },
        "plugins": ["@tailwindcss/typography"],
    },
    # Disable sitemap plugin to avoid warnings
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)
