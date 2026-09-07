"""Phase 1: upload a validated adapter to Cloudflare (correct REST flow per docs).

Flow: POST /ai/finetunes {model, name, description}
   -> POST /ai/finetunes/{id}/finetune-assets/ multipart {file_name, file} x2
   -> GET /ai/finetunes (confirm)
Needs token with Workers AI Write. Creds from env only (never hardcode):
  PowerShell: $env:CLOUDFLARE_API_TOKEN="..."; $env:CLOUDFLARE_ACCOUNT_ID="..."
Usage: python deploy_lora.py --dir ./lora_adapter --name jharkhand-classifier
  (runs check_adapter.py gate first; wrangler equivalent:
   npx wrangler ai finetune create <model> <name> <folder>)
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

BASE_MODEL = "@cf/mistralai/mistral-7b-instruct-v0.2"


def _req(method: str, url: str, token: str, body=None, multipart=None):
    if multipart:
        import uuid
        b = uuid.uuid4().hex.encode()
        parts = b""
        for k, v in multipart["fields"].items():
            parts += b"--" + b + b"\r\n" + f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        fname, fpath = multipart["file_name"], multipart["file_path"]
        with open(fpath, "rb") as f:
            content = f.read()
        parts += (b"--" + b + b"\r\n" + f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode()
                  + b"Content-Type: application/octet-stream\r\n\r\n") + content + b"\r\n--" + b + b"--\r\n"
        req = urllib.request.Request(url, data=parts, method=method,
                                     headers={"Authorization": f"Bearer {token}",
                                              "Content-Type": f"multipart/form-data; boundary={b.decode()}"})
    else:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"Authorization": f"Bearer {token}",
                                              "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="./lora_adapter")
    ap.add_argument("--name", default="jharkhand-classifier")
    ap.add_argument("--model", default=BASE_MODEL)
    a = ap.parse_args()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not (token and acct):
        raise SystemExit("set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID env vars")
    gate = subprocess.run([sys.executable, "check_adapter.py", "--dir", a.dir])
    if gate.returncode != 0:
        raise SystemExit("adapter gate failed — train/fix first (Phase 0)")

    base = f"https://api.cloudflare.com/client/v4/accounts/{acct}"
    created = _req("POST", f"{base}/ai/finetunes", token,
                   {"model": a.model, "name": a.name,
                    "description": "SIH Jharkhand 10-label challenge classifier"})
    fid = created["result"]["id"]
    print(f"finetune id: {fid}")
    for fn in ("adapter_model.safetensors", "adapter_config.json"):
        r = _req("POST", f"{base}/ai/finetunes/{fid}/finetune-assets/", token,
                 multipart={"fields": {"file_name": fn},
                            "file_name": fn, "file_path": os.path.join(a.dir, fn)})
        print(f"{fn}: success={r.get('success')}")
    listed = _req("GET", f"{base}/ai/finetunes", token)
    names = [f.get("name") for grp in listed["result"] for f in (grp if isinstance(grp, list) else [grp])]
    print(f"confirmed on account: {a.name in names}")
    print(f"next: python probe_lora.py --finetune {a.name} (needs CLOUDFLARE_* env)")


if __name__ == "__main__":
    main()
