"""
Pages API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.cache import redis_client
from app.models import Page, Post, Employee
from app.schemas.page import PageResponse, PageListResponse, PageDetailResponse
from app.schemas.common import FilterParams
from app.services.linkedin_service import linkedin_service
from app.services.storage_service import storage_service

router = APIRouter()


@router.get("/", response_model=PageListResponse)
async def get_pages(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Search by name (partial match)"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    min_followers: Optional[int] = Query(None, ge=0, description="Minimum follower count"),
    max_followers: Optional[int] = Query(None, ge=0, description="Maximum follower count"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of LinkedIn pages with optional filters.
    
    Filters:
    - name: Partial match search on page name
    - industry: Exact match on industry
    - min_followers/max_followers: Follower count range
    """
    # Build query with filters
    query = select(Page)
    count_query = select(func.count(Page.id))
    
    filters = []
    
    if name:
        filters.append(Page.name.ilike(f"%{name}%"))
    
    if industry:
        filters.append(Page.industry.ilike(f"%{industry}%"))
    
    if min_followers is not None:
        filters.append(Page.follower_count >= min_followers)
    
    if max_followers is not None:
        filters.append(Page.follower_count <= max_followers)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size
    
    # Get paginated results
    query = query.offset(offset).limit(page_size).order_by(Page.follower_count.desc())
    result = await db.execute(query)
    pages = result.scalars().all()
    
    return PageListResponse(
        items=[PageResponse.model_validate(p) for p in pages],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get("/{page_id}", response_model=PageDetailResponse)
async def get_page(
    page_id: str,
    fetch_if_missing: bool = Query(True, description="Fetch from LinkedIn if not in DB"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific LinkedIn page by page_id (URL slug).
    
    If the page is not in the database and fetch_if_missing is True,
    it will be fetched from LinkedIn in real-time.
    """
    # Check cache first
    cache_key = redis_client.cache_key("page_detail", page_id)
    cached = await redis_client.get(cache_key)
    if cached:
        return PageDetailResponse(**cached)
    
    # Try to find in database
    query = select(Page).where(Page.page_id == page_id)
    result = await db.execute(query)
    page = result.scalar_one_or_none()
    
    if not page and fetch_if_missing:
        # Fetch from LinkedIn API
        page = await _fetch_and_store_page(page_id, db)
    
    if not page:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found")
    
    # Get posts count
    posts_count_query = select(func.count(Post.id)).where(Post.page_id == page.id)
    posts_count_result = await db.execute(posts_count_query)
    posts_count = posts_count_result.scalar()
    
    # Get recent posts
    recent_posts_query = (
        select(Post)
        .where(Post.page_id == page.id)
        .order_by(Post.posted_at.desc())
        .limit(10)
    )
    recent_posts_result = await db.execute(recent_posts_query)
    recent_posts = [p.to_dict() for p in recent_posts_result.scalars().all()]
    
    response_data = {
        **page.to_dict(),
        "posts_count": posts_count,
        "recent_posts": recent_posts
    }
    
    # Cache the result
    await redis_client.set(cache_key, response_data)
    
    return PageDetailResponse(**response_data)


@router.post("/{page_id}/refresh", response_model=PageResponse)
async def refresh_page(
    page_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Force refresh page data from LinkedIn API.
    Updates the database with latest information.
    """
    # Invalidate cache
    await redis_client.clear_pattern(f"*{page_id}*")
    
    # Fetch fresh data
    page = await _fetch_and_store_page(page_id, db, force_update=True)
    
    if not page:
        raise HTTPException(status_code=404, detail=f"Could not fetch page '{page_id}' from LinkedIn")
    
    return PageResponse.model_validate(page)


@router.get("/{page_id}/posts")
async def get_page_posts(
    page_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=25),
    db: AsyncSession = Depends(get_db)
):
    """
    Get posts for a specific page with pagination.
    Returns up to 15-25 posts as specified in requirements.
    """
    # Find the page
    page_query = select(Page).where(Page.page_id == page_id)
    page_result = await db.execute(page_query)
    db_page = page_result.scalar_one_or_none()
    
    if not db_page:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found")
    
    # Get posts with pagination
    offset = (page - 1) * page_size
    
    posts_query = (
        select(Post)
        .where(Post.page_id == db_page.id)
        .order_by(Post.posted_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    count_query = select(func.count(Post.id)).where(Post.page_id == db_page.id)
    
    posts_result = await db.execute(posts_query)
    count_result = await db.execute(count_query)
    
    posts = posts_result.scalars().all()
    total = count_result.scalar()
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": [p.to_dict() for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


@router.get("/{page_id}/followers")
async def get_page_followers(
    page_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get followers/following of a specific page.
    """
    # Find the page
    page_query = select(Page).where(Page.page_id == page_id)
    page_result = await db.execute(page_query)
    db_page = page_result.scalar_one_or_none()
    
    if not db_page:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found")
    
    offset = (page - 1) * page_size
    
    # Get followers
    followers_query = (
        select(Employee)
        .where(Employee.page_id == db_page.id, Employee.is_follower == True)
        .offset(offset)
        .limit(page_size)
    )
    
    # Get following
    following_query = (
        select(Employee)
        .where(Employee.page_id == db_page.id, Employee.is_following == True)
        .offset(offset)
        .limit(page_size)
    )
    
    followers_result = await db.execute(followers_query)
    following_result = await db.execute(following_query)
    
    followers = followers_result.scalars().all()
    following = following_result.scalars().all()
    
    # Get counts
    followers_count_query = select(func.count(Employee.id)).where(
        Employee.page_id == db_page.id, Employee.is_follower == True
    )
    following_count_query = select(func.count(Employee.id)).where(
        Employee.page_id == db_page.id, Employee.is_following == True
    )
    
    followers_count = (await db.execute(followers_count_query)).scalar()
    following_count = (await db.execute(following_count_query)).scalar()
    
    return {
        "followers": [f.to_dict() for f in followers],
        "following": [f.to_dict() for f in following],
        "total_followers": followers_count,
        "total_following": following_count,
        "page": page,
        "page_size": page_size
    }


async def _fetch_and_store_page(
    page_id: str, 
    db: AsyncSession,
    force_update: bool = False
) -> Optional[Page]:
    """Fetch page from LinkedIn and store in database"""
    # Check if page exists
    existing_query = select(Page).where(Page.page_id == page_id)
    existing_result = await db.execute(existing_query)
    existing_page = existing_result.scalar_one_or_none()
    
    if existing_page and not force_update:
        return existing_page
    
    # Fetch from LinkedIn
    linkedin_data = await linkedin_service.get_organization_by_vanity_name(page_id)
    
    if not linkedin_data:
        return None
    
    # Clone profile picture to S3
    s3_picture_url = await storage_service.clone_page_images(
        linkedin_data.get("profile_picture_url"),
        page_id
    )
    
    if existing_page:
        # Update existing page
        for key, value in linkedin_data.items():
            if hasattr(existing_page, key) and value is not None:
                setattr(existing_page, key, value)
        
        existing_page.profile_picture_s3_url = s3_picture_url
        existing_page.last_scraped_at = datetime.now()
        await db.commit()
        await db.refresh(existing_page)
        return existing_page
    
    # Create new page
    page = Page(
        page_id=page_id,
        linkedin_id=linkedin_data.get("linkedin_id"),
        name=linkedin_data.get("name"),
        url=linkedin_data.get("url"),
        profile_picture_url=linkedin_data.get("profile_picture_url"),
        profile_picture_s3_url=s3_picture_url,
        description=linkedin_data.get("description"),
        website=linkedin_data.get("website"),
        industry=linkedin_data.get("industry"),
        company_size=linkedin_data.get("company_size"),
        headquarters=linkedin_data.get("headquarters"),
        founded_year=linkedin_data.get("founded_year"),
        company_type=linkedin_data.get("company_type"),
        follower_count=linkedin_data.get("follower_count", 0),
        specialties=linkedin_data.get("specialties"),
        locations=linkedin_data.get("locations"),
        last_scraped_at=datetime.now()
    )
    
    db.add(page)
    await db.commit()
    await db.refresh(page)
    
    # Fetch and store posts
    await _fetch_and_store_posts(page, db)
    
    # Fetch and store employees
    await _fetch_and_store_employees(page, db)
    
    return page


async def _fetch_and_store_posts(page: Page, db: AsyncSession):
    """Fetch and store posts for a page"""
    posts_data = await linkedin_service.get_organization_posts(page.linkedin_id, count=25)
    
    for post_data in posts_data:
        # Clone media to S3
        s3_media_url = await storage_service.clone_post_media(
            post_data.get("media_url"),
            page.page_id,
            post_data.get("post_id")
        )
        
        post = Post(
            post_id=post_data.get("post_id"),
            page_id=page.id,
            text=post_data.get("text"),
            content_type=post_data.get("content_type"),
            media_url=post_data.get("media_url"),
            media_s3_url=s3_media_url,
            media_type=post_data.get("media_type"),
            like_count=post_data.get("like_count", 0),
            comment_count=post_data.get("comment_count", 0),
            share_count=post_data.get("share_count", 0),
            posted_at=post_data.get("posted_at"),
            hashtags=post_data.get("hashtags"),
            mentions=post_data.get("mentions")
        )
        db.add(post)
    
    await db.commit()


async def _fetch_and_store_employees(page: Page, db: AsyncSession):
    """Fetch and store employees for a page"""
    employees_data = await linkedin_service.get_organization_employees(page.linkedin_id, count=50)
    
    for emp_data in employees_data:
        employee = Employee(
            linkedin_id=emp_data.get("linkedin_id"),
            page_id=page.id,
            first_name=emp_data.get("first_name"),
            last_name=emp_data.get("last_name"),
            full_name=f"{emp_data.get('first_name', '')} {emp_data.get('last_name', '')}".strip(),
            headline=emp_data.get("headline"),
            profile_url=emp_data.get("profile_url"),
            profile_picture_url=emp_data.get("profile_picture_url"),
            location=emp_data.get("location"),
            industry=emp_data.get("industry"),
            is_employee=True
        )
        db.add(employee)
    
    await db.commit()
