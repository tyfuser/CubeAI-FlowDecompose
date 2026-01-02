"""
FAISS Vector Database Service for the Video Shooting Assistant.

Provides vector similarity search for reference video retrieval.
"""
import json
import logging
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

logger = logging.getLogger(__name__)


@dataclass
class VectorDBConfig:
    """Configuration for the vector database."""
    dimension: int = 2048  # Default embedding dimension (ResNet50)
    index_type: str = "flat"  # "flat" for exact search, "ivf" for approximate
    nlist: int = 100  # Number of clusters for IVF index
    nprobe: int = 10  # Number of clusters to search
    index_path: Optional[str] = None  # Path to save/load index
    metadata_path: Optional[str] = None  # Path to save/load metadata


@dataclass
class VideoMetadata:
    """Metadata associated with a video embedding."""
    video_id: str
    video_path: str
    motion_type: Optional[str] = None
    subject_type: Optional[str] = None
    thumbnail_url: Optional[str] = None
    annotation: Optional[str] = None
    extra: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "video_id": self.video_id,
            "video_path": self.video_path,
            "motion_type": self.motion_type,
            "subject_type": self.subject_type,
            "thumbnail_url": self.thumbnail_url,
            "annotation": self.annotation,
            "extra": self.extra,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "VideoMetadata":
        """Create from dictionary."""
        return cls(
            video_id=data["video_id"],
            video_path=data["video_path"],
            motion_type=data.get("motion_type"),
            subject_type=data.get("subject_type"),
            thumbnail_url=data.get("thumbnail_url"),
            annotation=data.get("annotation"),
            extra=data.get("extra", {}),
        )


@dataclass
class SearchResult:
    """Result from a similarity search."""
    video_id: str
    similarity_score: float
    metadata: VideoMetadata
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "video_id": self.video_id,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata.to_dict(),
        }


@dataclass
class RetrievalFilters:
    """Filters for similarity search."""
    motion_type: Optional[str] = None
    subject_type: Optional[str] = None
    min_similarity: float = 0.0
    
    def matches(self, metadata: VideoMetadata) -> bool:
        """Check if metadata matches the filters."""
        if self.motion_type and metadata.motion_type != self.motion_type:
            return False
        if self.subject_type and metadata.subject_type != self.subject_type:
            return False
        return True


class VectorDBError(Exception):
    """Base exception for vector database errors."""
    pass


class FAISSNotAvailableError(VectorDBError):
    """Raised when FAISS is not installed."""
    pass


class IndexNotInitializedError(VectorDBError):
    """Raised when trying to use an uninitialized index."""
    pass


