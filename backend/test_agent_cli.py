"""CLI test script to verify LangGraph triage on all 3 seed tickets with rate-limiting and concurrency controls."""

import asyncio
import sys
import time

from app.agent.graph import GRAPH_CONFIG, triage_graph
from app.core.config import settings
from app.data.seed import SEED_TICKETS


async def triage_single_ticket(ticket, semaphore: asyncio.Semaphore):
    """Run triage on a single ticket within semaphore concurrency limit."""
    initial_state = {
        "ticket": ticket.model_dump(),
        "messages": [],
        "trace": [],
        "tool_calls_made": 0,
        "result": None,
        "error": None,
    }

    start = time.perf_counter()
    async with semaphore:
        final_state = await triage_graph.ainvoke(initial_state, config=GRAPH_CONFIG)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return ticket, final_state, elapsed_ms


def print_result(ticket, final_state, elapsed_ms):
    """Pretty-print triage result for a single ticket."""
    res = final_state.get("result", {})
    print(f"\n--- {ticket.id} ({ticket.user_id}) | {elapsed_ms}ms ---")
    print(f"Message: {ticket.text}")
    print(f"[Tag]: {res.get('tag')}")
    print(f"[Draft]: {res.get('draft')}")
    print(f"[Reasoning]: {res.get('reasoning')}")
    print(f"[Trace Steps]: {len(final_state.get('trace', []))}")
    for step in final_state.get("trace", []):
        print(f"  -> Step {step['step']} | {step['node']} | {step['type']} | Tool: {step.get('tool')}")
    print("=" * 50)


async def run_test():
    total_start = time.perf_counter()

    print("=" * 65)
    print("  TriageForge LangGraph Agent - Rate-Controlled Triage Test")
    print(f"  Model: {settings.groq_model} | Fallback: {settings.llm_fallback_model}")
    print(f"  Rate Limit: {settings.llm_requests_per_minute} RPM | Concurrency: {settings.test_concurrency}")
    print("=" * 65)

    # Concurrency control via Semaphore
    semaphore = asyncio.Semaphore(settings.test_concurrency)

    # Launch tickets concurrently with return_exceptions=True
    tasks = [triage_single_ticket(ticket, semaphore) for ticket in SEED_TICKETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = 0
    failure_count = 0

    for idx, item in enumerate(results):
        ticket = SEED_TICKETS[idx]
        if isinstance(item, Exception):
            failure_count += 1
            error_message = str(item).replace(settings.groq_api_key, "[REDACTED]") if settings.groq_api_key else str(item)
            print(f"\n[FAILED] {ticket.id} ({ticket.user_id}): {error_message}")
            print("=" * 50)
        else:
            success_count += 1
            t_obj, final_state, elapsed_ms = item
            print_result(t_obj, final_state, elapsed_ms)

    total_ms = int((time.perf_counter() - total_start) * 1000)

    print("\n" + "=" * 65)
    print("  TRIAGE EXECUTION SUMMARY")
    print(f"  Total Tickets: {len(SEED_TICKETS)} | Succeeded: {success_count} | Failed: {failure_count}")
    print(f"  Total Wall Time: {total_ms}ms ({total_ms / 1000:.2f}s)")
    print("=" * 65)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    asyncio.run(run_test())
