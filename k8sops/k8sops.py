"""K8SOps - Reflex app entry point.

This module serves as the Reflex entry point, importing the app from the UI package.
"""

# Re-export the app from the UI module
from k8sops.ui.app import app

__all__ = ["app"]
