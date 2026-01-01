"""
Tests for the Retrieval Agent and Vector Database.
"""
import numpy as np
import pytest

from src.services.vector_db import (
    VectorDB,
    VectorDBConfig,
    VideoMetadata,
    RetrievalFilters,
    SearchResult,
)
from src.agents.retrieval_agent import (
    RetrievalAgent,
    RetrievalAgentConfig,
    create_retrieval_agent,
)


class TestVectorDB:
    """Tests for the VectorDB class."""
    
    def test_init_flat_index(self):
        """Test initialization with flat index."""
        config = VectorDBConfig(dimension=128, index_type="flat")
        db = VectorDB(config)
        
        assert db.size == 0
        assert db.is_trained
    
    def test_add_and_search(self):
        """Test adding vectors and searching."""
        config = VectorDBConfig(dimension=128)
        db = VectorDB(config)
        
        # Add some vectors
        for i in range(5):
            embedding = np.random.randn(128).astype(np.float32)
            metadata = VideoMetadata(
                video_id=f"video_{i}",
                video_path=f"/path/to/video_{i}.mp4",
                motion_type="pan" if i % 2 == 0 else "dolly_in",
            )
            db.add(f"video_{i}", embedding, metadata)
        
        assert db.size == 5
        
        # Search with no minimum similarity filter
        query = np.random.randn(128).astype(np.float32)
        filters = RetrievalFilters(min_similarity=-1.0)  # Allow all results
        results = db.search(query, top_k=3, filters=filters)
        
        assert len(results) == 3
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_search_with_filters(self):
        """Test searching with motion_type filter."""
        config = VectorDBConfig(dimension=128)
        db = VectorDB(config)
        
        # Add vectors with different motion types
        for i in range(10):
            embedding = np.random.randn(128).astype(np.float32)
            motion_type = "pan" if i < 5 else "dolly_in"
            metadata = VideoMetadata(
                video_id=f"video_{i}",
                video_path=f"/path/to/video_{i}.mp4",
                motion_type=motion_type,
            )
            db.add(f"video_{i}", embedding, metadata)
        
        # Search with filter
        query = np.random.randn(128).astype(np.float32)
        filters = RetrievalFilters(motion_type="pan")
        results = db.search(query, top_k=10, filters=filters)
        
        # All results should have motion_type="pan"
        assert all(r.metadata.motion_type == "pan" for r in results)
    
    def test_get_by_id(self):
        """Test getting metadata by video ID."""
        config = VectorDBConfig(dimension=128)
        db = VectorDB(config)
        
        embedding = np.random.randn(128).astype(np.float32)
        metadata = VideoMetadata(
            video_id="test_video",
            video_path="/path/to/test.mp4",
            motion_type="pan",
            annotation="Test annotation",
        )
        db.add("test_video", embedding, metadata)
        
        result = db.get_by_id("test_video")
        assert result is not None
        assert result.video_id == "test_video"
        assert result.annotation == "Test annotation"
        
        # Non-existent ID
        assert db.get_by_id("nonexistent") is None
    
    def test_remove(self):
        """Test removing a video from the index."""
        config = VectorDBConfig(dimension=128)
        db = VectorDB(config)
        
        embedding = np.random.randn(128).astype(np.float32)
        metadata = VideoMetadata(
            video_id="test_video",
            video_path="/path/to/test.mp4",
        )
        db.add("test_video", embedding, metadata)
        
        assert db.get_by_id("test_video") is not None
        
        result = db.remove("test_video")
        assert result is True
        assert db.get_by_id("test_video") is None
        
        # Remove non-existent
        assert db.remove("nonexistent") is False


