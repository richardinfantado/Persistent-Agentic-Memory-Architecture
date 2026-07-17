"""Mem0 configuration for validation.

Local-only backends. No cloud dependencies. LLM extraction is bypassed
via `infer=False` on every add call, so the LLM api_key is never used.
"""

from __future__ import annotations

import os
import tempfile


def build_config(collection_name: str = "pamspec_validation") -> dict:
    # Chroma on Windows rejects ":memory:"; use a real per-collection temp dir.
    path = os.path.join(tempfile.gettempdir(), "pamspec-mem0-val", collection_name)
    os.makedirs(path, exist_ok=True)
    return {
        "llm": {
            # Never called in the validation flow (infer=False on every add),
            # but Mem0 requires an LLM section to instantiate.
            "provider": "openai",
            "config": {"api_key": "unused-infer-false", "model": "gpt-4o-mini"},
        },
        "embedder": {
            # Local SentenceTransformer; downloaded once, cached under
            # the user's HuggingFace cache dir. Deterministic.
            "provider": "huggingface",
            "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"},
        },
        "vector_store": {
            # Local Chroma; ephemeral per collection under system temp.
            "provider": "chroma",
            "config": {"collection_name": collection_name, "path": path},
        },
    }
