"""Girdi ve çıktıdan bağımsız arama döngüsü. CLI, ses ve eval aynı sınıfı kullanır.

    async with CallSession(customer_id) as s:
        print(await s.start())
        while not s.done:
            print(await s.send(input()))
"""

from __future__ import annotations

import shutil
import tempfile
import time
import warnings
from dataclasses import dataclass, field

import httpx
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

from . import config
from .prompt import build_system_prompt
from .tools import ALLOWED_TOOLS, SERVER_NAME, CallState, OnTool, build_bank_server

OPENING_NOTE = "[SİSTEM] Arama bağlandı, telefon açıldı. Açılış cümleni söyle."
HANGUP_NOTE = "[SİSTEM] Müşteri telefonu kapattı. Duruma uyan sonuçla hemen close_call çağır."
TIMEOUT_NOTE = ("[SİSTEM] Görüşme süresi doldu. Müşteriye kısaca vedalaş ve duruma uyan sonuçla "
                "close_call çağır.")
MAX_AGENT_TURNS = 10        # tek müşteri turunda ajan döngüsünün sınırı
MAX_CUSTOMER_TURNS = 20     # bir aramadaki müşteri turu sınırı


class CallFinishedError(RuntimeError):
    """Kapanmış aramaya mesaj gönderildi."""


@dataclass
class TurnStat:
    llm_s: float
    agent_turns: int
    cost_usd: float | None
    tools: list[str] = field(default_factory=list)


def build_options(customer_name: str, server, *, cwd: str, model: str | None = None,
                  effort: str | None = None) -> ClaudeAgentOptions:
    """Yalnız 5 banka tool'u olan, dosya sistemi ayarlarını yüklemeyen ajan ayarları."""
    return ClaudeAgentOptions(
        system_prompt=build_system_prompt(customer_name),
        model=model or config.MODEL,
        effort=effort or config.EFFORT,
        tools=[],                                   # yerleşik tool yok
        mcp_servers={SERVER_NAME: server},
        strict_mcp_config=True,                     # kullanıcının başka MCP sunucuları yüklenmez
        allowed_tools=list(ALLOWED_TOOLS),
        permission_mode="dontAsk",                  # ön onaylı olmayan her çağrı reddedilir
        setting_sources=[],                         # CLAUDE.md ve ayar dosyaları yüklenmez
        env={"ENABLE_TOOL_SEARCH": "false"},        # 5 tool baştan yüklenir, ToolSearch yok
        max_turns=MAX_AGENT_TURNS,
        cwd=cwd,                                    # boş geçici klasör: repo bağlama girmez
    )


