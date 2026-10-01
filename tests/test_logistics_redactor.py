import base64
import json
from unittest.mock import patch

from src.logistics_redactor import ShipmentEvent, decide_redaction, ocr_pdf


def test_delivered_event_is_archived_without_recipient_fields():
    event = ShipmentEvent("S1", "delivered", "A", "123", "Dock 4")
    decision = decide_redaction(event)
    assert decision.archive is True
    assert decision.fields == ("recipient_name", "recipient_phone", "delivery_address")


def test_in_transit_event_stays_operational():
    event = ShipmentEvent("S2", "in_transit", "A", "123", "Dock 4")
    assert decide_redaction(event).archive is False


def test_ocr_pdf_sends_base64_encoded_bytes(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    pdf = b"%PDF-1.4\n\x00\xff"

    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def read(self):
            return b'{"ok": true, "data": {}}'

    with patch("src.logistics_redactor.urllib.request.urlopen", return_value=Response()) as urlopen:
        assert ocr_pdf(pdf)["ok"] is True

    request = urlopen.call_args.args[0]
    assert json.loads(request.data) == {"pdf": base64.b64encode(pdf).decode("ascii"), "lang": "eng"}
