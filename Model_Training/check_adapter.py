"""Phase 0 gate: validate a trained adapter dir BEFORE upload.

Checks (per Cloudflare docs):
1. Exact filenames: adapter_model.safetensors + adapter_config.json
2. adapter_config.json has "model_type" in {mistral, gemma, llama}
3. LoRA rank <= 32 (from config["r"], else inferred from safetensor shapes)
4. Combined size < 300MB
Usage: python check_adapter.py --dir ./lora_adapter
"""
import argparse
import json
import os
import struct

LIMIT_MB = 300


def read_rank(cfg: dict, d: str):
    if isinstance(cfg.get("r"), int):
        return cfg["r"]
    # Fallback: infer from safetensor header (lora_A.<layer>.weight shape [r, in])
    try:
        with open(os.path.join(d, "adapter_model.safetensors"), "rb") as f:
            (n,) = struct.unpack("<Q", f.read(8))
            header = json.loads(f.read(n))
        for name, meta in header.items():
            if name.endswith("lora_A.weight"):
                return meta["shape"][0]
    except Exception:
        return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="./lora_adapter")
    a = ap.parse_args()
    errs = []
    for fn in ("adapter_model.safetensors", "adapter_config.json"):
        if not os.path.isfile(os.path.join(a.dir, fn)):
            errs.append(f"missing {fn}")
    if errs:
        print("FAIL:", "; ".join(errs))
        raise SystemExit(1)
    cfg = json.load(open(os.path.join(a.dir, "adapter_config.json")))
    if cfg.get("model_type") not in ("mistral", "gemma", "llama"):
        errs.append(f"model_type must be mistral|gemma|llama, got {cfg.get('model_type')!r}")
    rank = read_rank(cfg, a.dir)
    if rank is None:
        errs.append("could not determine rank")
    elif rank > 32:
        errs.append(f"rank {rank} > 32")
    mb = sum(os.path.getsize(os.path.join(a.dir, f)) for f in
             ("adapter_model.safetensors", "adapter_config.json")) / 1e6
    if mb >= LIMIT_MB:
        errs.append(f"size {mb:.1f}MB >= {LIMIT_MB}MB")
    if errs:
        print("FAIL:", "; ".join(errs))
        raise SystemExit(1)
    print(f"PASS rank={rank} model_type={cfg['model_type']} size={mb:.1f}MB — ready for Phase 1 upload")


if __name__ == "__main__":
    main()
