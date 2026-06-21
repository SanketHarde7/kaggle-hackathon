from app.providers.factory import get_provider

def test_providers():
    providers = ["gemini", "claude", "gpt", "grok", "openrouter"]
    for p in providers:
        print(f"Testing {p}...")
        provider = get_provider(p, "dummy_key")
        print(f"Successfully instantiated {p} -> {type(provider).__name__}")
        
    try:
        get_provider("unknown", "key")
        print("FAIL: unknown provider did not raise ValueError")
    except ValueError as e:
        print(f"Success: unknown provider raised ValueError: {e}")

if __name__ == "__main__":
    test_providers()
