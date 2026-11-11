"""Код агента"""

import asyncio
from copy import deepcopy


TOOL_DESCRIPTIONS = [
    {"name": "search", "description": "Поиск данных.",
     "args": {"query": "str"}},
    {"name": "vacation", "description": "Работа с отпуском.",
     "args": {"start": "str", "end": "str"}},
]


class Agent:
    def __init__(self, model, tools, store):
        self.model = model
        self.tools = tools
        self.store = store
        self.history = {}
        self.jobs = {}
        self.stopped = set()
        self.traces = {}

    async def send(self, chat_id: str, text: str) -> asyncio.Task:
        if chat_id not in self.history:
            self.history[chat_id] = await self.store.load(chat_id)
        self.history[chat_id].append({"role": "user", "content": text})
        await self.store.save(chat_id, self.history[chat_id])
        return self._start(chat_id)

    def _start(self, chat_id: str) -> asyncio.Task:
        self.stopped.discard(chat_id)
        self.traces[chat_id] = {
            "input": deepcopy(self.history[chat_id]),
            "events": [],
        }
        job = asyncio.create_task(self._run(chat_id))
        self.jobs[chat_id] = job
        return job

    async def _run(self, chat_id: str) -> str:
        history = self.history[chat_id]
        while chat_id not in self.stopped:
            context = history[-6:]
            decision = await self.model.next(context, TOOL_DESCRIPTIONS)
            self.traces[chat_id]["events"].append({
                "type": "model", "output": deepcopy(decision),
            })
            history.append({"role": "assistant", "content": decision})

            if decision["kind"] == "final":
                await self.store.save(chat_id, history)
                return decision["text"]

            name = decision["name"]
            args = decision["args"]
            result = await self._call_tool(name, args)
            history.append({"role": "tool", "name": name, "content": result})
            await self.store.save(chat_id, history)
            self.traces[chat_id]["events"].append({
                "type": "tool", "name": name,
                "args": deepcopy(args), "result": deepcopy(result),
            })

        return "Остановлено"

    async def _call_tool(self, name: str, args: dict):
        for attempt in range(2):
            try:
                return await asyncio.wait_for(self.tools[name](**args), timeout=2)
            except TimeoutError:
                continue
        raise TimeoutError(f"Инструмент {name} не ответил")

    def cancel(self, chat_id: str) -> None:
        self.stopped.add(chat_id)

    async def resume(self, chat_id: str) -> asyncio.Task:
        self.history[chat_id] = await self.store.load(chat_id)
        return self._start(chat_id)

    async def replay(self, chat_id: str) -> str:
        replay_id = f"{chat_id}:replay"
        self.history[replay_id] = deepcopy(self.traces[chat_id]["input"])
        return await self._start(replay_id)
