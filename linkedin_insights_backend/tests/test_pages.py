"""
Tests for Pages API
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
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.anyio
async def test_get_pages_empty(client: AsyncClient):
    """Test getting pages when database is empty"""
    response = await client.get("/api/v1/pages/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 0

@pytest.mark.anyio
async def test_get_pages_with_filters(client: AsyncClient):
    """Test getting pages with filters"""
    response = await client.get("/api/v1/pages/?min_followers=1000&max_followers=50000")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data

@pytest.mark.anyio
async def test_get_page_not_found(client: AsyncClient):
    """Test getting a non-existent page without fetching"""
    response = await client.get("/api/v1/pages/nonexistent-page-12345?fetch_if_missing=false")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_pagination(client: AsyncClient):
    """Test pagination parameters"""
    response = await client.get("/api/v1/pages/?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert "total_pages" in data
    assert "has_next" in data
    assert "has_prev" in data

@pytest.mark.anyio
async def test_invalid_pagination(client: AsyncClient):
    """Test invalid pagination parameters"""
    response = await client.get("/api/v1/pages/?page=0")
    assert response.status_code == 422  # Validation error

@pytest.mark.anyio
async def test_search_by_name(client: AsyncClient):
    """Test searching pages by name"""
    response = await client.get("/api/v1/pages/?name=test")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data

@pytest.mark.anyio
async def test_filter_by_industry(client: AsyncClient):
    """Test filtering pages by industry"""
    response = await client.get("/api/v1/pages/?industry=Technology")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
