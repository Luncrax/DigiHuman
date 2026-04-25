"""
Custom Qwen3-TTS server for DigiHuman.
Run this inside WSL with the flash_env environment activated.
"""
import argparse
import base64
import io
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import soundfile as sf
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

LOGGER = logging.getLogger("qwen3_tts_wsl_server")
MODEL_CACHE: Dict[str, Any] = {}


def _load_qwen_modules(source_path: str):
    source_root = Path(source_path)
    if not source_root.exists():
        raise FileNotFoundError(f"Qwen3-TTS source path does not exist: {source_path}")

    source_str = str(source_root)
    if source_str not in sys.path:
        sys.path.insert(0, source_str)

    from qwen_tts import Qwen3TTSModel, VoiceClonePromptItem  # type: ignore

    return Qwen3TTSModel, VoiceClonePromptItem


class SynthesizeRequest(BaseModel):
    text: str
    mode: str = "base"
    model_path: str
    source_path: str
    language: str = "Auto"
    speaker: Optional[str] = None
    instruct: Optional[str] = None
    prompt_path: Optional[str] = None
    device: str = "cuda:0"
    dtype: str = "bfloat16"
    flash_attn: bool = True
    max_new_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    repetition_penalty: Optional[float] = None
    subtalker_top_k: Optional[int] = None
    subtalker_top_p: Optional[float] = None
    subtalker_temperature: Optional[float] = None


app = FastAPI(title="DigiHuman Qwen3-TTS Service")


def _dtype_from_str(s: str):
    normalized = (s or "").strip().lower()
    if normalized in ("bf16", "bfloat16"):
        return torch.bfloat16
    if normalized in ("fp16", "float16", "half"):
        return torch.float16
    if normalized in ("fp32", "float32"):
        return torch.float32
    raise ValueError(f"Unsupported dtype: {s}")


def _model_cache_key(model_path: str, device: str, dtype: str, flash_attn: bool) -> str:
    return f"{model_path}|{device}|{dtype}|{flash_attn}"


def _clear_model_cache():
    if not MODEL_CACHE:
        return

    for key, model in list(MODEL_CACHE.items()):
        try:
            del model
        except Exception:
            pass
        MODEL_CACHE.pop(key, None)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _get_model(req: SynthesizeRequest):
    cache_key = _model_cache_key(req.model_path, req.device, req.dtype, req.flash_attn)
    if cache_key in MODEL_CACHE:
        return MODEL_CACHE[cache_key]

    if MODEL_CACHE and cache_key not in MODEL_CACHE:
        LOGGER.info("Switching Qwen3-TTS model, clearing previous cache first")
        _clear_model_cache()

    Qwen3TTSModel, _ = _load_qwen_modules(req.source_path)
    model = Qwen3TTSModel.from_pretrained(
        req.model_path,
        device_map=req.device,
        dtype=_dtype_from_str(req.dtype),
        attn_implementation="flash_attention_2" if req.flash_attn else "eager",
    )
    MODEL_CACHE[cache_key] = model
    LOGGER.info("Loaded Qwen3-TTS model: %s", cache_key)
    return model


def _load_voice_prompt(prompt_path: str, source_path: str) -> List[Any]:
    _, VoiceClonePromptItem = _load_qwen_modules(source_path)

    try:
        payload = torch.load(prompt_path, map_location="cpu", weights_only=True)
    except TypeError:
        payload = torch.load(prompt_path, map_location="cpu")

    if not isinstance(payload, dict) or "items" not in payload or not isinstance(payload["items"], list):
        raise ValueError(f"Invalid voice prompt file: {prompt_path}")

    items = []
    for raw in payload["items"]:
        if not isinstance(raw, dict):
            raise ValueError("Invalid voice prompt item format")

        ref_code = raw.get("ref_code")
        if ref_code is not None and not torch.is_tensor(ref_code):
            ref_code = torch.tensor(ref_code)

        ref_spk_embedding = raw.get("ref_spk_embedding")
        if ref_spk_embedding is None:
            raise ValueError("Voice prompt item missing ref_spk_embedding")
        if not torch.is_tensor(ref_spk_embedding):
            ref_spk_embedding = torch.tensor(ref_spk_embedding)

        items.append(
            VoiceClonePromptItem(
                ref_code=ref_code,
                ref_spk_embedding=ref_spk_embedding,
                x_vector_only_mode=bool(raw.get("x_vector_only_mode", False)),
                icl_mode=bool(raw.get("icl_mode", not bool(raw.get("x_vector_only_mode", False)))),
                ref_text=raw.get("ref_text"),
            )
        )
    return items


def _wav_to_base64(wav, sample_rate: int) -> str:
    buffer = io.BytesIO()
    sf.write(buffer, wav, sample_rate, format="WAV")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _gen_kwargs(req: SynthesizeRequest) -> Dict[str, Any]:
    keys = (
        "max_new_tokens",
        "temperature",
        "top_k",
        "top_p",
        "repetition_penalty",
        "subtalker_top_k",
        "subtalker_top_p",
        "subtalker_temperature",
    )
    return {key: getattr(req, key) for key in keys if getattr(req, key) is not None}


@app.get("/health")
def health():
    return {"status": "ok", "loaded_models": list(MODEL_CACHE.keys())}


@app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    def _run_once():
        model = _get_model(req)
        kwargs = _gen_kwargs(req)

        if req.mode == "custom_voice":
            wavs, sample_rate = model.generate_custom_voice(
                text=req.text,
                speaker=req.speaker or "Vivian",
                language=req.language,
                instruct=req.instruct,
                **kwargs,
            )
        elif req.mode == "voice_design":
            wavs, sample_rate = model.generate_voice_design(
                text=req.text,
                instruct=req.instruct or "Speak naturally.",
                language=req.language,
                **kwargs,
            )
        else:
            voice_clone_prompt = None
            if req.prompt_path:
                voice_clone_prompt = _load_voice_prompt(req.prompt_path, req.source_path)

            wavs, sample_rate = model.generate_voice_clone(
                text=req.text,
                language=req.language,
                voice_clone_prompt=voice_clone_prompt,
                **kwargs,
            )

        if not wavs:
            raise ValueError("Qwen3-TTS returned no waveform")

        return {
            "audio_base64": _wav_to_base64(wavs[0], sample_rate),
            "sample_rate": sample_rate,
            "mode": req.mode,
            "model_type": getattr(model.model, "tts_model_type", "unknown"),
        }

    try:
        return _run_once()
    except Exception as exc:
        if "out of memory" in str(exc).lower():
            LOGGER.warning("CUDA OOM detected, clearing model cache and retrying once")
            _clear_model_cache()
            try:
                return _run_once()
            except Exception:
                LOGGER.exception("Retry after CUDA OOM also failed")
        LOGGER.exception("Failed to synthesize audio")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def main():
    parser = argparse.ArgumentParser(description="Run DigiHuman's custom Qwen3-TTS server inside WSL.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
