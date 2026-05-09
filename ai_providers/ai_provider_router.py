def generate_ai_response(provider: str, prompt: str) -> str:
    if provider == "openai":
        from .openai_provider_adapter import call_openai

        return call_openai(prompt)

    elif provider == "oci":
        from .oci_provider_adapter import call_oci_genai

        return call_oci_genai(prompt)

    else:
        raise ValueError(f"Unknown provider: {provider}")
