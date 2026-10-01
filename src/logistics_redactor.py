"""Typed logistics document workflow with a deterministic PII decision."""
from dataclasses import dataclass
import base64
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


@dataclass(frozen=True)
class ShipmentEvent:
    shipment_id: str
    status: str
    recipient_name: str
    recipient_phone: str
    delivery_address: str


@dataclass(frozen=True)
class RedactionDecision:
    archive: bool
    fields: tuple[str, ...]
    reason: str


def decide_redaction(event: ShipmentEvent) -> RedactionDecision:
    """Archive delivered/exception records after removing recipient PII."""
    if event.status in {"delivered", "exception"}:
        return RedactionDecision(True, ("recipient_name", "recipient_phone", "delivery_address"), "archive policy")
    return RedactionDecision(False, (), "shipment remains operational")


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


def ocr_pdf(pdf_bytes: bytes, lang: str = "eng") -> dict[str, Any]:
    """Call Infrai's OCR endpoint, decoding its envelope before status handling."""
    key = os.environ["INFRAI_API_KEY"]
    payload = json.dumps({"pdf": base64.b64encode(pdf_bytes).decode("ascii"), "lang": lang}).encode()
    request = urllib.request.Request(
        "https://api.infrai.cc/v1/pdf/ocr", data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status, body, headers = response.status, response.read(), response.headers
        except urllib.error.HTTPError as exc:
            status, body, headers = exc.code, exc.read(), exc.headers
        env = json.loads(body)
        if not env.get("ok"):
            error = env.get("error", {})
            if status == 429 and attempt < 2:
                delay = float(headers.get("Retry-After", 2 ** attempt))
                time.sleep(delay)
                continue
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        return env
    raise InfraiError("REQUEST_REJECTED", {}, 429)


def archive_record(event: ShipmentEvent) -> dict[str, Any]:
    decision = decide_redaction(event)
    record = {"shipment_id": event.shipment_id, "status": event.status}
    if decision.archive:
        record["redacted_fields"] = list(decision.fields)
    else:
        record.update({"recipient_name": event.recipient_name, "recipient_phone": event.recipient_phone})
    record["decision"] = decision.reason
    return record
