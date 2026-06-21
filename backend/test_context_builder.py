import sys
import os

# Add backend to path so we can import
sys.path.append(os.path.abspath("."))

from app.memory.context_builder import build_memory_context

if __name__ == "__main__":
    print("--- Memory Context for: 'What data caching strategy should I use?' ---")
    print(build_memory_context(".", "What data caching strategy should I use?", token_budget=1500))
    print("\n--- Memory Context for: 'Should I use Zustand or Redux?' ---")
    print(build_memory_context(".", "Should I use Zustand or Redux?", token_budget=1500))
