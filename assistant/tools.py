"""Asistanın 5 tool'u. Hepsi banka servisini çağırır, `call_id` closure ile bağlıdır.

LLM müşteri kimliğini, çağrı numarasını ya da kayıtlı doğum tarihini hiçbir zaman görmez
ve parametre olarak geçemez. Servis hataları LLM'e okunur Türkçe metin olarak döner.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import httpx
from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server, tool

SERVER_NAME = "bank"
TOOL_NAMES = ("confirm_identity_name", "verify_dob", "list_slots", "book_appointment", "close_call")
ALLOWED_TOOLS = [f"mcp__{SERVER_NAME}__{name}" for name in TOOL_NAMES]
OUTCOMES = ["booked", "no_slot", "declined", "not_verified"]

# on_tool(tool_name, args, status_code | None, body) — debug çıktısı ve eval tetikleyicileri için.
OnTool = Callable[[str, dict, "int | None", dict], "Awaitable[None] | None"]


# close_call sonrası modele dönen talimat: model close_call'ı metinsiz çağırırsa (ör. list_slots
# boş dönünce) müşteri yine de R7 cümlesini duyar. Aynı turda zaten söylendiyse metin atılır.
CLOSE_HINTS = {
    "no_slot": "Arama kapandı. Müşteriye son sözünü şimdi söyle: uygun yer olmadığını ya da "
               "seçilmediğini kısaca belirt, aynen \"Sizi gelecek hafta arayacağız\" de ve vedalaş. "
               "Başka tool çağırma.",
    "declined": "Arama kapandı. Müşteriye kararını not ettiğini ve teslimatın planlanmayacağını söyle, "
                "vedalaş. Başka tool çağırma.",
}


@dataclass
class CallState:
    call_id: int
    closed: bool = False
    outcome: str | None = None


def _text(body: Any, is_error: bool = False) -> dict[str, Any]:
    text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["is_error"] = True
    return result


def build_tools(state: CallState, http: httpx.AsyncClient,
                on_tool: OnTool | None = None) -> list[SdkMcpTool]:
    base = f"/calls/{state.call_id}"

    async def call_service(name: str, args: dict, method: str, path: str,
                           payload: dict | None = None) -> tuple[int | None, dict]:
        try:
            resp = await http.request(method, base + path, json=payload)
            status, body = resp.status_code, resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            status, body = None, {"error": "service_unreachable", "message": str(exc)}
        if on_tool is not None:
            res = on_tool(name, args, status, body)
            if inspect.isawaitable(res):
                await res
        return status, body

    def to_result(status: int | None, body: dict) -> dict[str, Any]:
        if status is None:
            return _text("HATA: Banka servisine ulaşılamadı. Müşteriye teknik bir sorun olduğunu, "
                         "daha sonra tekrar aranacağını söyle.", is_error=True)
        if status >= 400:
            return _text(f"HATA {status} {body.get('error', '')}: {body.get('message', '')}".strip(),
                         is_error=True)
        return _text(body)

    @tool(
        "confirm_identity_name",
        "Telefonu açan kişinin müşterinin kendisi olup olmadığını bankaya bildirir. Açılışta "
        "'Ad Soyad ile mi görüşüyorum?' sorusuna cevap gelince çağır. Kişi müşteri değilse "
        "is_customer=false gönder.",
        {
            "type": "object",
            "properties": {
                "is_customer": {"type": "boolean",
                                "description": "Telefonu açan kişi müşterinin kendisi mi"},
            },
            "required": ["is_customer"],
        },
    )
    async def confirm_identity_name(args: dict) -> dict:
        payload = {"is_customer": bool(args["is_customer"])}
        return to_result(*await call_service("confirm_identity_name", args, "POST",
                                             "/confirm-name", payload))

    @tool(
        "verify_dob",
        "Müşterinin söylediği doğum tarihini bankaya doğrulatır. Kontrolü banka yapar; doğru "
        "tarihi sen bilmezsin. Tarihi GG.AA.YYYY biçimine çevir (ör. '14 Mart 1988' -> "
        "'14.03.1988'). Yıl iki haneli söylendiyse çağırma, dört haneli yılı sor. Yalnız "
        "confirm_identity_name müşteri olduğunu doğruladıktan sonra çağır.",
        {
            "type": "object",
            "properties": {
                "spoken_date": {"type": "string",
                                "description": "Müşterinin söylediği tarih, GG.AA.YYYY biçiminde"},
            },
            "required": ["spoken_date"],
        },
    )
    async def verify_dob(args: dict) -> dict:
        payload = {"dob": str(args["spoken_date"])}
        return to_result(*await call_service("verify_dob", args, "POST", "/verify", payload))

    @tool(
        "list_slots",
        "Müşterinin ilçesindeki bu haftanın boş kurye teslimat yerlerini getirir. Yalnız kimlik "
        "doğrulandıktan sonra çağır. Müşteriye yalnız buradan dönen yerleri öner.",
        {"type": "object", "properties": {}},
    )
    async def list_slots(args: dict) -> dict:
        return to_result(*await call_service("list_slots", args, "GET", "/slots"))

    @tool(
        "book_appointment",
        "Seçilen yere teslimat randevusu yazar. Yalnız seçilen yeri (gün, saat aralığı, Ev/İş yeri) "
        "müşteriye tekrar okuyup açık onay aldıktan sonra çağır. slot_id list_slots sonucundan gelir.",
        {
            "type": "object",
            "properties": {
                "slot_id": {"type": "integer", "description": "list_slots sonucundaki slot_id"},
            },
            "required": ["slot_id"],
        },
    )
    async def book_appointment(args: dict) -> dict:
        payload = {"slot_id": int(args["slot_id"])}
        status, body = await call_service("book_appointment", args, "POST", "/appointments", payload)
        if status == 201:
            body = {**body, "next": "Randevuyu teyit et, kartın yalnız kart sahibine kimlikle teslim "
                                    "edileceğini hatırlat ve başka sorusu olup olmadığını sor. "
                                    "close_call'u bu turda çağırma."}
        return to_result(status, body)

    @tool(
        "close_call",
        "Aramayı sonuçla kapatır. Her arama bununla biter. Vedalaştığın turda çağır. "
        "booked: randevu yazıldı. no_slot: uygun yer yok ya da müşteri hiçbirini seçmedi. "
        "declined: doğrulanmış müşteri teslimatı tümden istemedi. not_verified: telefonu başkası "
        "açtı ya da doğum tarihi doğrulanamadı.",
        {
            "type": "object",
            "properties": {
                "outcome": {"type": "string", "enum": OUTCOMES, "description": "Arama sonucu"},
                "note": {"type": "string", "description": "Kısa açıklama (isteğe bağlı)"},
            },
            "required": ["outcome"],
        },
    )
    async def close_call(args: dict) -> dict:
        payload = {"outcome": args["outcome"], "note": args.get("note") or ""}
        status, body = await call_service("close_call", args, "POST", "/close", payload)
        if status == 200:
            state.closed = True
            state.outcome = body.get("outcome")
            hint = CLOSE_HINTS.get(state.outcome)
            if hint:    # bu turda henüz bir şey söylenmediyse müşteri son sözü buradan duyar
                body = {**body, "next": hint}
        return to_result(status, body)

    return [confirm_identity_name, verify_dob, list_slots, book_appointment, close_call]


def build_bank_server(state: CallState, http: httpx.AsyncClient, on_tool: OnTool | None = None):
    return create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0",
                                 tools=build_tools(state, http, on_tool))
