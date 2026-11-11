"""Необязательный запуск одного успешного сценария без сети и API-ключей."""

import asyncio

from agent import Agent
from integrations import HRService, MemoryStore, ScriptedModel, search


async def main():
    model = ScriptedModel([
        {"kind": "tool", "name": "search", "args": {"query": "как оформить отпуск"}},
        {"kind": "final", "text": "Заявку создают в HR-системе, затем её согласует руководитель."},
    ])
    hr = HRService()
    agent = Agent(model, {"search": search, "vacation": hr.vacation}, MemoryStore())
    job = await agent.send("chat-1", "Как оформить отпуск?")
    print(await job)


if __name__ == "__main__":
    asyncio.run(main())
