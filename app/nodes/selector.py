#app/nodes/selector.py
import json
from google import genai
from google.genai import types
import re
from core.llm import client

EXPERT_FINDER_PROMPT = """
{
  "instruction": {
    "role": "Expert Academic Researcher",
    "task": "Identify exactly 3 experts who have written a significant number of books on the user's problem.",
    "constraints": {
      "count": 3,
      "format": "JSON only",
      "strictness": "Do not provide more or fewer than 3 experts."
    },
    "output_schema": {
      "problem": "Brief description of the problem identified",
      "experts": [
        {
          "name": "Full name",
          "total_books_estimate": "Number of books written on this topic",
          "top_3_publications": ["Book 1", "Book 2", "Book 3"],
          "summary": "Expertise description"
        }
      ]
    }
  },
  "user_input": {
    "problem": "[INSERT YOUR PROBLEM HERE]"
  }
}
"""

def build_system_instruction(prompt_json: str) -> str:
    obj = json.loads(prompt_json)
    return json.dumps(obj, indent=2)

def find_experts(state):
    problem = state["problem"]
    prompt = EXPERT_FINDER_PROMPT.replace("[INSERT YOUR PROBLEM HERE]",problem)
    system_instruction = build_system_instruction(prompt)

    response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=[
        system_instruction,
        problem
    ],
    config=types.GenerateContentConfig(
        system_instruction=system_instruction
        )
    )

    try:
        # Regex JSON extraction is fragile but acceptable for controlled LLM output
        json_str = re.search(r'\{.*\}', response.text, re.S).group()
        expert_data = json.loads(json_str)
    except Exception:
        raise ValueError("Gemini failed to return valid JSON")

    if len(expert_data.get("experts", [])) != 3:
        raise ValueError("Expert finder must return exactly 3 experts")

    return {
        "expert_data": expert_data
    }
