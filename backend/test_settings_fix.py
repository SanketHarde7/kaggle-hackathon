import sys
import os

sys.path.append(os.path.abspath("."))
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("--- Testing valid provider ---")
response1 = client.post("/settings", json={"provider": "gpt", "api_key": "dummy_key"})
print("Status Code:", response1.status_code)
print("Response:", response1.json())

print("\n--- Testing invalid provider ---")
response2 = client.post("/settings", json={"provider": "chatgpt", "api_key": "dummy_key"})
print("Status Code:", response2.status_code)
print("Response:", response2.json())
