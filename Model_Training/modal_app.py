"""Phase 4: serve the trained adapter behind a Modal web endpoint (GPU fallback).

Deploys ./lora_adapter on a Modal T4/A10G with the same 10-label head; the
backend talks to it via MODAL_ENDPOINT (see backend/app/services/lora_classifier.py
_query_modal) — switching providers is config-only (LORA_PROVIDER=modal).

Setup (Modal account needed):
    pip install modal && python -m modal setup
    modal volume create lora-adapter
    modal volume put lora-adapter ./lora_adapter /      # uploads adapter files
    modal deploy modal_app.py   # prints the https endpoint -> MODAL_ENDPOINT
    # Auth: create a shared secret and attach it (see secrets=[...] below):
    #   modal secret create lora-api-key MODAL_API_KEY=<long-random-string>
    # then set the SAME value as backend MODAL_API_KEY in .env / Render env.

Prompt template MUST match training (### Human: ... ### Assistant:) — see
backend/app/services/lora_classifier.py::build_prompt, duplicated here so
the Modal image stays dependency-free.
"""
import os

import fastapi
import modal

IMG = modal.Image.debian_slim().pip_install(
    "torch", "transformers", "peft", "accelerate", "fastapi"
)
ADAPTER_VOL = modal.Volume.from_name("lora-adapter", create_if_missing=True)
BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
LABELS_10 = ["Education", "Agriculture", "Healthcare", "Water Resources", "Environment",
             "Energy", "Urban Development", "Accessibility", "Public Administration",
             "Rural Livelihoods"]
# Must equal lora_classifier.build_prompt(); duplicated to keep image lean.
TEMPLATE = "### Human: Categorize this societal challenge: {text} ### Assistant:"

app = modal.App("lora-classify", image=IMG)


@app.cls(gpu="T4", volumes={"/adapter": ADAPTER_VOL})
class Classifier:
    @modal.enter()
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        self.tok = AutoTokenizer.from_pretrained(BASE_MODEL)
        # fp16: full fp32 Mistral-7B (~28GB) OOMs a 16GB T4; fp16 is ~14GB.
        # If still tight, switch gpu="A10G" or add load_in_8bit=True (bitsandbytes).
        base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16)
        self.model = PeftModel.from_pretrained(base, "/adapter")

    @modal.method()
    def label(self, text: str) -> str:
        prompt = TEMPLATE.format(text=(text or "").strip())
        ids = self.tok(prompt, return_tensors="pt").input_ids
        out = self.model.generate(ids, max_new_tokens=10, do_sample=False)
        gen = self.tok.decode(out[0][ids.shape[1]:])
        for lab in LABELS_10:
            if lab.lower() in gen.lower():
                return lab
        return gen.strip()


@app.function(secrets=[modal.Secret.from_name("lora-api-key")])
@modal.fastapi_endpoint(method="POST")
async def classify(request: fastapi.Request):
    expected = os.environ.get("MODAL_API_KEY", "")
    if expected and request.headers.get("authorization") != f"Bearer {expected}":
        return fastapi.responses.JSONResponse({"detail": "unauthorized"}, status_code=401)
    item = await request.json()
    if not isinstance(item, dict):
        return fastapi.responses.JSONResponse({"detail": "expected JSON object"}, status_code=400)
    return {"label": Classifier().label.remote(item.get("text", ""))}
