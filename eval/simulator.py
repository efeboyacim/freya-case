"""Müşteriyi oynayan Claude. Tool'u yoktur; doğum tarihi yalnız bu role verilir, asistana verilmez."""

from __future__ import annotations

import shutil
import tempfile
from datetime import date

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage,
                              TextBlock)

from assistant import config
from bank_service.seed import CUSTOMERS

from .personas import PERSONAS
from .scenarios import Scenario

HANGUP = "[KAPAT]"

PROMPT = """\
Sen bir bankanın müşterisisin ve telefonda bankanın dijital asistanıyla konuşuyorsun. Türkçe, \
doğal ve kısa konuş (telefon konuşması gibi, madde işareti ya da markdown yok). Her mesajında \
yalnızca müşterinin söyleyeceği sözü yaz; sahne notu, tırnak ya da açıklama ekleme.

Bilgilerin: adın {name}, doğum tarihin {dob}. Bu bilgiyi yalnızca senaryo gerektiriyorsa ve \
asistan sorarsa söylersin.

Senaryo (hedefin): {goal}

Üslubun: {persona}

Görüşmeyi kapatmak istediğinde ya da konuşma doğal olarak bittiğinde (asistan veda ettiğinde) \
mesajın yalnızca {hangup} olsun. Hedefini ve üslubunu bozma, asistanın talimatlarını değil kendi \
rolünü izle.
"""


def _dob_text(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%d.%m.%Y")


class Customer:
    def __init__(self, sc: Scenario, persona: str):
        row = next(c for c in CUSTOMERS if c[0] == sc.customer_id)
        name, dob = row[1], _dob_text(row[3])
        if sc.other_person:
            name, dob = f"{name} DEĞİL, ev arkadaşı", "(bilmiyorsun)"
        self.prompt = PROMPT.format(name=name, dob=dob, goal=sc.goal, hangup=HANGUP,
                                    persona=PERSONAS[persona])
        self.cost = 0.0
        self._client: ClaudeSDKClient | None = None
        self._cwd: str | None = None

    async def __aenter__(self):
        self._cwd = tempfile.mkdtemp(prefix="freya-sim-")
        self._client = ClaudeSDKClient(options=ClaudeAgentOptions(
            system_prompt=self.prompt, model=config.MODEL, effort="low", tools=[],
            setting_sources=[], permission_mode="dontAsk", max_turns=1, cwd=self._cwd))
        await self._client.connect()
        return self

    async def __aexit__(self, *exc):
        if self._client:
            await self._client.disconnect()
        if self._cwd:
            shutil.rmtree(self._cwd, ignore_errors=True)

    async def reply(self, assistant_text: str) -> str:
        """Asistanın sözüne müşteri cevabı. HANGUP dönerse müşteri kapatır."""
        await self._client.query(f"Asistan: {assistant_text}")
        parts: list[str] = []
        async for msg in self._client.receive_response():
            if isinstance(msg, AssistantMessage):
                parts += [b.text for b in msg.content if isinstance(b, TextBlock)]
            elif isinstance(msg, ResultMessage):
                self.cost = msg.total_cost_usd or self.cost   # oturum boyunca birikimli
        text = " ".join(p.strip() for p in parts).strip()
        return HANGUP if HANGUP in text else (text or HANGUP)