class VectorDB:
    """
    FAISS-based vector database for video embedding storage and retrieval.
    
    Supports:
    - Adding video embeddings with metadata
    - Cosine similarity search
    - Filtering by motion_type and subject_type
    - Persistence (save/load index and metadata)
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the vector database.
        
        Args:
            config: Configuration for the vector database
        """
        if faiss is None:
            raise FAISSNotAvailableError(
                "FAISS is not installed. Install with: pip install faiss-cpu"
            )
        
        self.config = config or VectorDBConfig()
        self._index: Optional[faiss.Index] = None
        self._metadata: list[VideoMetadata] = []
        self._id_to_idx: dict[str, int] = {}
        
        # Initialize index
        self._init_index()
    
    def _init_index(self) -> None:
        """Initialize the FAISS index based on configuration."""
        dimension = self.config.dimension
        
        if self.config.index_type == "flat":
            # Exact search using inner product (for normalized vectors = cosine similarity)
            self._index = faiss.IndexFlatIP(dimension)
        elif self.config.index_type == "ivf":
            # Approximate search using IVF
            quantizer = faiss.IndexFlatIP(dimension)
            self._index = faiss.IndexIVFFlat(
                quantizer, dimension, self.config.nlist, faiss.METRIC_INNER_PRODUCT
            )
        else:
            raise VectorDBError(f"Unknown index type: {self.config.index_type}")
        
        logger.info(f"Initialized FAISS index: type={self.config.index_type}, dim={dimension}")

    
    @property
    def is_trained(self) -> bool:
        """Check if the index is trained (for IVF indexes)."""
        if self._index is None:
            return False
        return self._index.is_trained
    
    @property
    def size(self) -> int:
        """Return the number of vectors in the index."""
        if self._index is None:
            return 0
        return self._index.ntotal
    
    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """
        Normalize vectors for cosine similarity.
        
        Args:
            vectors: Input vectors of shape (n, dimension)
            
        Returns:
            Normalized vectors
        """
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms
    
    def train(self, vectors: np.ndarray) -> None:
        """
        Train the index (required for IVF indexes).
        
        Args:
            vectors: Training vectors of shape (n, dimension)
        """
        if self._index is None:
            raise IndexNotInitializedError("Index not initialized")
        
        if self.config.index_type == "flat":
            # Flat index doesn't need training
            return
        
        vectors = np.asarray(vectors, dtype=np.float32)
        vectors = self._normalize_vectors(vectors)
        
        logger.info(f"Training index with {len(vectors)} vectors")
        self._index.train(vectors)
        logger.info("Index training complete")
    
    def add(
        self,
        video_id: str,
        embedding: np.ndarray,
        metadata: VideoMetadata,
    ) -> int:
        """
        Add a video embedding to the index.
        
        Args:
            video_id: Unique identifier for the video
            embedding: Embedding vector of shape (dimension,)
            metadata: Associated metadata
            
        Returns:
            Index position of the added vector
        """
        if self._index is None:
            raise IndexNotInitializedError("Index not initialized")
        
        # Check if video already exists
        if video_id in self._id_to_idx:
            logger.warning(f"Video {video_id} already exists, skipping")
            return self._id_to_idx[video_id]
        
        # Prepare embedding
        embedding = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        
        if embedding.shape[1] != self.config.dimension:
            raise VectorDBError(
                f"Embedding dimension mismatch: expected {self.config.dimension}, "
                f"got {embedding.shape[1]}"
            )
        
        # Normalize for cosine similarity
        embedding = self._normalize_vectors(embedding)
        
        # Add to index
        idx = self._index.ntotal
        self._index.add(embedding)
        
        # Store metadata
        self._metadata.append(metadata)
        self._id_to_idx[video_id] = idx
        
        logger.debug(f"Added video {video_id} at index {idx}")
        return idx
    
    def add_batch(
        self,
        video_ids: list[str],
        embeddings: np.ndarray,
        metadata_list: list[VideoMetadata],
    ) -> list[int]:
        """
        Add multiple video embeddings to the index.
        
        Args:
            video_ids: List of unique identifiers
            embeddings: Embedding vectors of shape (n, dimension)
            metadata_list: List of associated metadata
            
        Returns:
            List of index positions
        """
        if len(video_ids) != len(embeddings) or len(video_ids) != len(metadata_list):
            raise VectorDBError("Mismatched lengths for video_ids, embeddings, and metadata")
        
        indices = []
        for video_id, embedding, metadata in zip(video_ids, embeddings, metadata_list):
            idx = self.add(video_id, embedding, metadata)
            indices.append(idx)
        
        return indices

    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[RetrievalFilters] = None,
    ) -> list[SearchResult]:
        """
        Search for similar videos using cosine similarity.
        
        Args:
            query_embedding: Query vector of shape (dimension,)
            top_k: Number of results to return
            filters: Optional filters for motion_type, subject_type
            
        Returns:
            List of SearchResult objects sorted by similarity (descending)
        """
        if self._index is None:
            raise IndexNotInitializedError("Index not initialized")
        
        if self._index.ntotal == 0:
            return []
        
        # Prepare query
        query = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        
        if query.shape[1] != self.config.dimension:
            raise VectorDBError(
                f"Query dimension mismatch: expected {self.config.dimension}, "
                f"got {query.shape[1]}"
            )
        
        # Normalize for cosine similarity
        query = self._normalize_vectors(query)
        
        # Set nprobe for IVF index
        if self.config.index_type == "ivf":
            self._index.nprobe = self.config.nprobe
        
        # Search more than top_k to account for filtering
        search_k = min(top_k * 3, self._index.ntotal) if filters else top_k
        
        # Perform search
        scores, indices = self._index.search(query, search_k)
        scores = scores[0]  # Remove batch dimension
        indices = indices[0]
        
        # Build results with filtering
        results = []
        min_similarity = filters.min_similarity if filters else 0.0
        
        for score, idx in zip(scores, indices):
            if idx < 0 or idx >= len(self._metadata):
                continue
            
            # Convert inner product to similarity score (already normalized, so IP = cosine)
            similarity = float(score)
            
            if similarity < min_similarity:
                continue
            
            metadata = self._metadata[idx]
            
            # Apply filters
            if filters and not filters.matches(metadata):
                continue
            
            results.append(SearchResult(
                video_id=metadata.video_id,
                similarity_score=similarity,
                metadata=metadata,
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def get_by_id(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Get metadata for a specific video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            VideoMetadata if found, None otherwise
        """
        idx = self._id_to_idx.get(video_id)
        if idx is None:
            return None
        return self._metadata[idx]
    
    def remove(self, video_id: str) -> bool:
        """
        Remove a video from the index.
        
        Note: FAISS doesn't support efficient removal, so this marks the entry
        as removed but doesn't actually remove it from the index.
        For production use, consider periodic index rebuilding.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if removed, False if not found
        """
        idx = self._id_to_idx.get(video_id)
        if idx is None:
            return False
        
        # Mark as removed by setting video_id to None
        self._metadata[idx] = VideoMetadata(
            video_id="__removed__",
            video_path="",
        )
        del self._id_to_idx[video_id]
        
        logger.debug(f"Marked video {video_id} as removed")
        return True

    
    def save(self, index_path: Optional[str] = None, metadata_path: Optional[str] = None) -> None:
        """
        Save the index and metadata to disk.
        
        Args:
            index_path: Path to save the FAISS index
            metadata_path: Path to save the metadata
        """
        if self._index is None:
            raise IndexNotInitializedError("Index not initialized")
        
        index_path = index_path or self.config.index_path
        metadata_path = metadata_path or self.config.metadata_path
        
        if not index_path or not metadata_path:
            raise VectorDBError("Index path and metadata path must be specified")
        
        # Create directories if needed
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self._index, index_path)
        logger.info(f"Saved FAISS index to {index_path}")
        
        # Save metadata
        metadata_data = {
            "metadata": [m.to_dict() for m in self._metadata],
            "id_to_idx": self._id_to_idx,
            "config": {
                "dimension": self.config.dimension,
                "index_type": self.config.index_type,
                "nlist": self.config.nlist,
                "nprobe": self.config.nprobe,
            }
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    
    def load(self, index_path: Optional[str] = None, metadata_path: Optional[str] = None) -> None:
        """
        Load the index and metadata from disk.
        
        Args:
            index_path: Path to load the FAISS index from
            metadata_path: Path to load the metadata from
        """
        index_path = index_path or self.config.index_path
        metadata_path = metadata_path or self.config.metadata_path
        
        if not index_path or not metadata_path:
            raise VectorDBError("Index path and metadata path must be specified")
        
        if not os.path.exists(index_path):
            raise VectorDBError(f"Index file not found: {index_path}")
        if not os.path.exists(metadata_path):
            raise VectorDBError(f"Metadata file not found: {metadata_path}")
        
        # Load FAISS index
        self._index = faiss.read_index(index_path)
        logger.info(f"Loaded FAISS index from {index_path}")
        
        # Load metadata
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_data = json.load(f)
        
        self._metadata = [VideoMetadata.from_dict(m) for m in metadata_data["metadata"]]
        self._id_to_idx = metadata_data["id_to_idx"]
        
        # Update config from saved data
        saved_config = metadata_data.get("config", {})
        self.config.dimension = saved_config.get("dimension", self.config.dimension)
        self.config.index_type = saved_config.get("index_type", self.config.index_type)
        self.config.nlist = saved_config.get("nlist", self.config.nlist)
        self.config.nprobe = saved_config.get("nprobe", self.config.nprobe)
        
        logger.info(f"Loaded {len(self._metadata)} video entries from {metadata_path}")
    
    def clear(self) -> None:
        """Clear all data from the index."""
        self._init_index()
        self._metadata = []
        self._id_to_idx = {}
        logger.info("Cleared vector database")
    
    def rebuild(self) -> None:
        """
        Rebuild the index, removing entries marked as deleted.
        
        This is useful for reclaiming space after many deletions.
        """
        if self._index is None:
            raise IndexNotInitializedError("Index not initialized")
        
        # Collect valid entries
        valid_entries = []
        for video_id, idx in list(self._id_to_idx.items()):
            metadata = self._metadata[idx]
            if metadata.video_id != "__removed__":
                # Get the embedding from the index
                embedding = self._index.reconstruct(idx)
                valid_entries.append((video_id, embedding, metadata))
        
        # Reinitialize
        self._init_index()
        self._metadata = []
        self._id_to_idx = {}
        
        # Re-add valid entries
        for video_id, embedding, metadata in valid_entries:
            self.add(video_id, embedding, metadata)
        
        logger.info(f"Rebuilt index with {len(valid_entries)} entries")


def create_vector_db(config: Optional[VectorDBConfig] = None) -> VectorDB:
    """
    Factory function to create a VectorDB instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        VectorDB instance
    """
    return VectorDB(config)
