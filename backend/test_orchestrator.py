import httpx
import json
import time

print("Sending full pipeline request...")
start_time = time.time()
response = httpx.post(
    "http://localhost:8000/analyze",
    json={"query": "should I use Zustand or Redux for a small React project", "workspace_path": "C:\\"},
    timeout=120.0
)
end_time = time.time()

if response.status_code == 200:
    print(f"Total time: {end_time - start_time:.2f} seconds")
    data = response.json()
    with open("output_brief.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("DecisionBrief saved to output_brief.json")
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"Error {response.status_code}: {response.text}")