class CallSession:
    def __init__(self, customer_id: int, *, http: httpx.AsyncClient | None = None,
                 on_tool: OnTool | None = None, model: str | None = None,
                 effort: str | None = None, max_customer_turns: int = MAX_CUSTOMER_TURNS):
        self.customer_id = customer_id
        self._http = http
        self._own_http = http is None
        self._on_tool = on_tool
        self._model = model
        self._effort = effort
        self.max_customer_turns = max_customer_turns

        self.call_id: int | None = None
        self.customer_name: str | None = None
        self.state: CallState | None = None
        self.customer_turns = 0
        self.turn_stats: list[TurnStat] = []
        self.violations: list[str] = []
        self.events: list[tuple[int, str, str]] = []   # (tur, blok tipi, metin ya da tool adı)
        self.init_tools: list[str] | None = None       # CLI'ın modele sunduğu tool listesi
        self.gave_up = False
        self._client: ClaudeSDKClient | None = None
        self._cwd: str | None = None

    # ---------- durum ----------

    @property
    def closed(self) -> bool:
        return bool(self.state and self.state.closed)

    @property
    def outcome(self) -> str | None:
        return self.state.outcome if self.state else None

    @property
    def done(self) -> bool:
        return self.closed or self.gave_up

    # ---------- yaşam döngüsü ----------

    async def __aenter__(self) -> "CallSession":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._client is not None:
            client, self._client = self._client, None
            await client.disconnect()
        if self._own_http and self._http is not None:
            await self._http.aclose()
            self._http = None
        if self._cwd:
            shutil.rmtree(self._cwd, ignore_errors=True)
            self._cwd = None

    async def start(self) -> str:
        """Çağrıyı serviste açar, ajanı bağlar ve açılış cümlesini döner."""
        if self._http is None:
            self._http = httpx.AsyncClient(base_url=config.BANK_URL, timeout=15)
        resp = await self._http.post("/calls", json={"customer_id": self.customer_id})
        resp.raise_for_status()
        data = resp.json()
        self.call_id, self.customer_name = data["call_id"], data["customer_name"]
        self.state = CallState(call_id=self.call_id)

        server = build_bank_server(self.state, self._http, self._on_tool)
        self._cwd = tempfile.mkdtemp(prefix="freya-call-")
        options = build_options(self.customer_name, server, cwd=self._cwd,
                                model=self._model, effort=self._effort)
        self._client = ClaudeSDKClient(options=options)
        await self._client.connect()
        return await self._turn(OPENING_NOTE)

    async def send(self, customer_text: str) -> str:
        """Müşterinin sözünü iletir, asistanın cevabını döner."""
        if self.done:
            raise CallFinishedError("Arama bitti.")
        self.customer_turns += 1
        await self._transcript("customer", customer_text)
        reply = await self._turn(customer_text)
        if not self.done and self.customer_turns >= self.max_customer_turns:
            extra = await self._system(TIMEOUT_NOTE)
            reply = " ".join(p for p in (reply, extra) if p)
        return reply

    async def hangup(self) -> str:
        """Müşteri kapattı: asistana bir kez close_call fırsatı verilir."""
        if self.done:
            return ""
        return await self._system(HANGUP_NOTE)

    # ---------- iç ----------

    async def _system(self, note: str) -> str:
        reply = await self._turn(note)
        if not self.closed:
            self.gave_up = True
            warnings.warn(f"Çağrı {self.call_id} close_call olmadan bitti; servise sonuç yazılmadı.")
        return reply

    async def _turn(self, prompt: str) -> str:
        assert self._client is not None
        started = time.perf_counter()
        await self._client.query(prompt)
        texts: list[str] = []
        stat = TurnStat(llm_s=0.0, agent_turns=0, cost_usd=None)
        async for msg in self._client.receive_response():
            if isinstance(msg, SystemMessage) and msg.subtype == "init":
                self.init_tools = list(msg.data.get("tools", []))
                extra = sorted(set(self.init_tools) - set(ALLOWED_TOOLS))
                if extra:
                    self.violations.append(f"init tool listesinde fazladan tool: {extra}")
            elif isinstance(msg, AssistantMessage):
                for block in msg.content:
                    self.events.append((len(self.turn_stats), type(block).__name__,
                                        getattr(block, "text", None) or getattr(block, "name", "")))
                    if isinstance(block, TextBlock) and block.text.strip():
                        # close_call'dan sonra gelen metin yalnız bu turda henüz bir şey
                        # söylenmediyse (veda) alınır; böylece tek veda kalır.
                        if not (self.closed and texts):
                            texts.append(block.text.strip())
                    elif isinstance(block, ToolUseBlock):
                        stat.tools.append(block.name)
                        if block.name not in ALLOWED_TOOLS:
                            self.violations.append(f"izinsiz tool çağrısı: {block.name}")
            elif isinstance(msg, ResultMessage):
                stat.agent_turns = msg.num_turns
                stat.cost_usd = msg.total_cost_usd
                if msg.is_error:
                    self.violations.append(f"ajan hatası: {msg.subtype} {msg.errors or ''}")
        stat.llm_s = time.perf_counter() - started
        self.turn_stats.append(stat)
        reply = " ".join(texts)
        if reply:
            await self._transcript("assistant", reply)
        return reply

    async def _transcript(self, role: str, text: str) -> None:
        try:
            await self._http.post(f"/calls/{self.call_id}/transcript", json={"role": role, "text": text})
        except httpx.HTTPError as exc:
            warnings.warn(f"Transkript yazılamadı: {exc}")
