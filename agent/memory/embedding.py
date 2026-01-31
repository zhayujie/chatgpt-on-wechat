"""
Embedding providers for memory

Supports OpenAI and local embedding models
"""

from typing import List, Optional
from abc import ABC, abstractmethod
import hashlib
import json


class EmbeddingProvider(ABC):
    """Base class for embedding providers"""
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Get embedding dimensions"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize OpenAI embedding provider
        
        Args:
            model: Model name (text-embedding-3-small or text-embedding-3-large)
            api_key: OpenAI API key
            api_base: Optional API base URL
        """
        self.model = model
        self.api_key = api_key
        self.api_base = api_base or "https://api.openai.com/v1"
        
        # Lazy import to avoid dependency issues
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=api_base)
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        # Set dimensions based on model
        self._dimensions = 1536 if "small" in model else 3072
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [item.embedding for item in response.data]
    
    @property
    def dimensions(self) -> int:
        return self._dimensions


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers"""
    
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding provider
        
        Args:
            model: Model name from sentence-transformers
        """
        self.model_name = model
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model)
            self._dimensions = self.model.get_sentence_embedding_dimension()
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    @property
    def dimensions(self) -> int:
        return self._dimensions


class EmbeddingCache:
    """Cache for embeddings to avoid recomputation"""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, text: str, provider: str, model: str) -> Optional[List[float]]:
        """Get cached embedding"""
        key = self._compute_key(text, provider, model)
        return self.cache.get(key)
    
    def put(self, text: str, provider: str, model: str, embedding: List[float]):
        """Cache embedding"""
        key = self._compute_key(text, provider, model)
        self.cache[key] = embedding
    
    @staticmethod
    def _compute_key(text: str, provider: str, model: str) -> str:
        """Compute cache key"""
        content = f"{provider}:{model}:{text}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()


def create_embedding_provider(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None
) -> EmbeddingProvider:
    """
    Factory function to create embedding provider
    
    Args:
        provider: Provider name ("openai" or "local")
        model: Model name (provider-specific)
        api_key: API key for remote providers
        api_base: API base URL for remote providers
        
    Returns:
        EmbeddingProvider instance
    """
    if provider == "openai":
        model = model or "text-embedding-3-small"
        return OpenAIEmbeddingProvider(model=model, api_key=api_key, api_base=api_base)
    elif provider == "local":
        model = model or "all-MiniLM-L6-v2"
        return LocalEmbeddingProvider(model=model)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
