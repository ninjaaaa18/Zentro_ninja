# Mandate Pay Backend

This is the FastAPI backend for Mandate Pay's payment integration and transaction
audit module. The current endpoints are placeholders: orders are stored in memory,
and no PayPal requests or real payment processing take place.

## Requirements

- Python 3.10 or newer
- The project virtual environment at `backend\venv\`

## Install and run (PowerShell)

From the project root:

```powershell
Set-Location .\backend
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API documentation is
available at `http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /health` — backend health check.
- `GET /payments/paypal/connection-test` — obtains a PayPal Sandbox OAuth token
  and returns only a safe connection status. The access token stays in the backend.
- `POST /payments/create-order` — creates an in-memory placeholder order. The
  request requires a positive amount and a three-letter uppercase currency code.
- `POST /payments/capture/{order_id}` — requires an `authorization_id` and asks
  the backend policy verifier to verify it. A frontend approval flag is neither
  accepted nor trusted. Until a policy engine is configured, this endpoint fails
  closed with `503`. Even after successful authorization, PayPal capture is
  unimplemented and returns `501`; the order is not marked as captured.
- `GET /payments/{order_id}` — fetches an in-memory order or returns `404`.

The default policy verifier deliberately reports itself as unconfigured. Wire a
trusted backend-to-backend Mandate Pay policy engine verifier before enabling
capture. Do not replace it with a client-supplied approval flag. PayPal integration
also requires a separately configured provider implementation; no credentials
are included in this project.

Set `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` in `backend\.env` before
calling the connection-test endpoint. The sandbox API base URL is
`https://api-m.sandbox.paypal.com`. Never commit `.env` or expose its values.

## Run tests

```powershell
Set-Location .\backend
.\venv\Scripts\Activate.ps1
python -m pytest
```
