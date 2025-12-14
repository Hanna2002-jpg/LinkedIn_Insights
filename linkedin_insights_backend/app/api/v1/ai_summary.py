"""
AI Summary API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.core.cache import redis_client
from app.models import Page, Post, Employee
from app.schemas.ai_summary import AISummaryRequest, AISummaryResponse, QuickSummaryResponse
from app.services.ai_service import ai_service

router = APIRouter()


@router.post("/summary/{page_id}", response_model=AISummaryResponse)
async def generate_ai_summary(
    page_id: str,
    include_posts: bool = Query(True, description="Include post analysis"),
    include_employees: bool = Query(True, description="Include employee/follower analysis"),
    force_refresh: bool = Query(False, description="Force regenerate summary"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate comprehensive AI summary for a LinkedIn page.
    
    Uses ChatGPT to analyze:
    - Page information and positioning
    - Follower demographics and engagement
    - Content performance and patterns
    - Actionable recommendations
    """
    # Check cache first (unless force refresh)
    cache_key = redis_client.cache_key("ai_summary", page_id)
    if not force_refresh:
        cached = await redis_client.get(cache_key)
        if cached:
            return AISummaryResponse(**cached)
    
    # Find page
    page_query = select(Page).where(Page.page_id == page_id)
    page_result = await db.execute(page_query)
    page = page_result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found")
    
    # Prepare data for AI analysis
    page_data = page.to_dict()
    posts_data = None
    employees_data = None
    
    if include_posts:
        posts_query = (
            select(Post)
            .where(Post.page_id == page.id)
            .order_by(Post.posted_at.desc())
            .limit(25)
        )
        posts_result = await db.execute(posts_query)
        posts_data = [p.to_dict() for p in posts_result.scalars().all()]
    
    if include_employees:
        employees_query = (
            select(Employee)
            .where(Employee.page_id == page.id)
            .limit(50)
        )
        employees_result = await db.execute(employees_query)
        employees_data = [e.to_dict() for e in employees_result.scalars().all()]
    
    # Generate AI summary
    summary = await ai_service.generate_page_summary(
        page_data=page_data,
        posts_data=posts_data,
        employees_data=employees_data
    )
    
    # Cache the result (longer TTL for AI summaries - 30 minutes)
    await redis_client.set(cache_key, summary, ttl=1800)
    
    return AISummaryResponse(**summary)


@router.get("/quick-summary/{page_id}", response_model=QuickSummaryResponse)
async def get_quick_summary(
    page_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a quick summary with key statistics.
    Faster than full AI summary - uses cached data when available.
    """
    # Check cache
    cache_key = redis_client.cache_key("quick_summary", page_id)
    cached = await redis_client.get(cache_key)
    if cached:
        return QuickSummaryResponse(**cached)
    
    # Find page
    page_query = select(Page).where(Page.page_id == page_id)
    page_result = await db.execute(page_query)
    page = page_result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found")
    
    # Get post statistics
    from sqlalchemy import func
    
    post_stats_query = select(
        func.count(Post.id).label('total_posts'),
        func.avg(Post.like_count).label('avg_likes'),
        func.avg(Post.comment_count).label('avg_comments'),
        func.sum(Post.like_count).label('total_likes')
    ).where(Post.page_id == page.id)
    
    post_stats_result = await db.execute(post_stats_query)
    post_stats = post_stats_result.one()
    
    # Get employee count
    employee_count_query = select(func.count(Employee.id)).where(Employee.page_id == page.id)
    employee_count_result = await db.execute(employee_count_query)
    employee_count = employee_count_result.scalar()
    
    # Generate summary text
    summary = (
        f"{page.name} is a {page.industry or 'company'} with {page.follower_count:,} followers. "
        f"They have published {post_stats.total_posts or 0} posts with an average of "
        f"{int(post_stats.avg_likes or 0)} likes per post."
    )
    
    response = {
        "page_id": page_id,
        "summary": summary,
        "key_stats": {
            "follower_count": page.follower_count,
            "employee_count": page.employee_count or employee_count,
            "total_posts": post_stats.total_posts or 0,
            "total_engagement": int(post_stats.total_likes or 0),
            "avg_likes_per_post": round(float(post_stats.avg_likes or 0), 1),
            "avg_comments_per_post": round(float(post_stats.avg_comments or 0), 1),
            "industry": page.industry,
            "company_size": page.company_size,
            "headquarters": page.headquarters
        },
        "generated_at": datetime.now()
    }
    
    # Cache for 5 minutes
    await redis_client.set(cache_key, response)
    
    return QuickSummaryResponse(**response)


@router.post("/compare")
async def compare_pages(
    page_ids: list[str],
    db: AsyncSession = Depends(get_db)
):
    """
    Compare multiple LinkedIn pages using AI analysis.
    """
    if len(page_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 page IDs required for comparison")
    
    if len(page_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 pages can be compared at once")
    
    pages_data = []
    
    for page_id in page_ids:
        page_query = select(Page).where(Page.page_id == page_id)
        page_result = await db.execute(page_query)
        page = page_result.scalar_one_or_none()
        
        if page:
            pages_data.append(page.to_dict())
    
    if len(pages_data) < 2:
        raise HTTPException(status_code=404, detail="Not enough pages found for comparison")
    
    # Generate comparison using AI
    comparison = await _generate_comparison(pages_data)
    
    return comparison


async def _generate_comparison(pages: list[dict]) -> dict:
    """Generate AI-powered comparison between pages"""
    from app.services.ai_service import ai_service
    import openai
    import json
    
    prompt = f"""Compare these LinkedIn company pages and provide insights:

Pages:
{json.dumps([{
    'name': p.get('name'),
    'industry': p.get('industry'),
    'followers': p.get('follower_count'),
    'employees': p.get('employee_count'),
    'description': p.get('description', '')[:200]
} for p in pages], indent=2)}

Provide comparison in JSON format with:
- winner_by_followers
- winner_by_engagement
- key_differences: list of notable differences
- similarities: list of common traits
- recommendations: specific advice for each company
"""
    
    try:
        response = await ai_service.client.chat.completions.create(
            model=ai_service.model,
            messages=[
                {"role": "system", "content": "You are a LinkedIn analytics expert. Compare company pages objectively."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        return {
            "pages_compared": [p.get("name") for p in pages],
            "analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "pages_compared": [p.get("name") for p in pages],
            "analysis": {
                "error": "Could not generate comparison",
                "basic_comparison": {
                    "by_followers": sorted(pages, key=lambda x: x.get("follower_count", 0), reverse=True)[0].get("name")
                }
            },
            "generated_at": datetime.now().isoformat()
        }
