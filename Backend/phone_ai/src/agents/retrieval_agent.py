"""
Retrieval Agent for the Video Shooting Assistant.

Provides reference video retrieval using vector similarity search.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from src.models.data_types import RetrievalOutput, RetrievalResult
from src.services.vector_db import (
    VectorDB,
    VectorDBConfig,
    VideoMetadata,
    SearchResult,
    RetrievalFilters,
    create_vector_db,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievalAgentConfig:
    """Configuration for the Retrieval Agent."""
    dimension: int = 2048  # Embedding dimension
    index_type: str = "flat"  # FAISS index type
    default_top_k: int = 5  # Default number of results
    min_similarity: float = 0.3  # Minimum similarity threshold
    index_path: Optional[str] = None  # Path to FAISS index
    metadata_path: Optional[str] = None  # Path to metadata


class RetrievalAgent:
    """
    参考样片检索模块
    Reference video retrieval agent using vector similarity search.
    
    This agent provides:
    - Similarity search using frame-level embeddings
    - Filtering by motion_type and subject_type
    - Video indexing for building the reference library
    """
    
    def __init__(
        self,
        config: Optional[RetrievalAgentConfig] = None,
        vector_db: Optional[VectorDB] = None,
    ):
        """
        Initialize the Retrieval Agent.
        
        Args:
            config: Agent configuration
            vector_db: Optional pre-configured VectorDB instance
        """
        self.config = config or RetrievalAgentConfig()
        
        if vector_db is not None:
            self._vector_db = vector_db
        else:
            db_config = VectorDBConfig(
                dimension=self.config.dimension,
                index_type=self.config.index_type,
                index_path=self.config.index_path,
                metadata_path=self.config.metadata_path,
            )
            self._vector_db = create_vector_db(db_config)
        
        logger.info(f"Initialized RetrievalAgent with dimension={self.config.dimension}")

    
    @property
    def vector_db(self) -> VectorDB:
        """Get the underlying vector database."""
        return self._vector_db
    
    @property
    def index_size(self) -> int:
        """Get the number of indexed videos."""
        return self._vector_db.size
    
    async def search(
        self,
        query_embedding: np.ndarray,
        query_video_id: str,
        top_k: Optional[int] = None,
        motion_type: Optional[str] = None,
        subject_type: Optional[str] = None,
        min_similarity: Optional[float] = None,
    ) -> RetrievalOutput:
        """
        Search for similar reference videos.
        
        Args:
            query_embedding: Query vector (frame embedding or aggregated embedding)
            query_video_id: ID of the query video
            top_k: Number of results to return
            motion_type: Filter by motion type
            subject_type: Filter by subject type
            min_similarity: Minimum similarity threshold
            
        Returns:
            RetrievalOutput with search results
        """
        top_k = top_k or self.config.default_top_k
        min_similarity = min_similarity or self.config.min_similarity
        
        # Build filters
        filters = RetrievalFilters(
            motion_type=motion_type,
            subject_type=subject_type,
            min_similarity=min_similarity,
        )
        
        logger.info(
            f"Searching for similar videos: query={query_video_id}, "
            f"top_k={top_k}, motion_type={motion_type}, subject_type={subject_type}"
        )
        
        # Perform search
        search_results = self._vector_db.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )
        
        # Convert to RetrievalOutput format
        results = []
        for sr in search_results:
            # Skip if this is the query video itself
            if sr.video_id == query_video_id:
                continue
            
            results.append(RetrievalResult(
                ref_video_id=sr.video_id,
                thumbnail_url=sr.metadata.thumbnail_url or "",
                similarity_score=sr.similarity_score,
                annotation=sr.metadata.annotation,
            ))
        
        logger.info(f"Found {len(results)} similar videos")
        
        return RetrievalOutput(
            query_video_id=query_video_id,
            results=results,
        )
    
    async def search_by_aggregated_embedding(
        self,
        frame_embeddings: list[list[float]],
        query_video_id: str,
        top_k: Optional[int] = None,
        motion_type: Optional[str] = None,
        subject_type: Optional[str] = None,
        aggregation: str = "mean",
    ) -> RetrievalOutput:
        """
        Search using aggregated frame embeddings.
        
        Args:
            frame_embeddings: List of frame embedding vectors
            query_video_id: ID of the query video
            top_k: Number of results to return
            motion_type: Filter by motion type
            subject_type: Filter by subject type
            aggregation: Aggregation method ("mean", "max", "first", "last")
            
        Returns:
            RetrievalOutput with search results
        """
        if not frame_embeddings:
            logger.warning("No frame embeddings provided")
            return RetrievalOutput(query_video_id=query_video_id, results=[])
        
        embeddings = np.array(frame_embeddings, dtype=np.float32)
        
        # Aggregate embeddings
        if aggregation == "mean":
            query_embedding = np.mean(embeddings, axis=0)
        elif aggregation == "max":
            query_embedding = np.max(embeddings, axis=0)
        elif aggregation == "first":
            query_embedding = embeddings[0]
        elif aggregation == "last":
            query_embedding = embeddings[-1]
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
        
        return await self.search(
            query_embedding=query_embedding,
            query_video_id=query_video_id,
            top_k=top_k,
            motion_type=motion_type,
            subject_type=subject_type,
        )

    
    def index_video(
        self,
        video_id: str,
        video_path: str,
        embedding: np.ndarray,
        motion_type: Optional[str] = None,
        subject_type: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        annotation: Optional[str] = None,
        extra_metadata: Optional[dict] = None,
    ) -> int:
        """
        Index a video for future retrieval.
        
        Args:
            video_id: Unique identifier for the video
            video_path: Path to the video file
            embedding: Video embedding vector
            motion_type: Type of camera motion
            subject_type: Type of subject in the video
            thumbnail_url: URL to video thumbnail
            annotation: Optional annotation text
            extra_metadata: Additional metadata to store
            
        Returns:
            Index position of the added video
        """
        metadata = VideoMetadata(
            video_id=video_id,
            video_path=video_path,
            motion_type=motion_type,
            subject_type=subject_type,
            thumbnail_url=thumbnail_url,
            annotation=annotation,
            extra=extra_metadata or {},
        )
        
        idx = self._vector_db.add(video_id, embedding, metadata)
        logger.info(f"Indexed video {video_id} at position {idx}")
        
        return idx
    
    def index_video_from_frames(
        self,
        video_id: str,
        video_path: str,
        frame_embeddings: list[list[float]],
        motion_type: Optional[str] = None,
        subject_type: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        annotation: Optional[str] = None,
        aggregation: str = "mean",
        extra_metadata: Optional[dict] = None,
    ) -> int:
        """
        Index a video using aggregated frame embeddings.
        
        Args:
            video_id: Unique identifier for the video
            video_path: Path to the video file
            frame_embeddings: List of frame embedding vectors
            motion_type: Type of camera motion
            subject_type: Type of subject in the video
            thumbnail_url: URL to video thumbnail
            annotation: Optional annotation text
            aggregation: Aggregation method ("mean", "max", "first", "last")
            extra_metadata: Additional metadata to store
            
        Returns:
            Index position of the added video
        """
        if not frame_embeddings:
            raise ValueError("No frame embeddings provided")
        
        embeddings = np.array(frame_embeddings, dtype=np.float32)
        
        # Aggregate embeddings
        if aggregation == "mean":
            video_embedding = np.mean(embeddings, axis=0)
        elif aggregation == "max":
            video_embedding = np.max(embeddings, axis=0)
        elif aggregation == "first":
            video_embedding = embeddings[0]
        elif aggregation == "last":
            video_embedding = embeddings[-1]
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
        
        return self.index_video(
            video_id=video_id,
            video_path=video_path,
            embedding=video_embedding,
            motion_type=motion_type,
            subject_type=subject_type,
            thumbnail_url=thumbnail_url,
            annotation=annotation,
            extra_metadata=extra_metadata,
        )
    
    def index_batch(
        self,
        videos: list[dict],
        aggregation: str = "mean",
    ) -> list[int]:
        """
        Index multiple videos at once.
        
        Args:
            videos: List of video dictionaries with keys:
                - video_id: str
                - video_path: str
                - embedding: np.ndarray or frame_embeddings: list[list[float]]
                - motion_type: Optional[str]
                - subject_type: Optional[str]
                - thumbnail_url: Optional[str]
                - annotation: Optional[str]
                - extra_metadata: Optional[dict]
            aggregation: Aggregation method for frame embeddings
            
        Returns:
            List of index positions
        """
        indices = []
        
        for video in videos:
            video_id = video["video_id"]
            video_path = video["video_path"]
            
            if "embedding" in video:
                idx = self.index_video(
                    video_id=video_id,
                    video_path=video_path,
                    embedding=video["embedding"],
                    motion_type=video.get("motion_type"),
                    subject_type=video.get("subject_type"),
                    thumbnail_url=video.get("thumbnail_url"),
                    annotation=video.get("annotation"),
                    extra_metadata=video.get("extra_metadata"),
                )
            elif "frame_embeddings" in video:
                idx = self.index_video_from_frames(
                    video_id=video_id,
                    video_path=video_path,
                    frame_embeddings=video["frame_embeddings"],
                    motion_type=video.get("motion_type"),
                    subject_type=video.get("subject_type"),
                    thumbnail_url=video.get("thumbnail_url"),
                    annotation=video.get("annotation"),
                    aggregation=aggregation,
                    extra_metadata=video.get("extra_metadata"),
                )
            else:
                raise ValueError(f"Video {video_id} must have 'embedding' or 'frame_embeddings'")
            
            indices.append(idx)
        
        logger.info(f"Indexed {len(indices)} videos")
        return indices
    
    def remove_video(self, video_id: str) -> bool:
        """
        Remove a video from the index.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if removed, False if not found
        """
        result = self._vector_db.remove(video_id)
        if result:
            logger.info(f"Removed video {video_id} from index")
        else:
            logger.warning(f"Video {video_id} not found in index")
        return result
    
    def get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Get metadata for a specific video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            VideoMetadata if found, None otherwise
        """
        return self._vector_db.get_by_id(video_id)
    
    def save_index(
        self,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ) -> None:
        """
        Save the index and metadata to disk.
        
        Args:
            index_path: Path to save the FAISS index
            metadata_path: Path to save the metadata
        """
        index_path = index_path or self.config.index_path
        metadata_path = metadata_path or self.config.metadata_path
        
        self._vector_db.save(index_path, metadata_path)
        logger.info(f"Saved index to {index_path} and metadata to {metadata_path}")
    
    def load_index(
        self,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ) -> None:
        """
        Load the index and metadata from disk.
        
        Args:
            index_path: Path to load the FAISS index from
            metadata_path: Path to load the metadata from
        """
        index_path = index_path or self.config.index_path
        metadata_path = metadata_path or self.config.metadata_path
        
        self._vector_db.load(index_path, metadata_path)
        logger.info(f"Loaded index from {index_path} with {self.index_size} videos")
    
    def clear_index(self) -> None:
        """Clear all data from the index."""
        self._vector_db.clear()
        logger.info("Cleared retrieval index")
    
    def rebuild_index(self) -> None:
        """Rebuild the index, removing deleted entries."""
        self._vector_db.rebuild()
        logger.info(f"Rebuilt index with {self.index_size} videos")


def create_retrieval_agent(
    config: Optional[RetrievalAgentConfig] = None,
    vector_db: Optional[VectorDB] = None,
) -> RetrievalAgent:
    """
    Factory function to create a RetrievalAgent instance.
    
    Args:
        config: Optional configuration
        vector_db: Optional pre-configured VectorDB instance
        
    Returns:
        RetrievalAgent instance
    """
    return RetrievalAgent(config=config, vector_db=vector_db)
