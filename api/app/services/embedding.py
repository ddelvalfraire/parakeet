import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Computes and caches text embeddings using sentence-transformers.

    Singleton — initialized once at startup, model loaded lazily on first encode() call.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode(self, text: str) -> bytes:
        """Encode text into an embedding vector, returned as bytes (numpy float32 tobytes()).
        Loads the model lazily on first call."""
        model = self._load_model()
        embedding = model.encode(text)
        return np.asarray(embedding).astype(np.float32).tobytes()

    def cosine_similarity(self, a: bytes, b: bytes) -> float:
        """Compute cosine similarity between two embeddings stored as bytes.
        Returns float between -1.0 and 1.0."""
        vec_a = np.frombuffer(a, dtype=np.float32)
        vec_b = np.frombuffer(b, dtype=np.float32)
        dot = np.dot(vec_a, vec_b)
        norm = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
        if norm < 1e-10:
            return 0.0
        return float(dot / norm)


_instance: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _instance
    if _instance is None:
        from app.config import settings
        _instance = EmbeddingService(model_name=settings.embedding_model)
    return _instance