class TestRetrievalAgent:
    """Tests for the RetrievalAgent class."""
    
    def test_init(self):
        """Test agent initialization."""
        config = RetrievalAgentConfig(dimension=128)
        agent = RetrievalAgent(config)
        
        assert agent.index_size == 0
    
    def test_index_video(self):
        """Test indexing a single video."""
        config = RetrievalAgentConfig(dimension=128)
        agent = RetrievalAgent(config)
        
        embedding = np.random.randn(128).astype(np.float32)
        idx = agent.index_video(
            video_id="test_video",
            video_path="/path/to/test.mp4",
            embedding=embedding,
            motion_type="pan",
            subject_type="person",
            thumbnail_url="http://example.com/thumb.jpg",
            annotation="Test video",
        )
        
        assert idx == 0
        assert agent.index_size == 1
        
        metadata = agent.get_video_metadata("test_video")
        assert metadata is not None
        assert metadata.motion_type == "pan"
        assert metadata.subject_type == "person"
    
    def test_index_video_from_frames(self):
        """Test indexing a video from frame embeddings."""
        config = RetrievalAgentConfig(dimension=128)
        agent = RetrievalAgent(config)
        
        # Create frame embeddings
        frame_embeddings = [
            np.random.randn(128).tolist() for _ in range(10)
        ]
        
        idx = agent.index_video_from_frames(
            video_id="test_video",
            video_path="/path/to/test.mp4",
            frame_embeddings=frame_embeddings,
            motion_type="dolly_in",
            aggregation="mean",
        )
        
        assert idx == 0
        assert agent.index_size == 1
    
    @pytest.mark.asyncio
    async def test_search(self):
        """Test searching for similar videos."""
        config = RetrievalAgentConfig(dimension=128, min_similarity=-1.0)  # Allow all results
        agent = RetrievalAgent(config)
        
        # Index some videos
        for i in range(5):
            embedding = np.random.randn(128).astype(np.float32)
            agent.index_video(
                video_id=f"video_{i}",
                video_path=f"/path/to/video_{i}.mp4",
                embedding=embedding,
                motion_type="pan" if i % 2 == 0 else "dolly_in",
            )
        
        # Search
        query = np.random.randn(128).astype(np.float32)
        result = await agent.search(
            query_embedding=query,
            query_video_id="query_video",
            top_k=3,
            min_similarity=-1.0,  # Allow all results
        )
        
        assert result.query_video_id == "query_video"
        assert len(result.results) == 3
    
    @pytest.mark.asyncio
    async def test_search_with_filter(self):
        """Test searching with motion_type filter."""
        config = RetrievalAgentConfig(dimension=128, min_similarity=0.0)
        agent = RetrievalAgent(config)
        
        # Index videos with different motion types
        for i in range(10):
            embedding = np.random.randn(128).astype(np.float32)
            motion_type = "pan" if i < 5 else "dolly_in"
            agent.index_video(
                video_id=f"video_{i}",
                video_path=f"/path/to/video_{i}.mp4",
                embedding=embedding,
                motion_type=motion_type,
            )
        
        # Search with filter
        query = np.random.randn(128).astype(np.float32)
        result = await agent.search(
            query_embedding=query,
            query_video_id="query_video",
            top_k=10,
            motion_type="pan",
        )
        
        # All results should have motion_type="pan"
        for r in result.results:
            metadata = agent.get_video_metadata(r.ref_video_id)
            assert metadata.motion_type == "pan"
    
    def test_index_batch(self):
        """Test batch indexing."""
        config = RetrievalAgentConfig(dimension=128)
        agent = RetrievalAgent(config)
        
        videos = [
            {
                "video_id": f"video_{i}",
                "video_path": f"/path/to/video_{i}.mp4",
                "embedding": np.random.randn(128).astype(np.float32),
                "motion_type": "pan",
            }
            for i in range(5)
        ]
        
        indices = agent.index_batch(videos)
        
        assert len(indices) == 5
        assert agent.index_size == 5
    
    def test_remove_video(self):
        """Test removing a video."""
        config = RetrievalAgentConfig(dimension=128)
        agent = RetrievalAgent(config)
        
        embedding = np.random.randn(128).astype(np.float32)
        agent.index_video(
            video_id="test_video",
            video_path="/path/to/test.mp4",
            embedding=embedding,
        )
        
        assert agent.get_video_metadata("test_video") is not None
        
        result = agent.remove_video("test_video")
        assert result is True
        assert agent.get_video_metadata("test_video") is None
    
    def test_clear_index(self):
        """Test clearing the index."""
        config = RetrievalAgentConfig(dimension=128)
        agent = RetrievalAgent(config)
        
        # Add some videos
        for i in range(5):
            embedding = np.random.randn(128).astype(np.float32)
            agent.index_video(
                video_id=f"video_{i}",
                video_path=f"/path/to/video_{i}.mp4",
                embedding=embedding,
            )
        
        assert agent.index_size == 5
        
        agent.clear_index()
        assert agent.index_size == 0


class TestCreateRetrievalAgent:
    """Tests for the factory function."""
    
    def test_create_with_defaults(self):
        """Test creating agent with default config."""
        agent = create_retrieval_agent()
        assert agent is not None
        assert agent.index_size == 0
    
    def test_create_with_config(self):
        """Test creating agent with custom config."""
        config = RetrievalAgentConfig(dimension=512, default_top_k=10)
        agent = create_retrieval_agent(config=config)
        
        assert agent.config.dimension == 512
        assert agent.config.default_top_k == 10
