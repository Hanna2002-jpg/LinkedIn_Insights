"""
Tests for Posts API
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.anyio
async def test_get_posts(client: AsyncClient):
    """Test getting all posts"""
    response = await client.get("/api/v1/posts/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.anyio
async def test_get_posts_by_page(client: AsyncClient):
    """Test getting posts filtered by page"""
    response = await client.get("/api/v1/posts/?page_id=test-page")
    assert response.status_code == 200

@pytest.mark.anyio
async def test_get_posts_by_content_type(client: AsyncClient):
    """Test getting posts filtered by content type"""
    response = await client.get("/api/v1/posts/?content_type=image")
    assert response.status_code == 200

@pytest.mark.anyio
async def test_get_posts_min_likes(client: AsyncClient):
    """Test getting posts with minimum likes"""
    response = await client.get("/api/v1/posts/?min_likes=100")
    assert response.status_code == 200

@pytest.mark.anyio
async def test_get_post_not_found(client: AsyncClient):
    """Test getting a non-existent post"""
    response = await client.get("/api/v1/posts/nonexistent-post-id")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_get_recent_posts(client: AsyncClient):
    """Test getting recent posts for a page"""
    # This will return 404 if page doesn't exist
    response = await client.get("/api/v1/posts/recent/test-page")
    assert response.status_code in [200, 404]
