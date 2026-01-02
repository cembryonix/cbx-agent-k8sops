

from .system import DEFAULT_SYSTEM_PROMPT
from .model_prompts import MODEL_SPECIFIC_INSTRUCTIONS
from .kubernetes import KUBERNETES_CONTEXT


def get_system_prompt(model_name: str) -> str:
    """Build complete system prompt for specific model."""
    base_prompt = DEFAULT_SYSTEM_PROMPT

    # Always add Kubernetes context awareness
    k8s_context = KUBERNETES_CONTEXT

    # Get model-specific instructions
    model_instructions = MODEL_SPECIFIC_INSTRUCTIONS.get(
        model_name.lower(),
        MODEL_SPECIFIC_INSTRUCTIONS.get("default", "")
    )

    # Combine all instructions
    complete_prompt = f"{base_prompt}\n\n{k8s_context}"

    if model_instructions:
        complete_prompt = f"{complete_prompt}\n\n{model_instructions}"

    return complete_prompt
