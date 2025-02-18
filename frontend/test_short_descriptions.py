import sys
import os

# ✅ Ensure Python finds 'app/' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ✅ Now import from app
from short_descriptions import archetype_descriptions, expert_descriptions

# ✅ Print Data for Debugging# ✅ Prevent automatic execution unless explicitly run
if __name__ == "__main__":
    print("Archetype Descriptions:", archetype_descriptions)
    print("Expert Descriptions:", expert_descriptions)
