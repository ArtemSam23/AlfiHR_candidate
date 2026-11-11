"""Локальные заглушки для необязательного запуска. Это не предмет код-ревью."""

import asyncio
from collections import deque
from copy import deepcopy


class ScriptedModel:
    """Последовательно возвращает заранее заданные ответы вместо вызова LLM API."""

    def __init__(self, replies):
        self.replies = deque(deepcopy(replies))
        self.calls = []

    async def next(self, messages, tools):
        self.calls.append({"messages": deepcopy(messages), "tools": deepcopy(tools)})
        await asyncio.sleep(0)
        if self.replies:
            return self.replies.popleft()
        return {"kind": "final", "text": "Готово"}


class MemoryStore:
    """Дубль внешнего хранилища: объект живёт дольше отдельного экземпляра Agent."""

    def __init__(self):
        self.data = {}
        self.save_count = 0
        self.fail_on_save = None

    async def load(self, chat_id):
        return deepcopy(self.data.get(chat_id, []))

    async def save(self, chat_id, messages):
        self.save_count += 1
        if self.save_count == self.fail_on_save:
            raise RuntimeError("Хранилище временно недоступно")
        self.data[chat_id] = deepcopy(messages)


class HRService:
    """Тестовый HR API, уже привязанный к текущему сотруднику."""

    def __init__(self):
        self.requests = []
        self.lose_next_response = False

    async def vacation(self, start, end):
        request = {"id": f"vac-{len(self.requests) + 1}", "start": start, "end": end}
        self.requests.append(request)
        if self.lose_next_response:
            self.lose_next_response = False
            raise TimeoutError("Ответ HR API потерян")
        return deepcopy(request)


async def search(query):
    return [{
        "id": "leave-policy-1",
        "title": "Планирование отпуска",
        "text": "Заявку создают в HR-системе. После создания её согласует руководитель.",
        "url": "https://hr.example.test/policies/leave",
    }]
