# app/nodes/expert.py

import json
import asyncio
from typing import Dict, Any
from google import genai
from google.genai import types
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor

from core.llm import client


PERSONA_PROMPT = """
{
  "system_instruction": "You are a high-fidelity persona emulator. Your task is to process the provided JSON identity data and respond to a problem strictly from that individual's perspective.",
  "execution_rules": [
    "Adopt the vocabulary, era-appropriate language, and professional expertise of the subject.",
    "Reference the subject's known works, philosophies, or historical actions in the response.",
    "Maintain the person's unique psychological profile (e.g., a scientist should be analytical, a king should be authoritative).",
    "Stay in character consistently; do not provide 'AI' disclaimers unless safety is at risk."
  ],
  "input_format_required": {
    "identity_profile": "The JSON object containing name, publications/works, and summary.",
    "user_problem": "The specific scenario or question to be addressed."
  },
  "required_output": "Plain text only. Do not return JSON or metadata."
}
"""


def build_system_instruction(prompt_json: str) -> str:
    obj = json.loads(prompt_json)
    return json.dumps(obj, indent=2)


async def stream_expert_advice(
    expert: Dict[str, Any],
    problem: str,
    queue: asyncio.Queue
):
    expert_name = expert.get("name", "Unknown Expert")
    system_instruction = build_system_instruction(PERSONA_PROMPT)
    loop = asyncio.get_running_loop()

    def blocking_stream():
        try:
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash-lite",
                contents=[
                    system_instruction,
                    json.dumps({
                        "identity_profile": expert,
                        "user_problem": problem
                    })
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )

            for chunk in response:
                if not chunk.text:
                    continue

                asyncio.run_coroutine_threadsafe(
                    queue.put({
                        "type": "delta",
                        "expert": expert_name,
                        "content": chunk.text
                    }),
                    loop
                )

        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "error",
                    "expert": expert_name,
                    "message": str(e)
                }),
                loop
            )
        finally:
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "done",
                    "expert": expert_name
                }),
                loop
            )

    # Run blocking Gemini stream in thread
    await loop.run_in_executor(None, blocking_stream)




async def generate_persona_advice_stream(state: Dict[str, Any], queue: asyncio.Queue):
    """
    Launches all experts in parallel and streams their outputs.
    This function RETURNS NOTHING.
    """
    problem = state["problem"]
    experts = state["expert_data"]["experts"]

    tasks = [
        asyncio.create_task(
            stream_expert_advice(expert, problem, queue)
        )
        for expert in experts
    ]

    # Wait for all experts to finish (stream continues meanwhile)
    await asyncio.gather(*tasks)
