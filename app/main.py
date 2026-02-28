# main.py

import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



from graph import run_graph
from nodes.expert import generate_persona_advice_stream

used_ips = set()

app = FastAPI(title="Expert Advice API")
app.add_middleware(
    CORSMiddleware,
    # WARNING: allow_origins=["*"] is for local dev only
    allow_origins=[
        "https://council-of-experts.onrender.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProblemRequest(BaseModel):
    problem: str


@app.post("/advice")
async def get_advice(payload: ProblemRequest, request: Request):
     # Get client IP (Render uses proxy → check headers first)
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0]
    else:
        client_ip = request.client.host

    # Restrict to one attempt per IP
    if client_ip in used_ips:
        raise HTTPException(
            status_code=429,
            detail="You have already used your one allowed attempt.",
        )

    # Mark IP as used
    used_ips.add(client_ip)
    
    try:
        # 1️⃣ Run graph (NO streaming here)
        graph_result = await run_graph(payload.problem)
        experts = graph_result["expert_data"]["experts"]

        # 2️⃣ Shared async queue for fan-in
        queue: asyncio.Queue = asyncio.Queue()

        # 3️⃣ Launch expert streaming task
        producer_task = asyncio.create_task(
            generate_persona_advice_stream(
                state={
                    "problem": payload.problem,
                    "expert_data": {"experts": experts},
                },
                queue=queue,
            )
        )

        # 4️⃣ Streaming generator
        async def event_stream():
            finished_experts = 0
            total_experts = len(experts)

            try:
                while True:
                    # Client disconnected → cancel everything
                    if await request.is_disconnected():
                        producer_task.cancel()
                        break

                    event = await queue.get()

                    if event["type"] == "done":
                        finished_experts += 1

                    yield json.dumps(event) + "\n"

                    if finished_experts >= total_experts:
                        break

            except asyncio.CancelledError:
                producer_task.cancel()
                raise

        # 5️⃣ Return streaming response
        return StreamingResponse(
            event_stream(),
            media_type="application/json",
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")
