"""
Tests for AI Summary API
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
async def test_quick_summary_not_found(client: AsyncClient):
    """Test quick summary for non-existent page"""
    response = await client.get("/api/v1/ai/quick-summary/nonexistent")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_ai_summary_not_found(client: AsyncClient):
    """Test AI summary for non-existent page"""
    response = await client.post("/api/v1/ai/summary/nonexistent")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_compare_pages_too_few(client: AsyncClient):
    """Test page comparison with too few pages"""
    response = await client.post("/api/v1/ai/compare", json=["only-one"])
    assert response.status_code == 400

@pytest.mark.anyio
async def test_compare_pages_too_many(client: AsyncClient):
    """Test page comparison with too many pages"""
    response = await client.post(
        "/api/v1/ai/compare", 
        json=["page1", "page2", "page3", "page4", "page5", "page6"]
    )
    assert response.status_code == 400
