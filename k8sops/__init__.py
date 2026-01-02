"""K8SOps - Kubernetes Operations Agent."""

__version__ = "0.2.0"

from k8sops.session import AgentSession, SessionSettings

__all__ = ["AgentSession", "SessionSettings"]
