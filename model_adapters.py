#!/usr/bin/env python3
"""Explicit model-family adapters for reproducible image-text generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


@dataclass
class LoadedAdapter:
    model: Any
    processor: Any
    device: Any
    dtype: Any
    adapter_type: str

    def _move(self, inputs: Any) -> Any:
        moved = {}
        for key, value in inputs.items():
            if not hasattr(value, "to"):
                moved[key] = value
            elif self.adapter_type == "phi35" and self.device.type == "mps" and key == "image_sizes":
                # Phi's remote HD transform uses crop sizes as Python shape
                # values. Keeping this integer metadata on CPU avoids MPS
                # placeholder-storage errors; model tensors still run on MPS.
                moved[key] = value.to("cpu")
            elif hasattr(value, "is_floating_point") and value.is_floating_point():
                moved[key] = value.to(device=self.device, dtype=self.dtype)
            else:
                moved[key] = value.to(self.device)
        return moved

    def generate(self, image_path: str, prompt: str, max_new_tokens: int, sample: bool) -> str:
        image = Image.open(image_path).convert("RGB")
        if self.adapter_type == "phi35":
            text = f"<|user|>\n<|image_1|>\n{prompt}<|end|>\n<|assistant|>\n"
            inputs = self.processor(text, [image], return_tensors="pt")
        else:
            messages = [{"role": "user", "content": [
                {"type": "image", "url": image_path},
                {"type": "text", "text": prompt},
            ]}]
            try:
                inputs = self.processor.apply_chat_template(
                    messages, add_generation_prompt=True, tokenize=True,
                    return_dict=True, return_tensors="pt"
                )
            except (TypeError, ValueError):
                formatted = self.processor.apply_chat_template(messages, add_generation_prompt=True)
                inputs = self.processor(text=[formatted], images=[image], return_tensors="pt")
        inputs = self._move(inputs)
        input_length = inputs["input_ids"].shape[1]
        kwargs = {"max_new_tokens": max_new_tokens, "do_sample": sample}
        if sample:
            kwargs.update({"temperature": 0.2, "top_p": 0.9})
        output = self.model.generate(**inputs, **kwargs)
        return self.processor.batch_decode(output[:, input_length:], skip_special_tokens=True)[0].strip()


def resolve_device(torch: Any, requested: str) -> Any:
    if requested != "auto":
        if requested == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available in this environment")
        if requested == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("MPS was requested but is not available in this Python environment")
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _force_eager_attention(model_config: Any) -> Any:
    """Disable unsupported Flash Attention in remote Phi configuration objects."""
    model_config._attn_implementation = "eager"
    model_config._attn_implementation_internal = "eager"
    return model_config


def _require_phi_reference_runtime() -> None:
    """Reject cache-incompatible runtimes instead of silently patching Phi."""
    import torch
    import transformers

    if transformers.__version__ != "4.43.0" or not torch.__version__.startswith("2.3.0"):
        raise RuntimeError(
            "Phi-3.5-Vision requires the author-pinned runtime "
            "(transformers==4.43.0, torch==2.3.0). Run it through "
            "wacv_pipeline.py after `python wacv_pipeline.py setup-phi`."
        )


def load_adapter(
    config: dict[str, Any],
    device_name: str,
    dtype_name: str,
    phi_num_crops: int = 4,
) -> LoadedAdapter:
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoProcessor

    if config["adapter_type"] == "phi35":
        _require_phi_reference_runtime()

    device = resolve_device(torch, device_name)
    dtype_map = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}
    dtype = dtype_map.get(dtype_name, torch.float16 if device.type in {"cuda", "mps"} else torch.float32)
    trust = bool(config.get("trust_remote_code", False))
    processor_kwargs = {"trust_remote_code": trust}
    if config["adapter_type"] == "phi35":
        processor_kwargs["num_crops"] = phi_num_crops
    revision = config.get("revision")
    if revision:
        processor_kwargs["revision"] = revision
    processor = AutoProcessor.from_pretrained(config["model_id"], **processor_kwargs)
    model_kwargs = {
        "trust_remote_code": trust,
        "torch_dtype": dtype,
        "low_cpu_mem_usage": True,
    }
    if revision:
        model_kwargs["revision"] = revision
    if device.type == "cuda":
        model_kwargs["device_map"] = "auto"
    if config["adapter_type"] == "phi35":
        # Apple MPS does not support Phi's Flash Attention 2 path.
        phi_config_kwargs = {"trust_remote_code": trust}
        if revision:
            phi_config_kwargs["revision"] = revision
        phi_config = AutoConfig.from_pretrained(config["model_id"], **phi_config_kwargs)
        model_kwargs["config"] = _force_eager_attention(phi_config)
        model = AutoModelForCausalLM.from_pretrained(config["model_id"], **model_kwargs)
    else:
        from transformers import AutoModelForImageTextToText

        model = AutoModelForImageTextToText.from_pretrained(config["model_id"], **model_kwargs)
    if device.type != "cuda":
        model.to(device)
    model.eval()
    return LoadedAdapter(model, processor, device, dtype, config["adapter_type"])
