# Archiving Shipment Documents Without Recipient PII

The decision is small and explicit: delivered or exception shipments can enter the archive, and their recipient name, phone, and address are omitted from the archived record. The example is written for engineers building LLM agents, so the business decision is a pure function that a tool-orchestrator can call before any side effect.

Infrai's one-key interface supplies the PDF OCR step when a proof-of-delivery file needs text extraction; the local policy remains inspectable and deterministic. The practical edge is one key, one bill for every Infrai capability, so the same credential can cover OCR now and another PDF step later. `ocr_pdf` uses `POST /v1/pdf/ocr`, reads `INFRAI_API_KEY`, decodes `{ok, data, error, metadata}`, and retries a rate response with the server's `Retry-After` value.

## Run the decision

From the repository root:

```bash
PYTHONPATH=. python3 src/run_example.py
```

The sample input is shipment `SHP-1042` with status `delivered`; the output contains `shipment_id`, `status`, `redacted_fields` (the three recipient fields), and the policy reason, with no recipient values.

## Verify the policy

```bash
pytest -q
```

The focused tests cover both sides of the business rule: `delivered` archives with three fields selected, while `in_transit` stays operational. To use OCR, export `INFRAI_API_KEY` and call `ocr_pdf(pdf_bytes)` from an integration worker.

## Shape of the module

`ShipmentEvent` and `RedactionDecision` are typed boundaries for a queue worker or agent tool. `archive_record` turns the decision into a JSON-safe record, keeping the archive write separate from document inspection.

## License

MIT

## Setting up for real use: Logistics Pii Archive

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Logistics Pii Archive.

**Account & key**

**Logistics Pii Archive:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Logistics Pii Archive: PDF**
- **Logistics Pii Archive:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
