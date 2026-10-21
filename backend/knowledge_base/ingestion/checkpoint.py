from __future__ import annotations

import json
from pathlib import Path

import numpy as np


class EmbeddingCheckpoint:
    """
    Stores partially generated embeddings so ingestion can resume
    after interruption or API quota exhaustion.
    """

    def __init__(self, index_dir: Path, domain: str):

        self.progress_path = index_dir / f"{domain}.progress.json"
        self.vector_path = index_dir / f"{domain}.partial_vectors.npy"

    def exists(self) -> bool:

        return (
            self.progress_path.exists()
            and self.vector_path.exists()
        )

    def load(self):
    
        vectors = np.load(
            self.vector_path,
            allow_pickle=False,
        ).tolist()

        with open(
            self.progress_path,
            "r",
            encoding="utf-8",
        ) as f:
            progress = json.load(f)

        return (
            vectors,
            progress["completed"],
        )

    

    def save(
        self,
        vectors,
    ):

        self.vector_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        np.save(
            self.vector_path,
            np.asarray(
                vectors,
                dtype=np.float32,
            ),
        )

        with open(
            self.progress_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                {
                    "completed": len(vectors),
                },
                f,
                indent=2,
            )

    def clear(self):

        for file in (
            self.progress_path,
            self.vector_path,
        ):

            if file.exists():
                file.unlink()