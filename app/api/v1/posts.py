"""
Posts API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.cache import redis_client
from app.models import Post, Comment, Page
from app.schemas.post import PostResponse, PostListResponse, PostDetailResponse

router = APIRouter()


@router.get("/", response_model=PostListResponse)
async def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    page_id: Optional[str] = Query(None, description="Filter by page_id"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    min_likes: Optional[int] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of posts with optional filters.
    """
    query = select(Post)
    count_query = select(func.count(Post.id))
    
    # Apply filters
    if page_id:
        page_query = select(Page.id).where(Page.page_id == page_id)
        page_result = await db.execute(page_query)
        db_page_id = page_result.scalar_one_or_none()
        if db_page_id:
            query = query.where(Post.page_id == db_page_id)
            count_query = count_query.where(Post.page_id == db_page_id)
    
    if content_type:
        query = query.where(Post.content_type == content_type)
        count_query = count_query.where(Post.content_type == content_type)
    
    if min_likes is not None:
        query = query.where(Post.like_count >= min_likes)
        count_query = count_query.where(Post.like_count >= min_likes)
    
    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size
    
    query = query.offset(offset).limit(page_size).order_by(Post.posted_at.desc())
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: str,
    include_comments: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific post with optional comments.
    """
    # Check cache
    cache_key = redis_client.cache_key("post_detail", post_id)
    cached = await redis_client.get(cache_key)
    if cached:
        return PostDetailResponse(**cached)
    
    # Find post
    query = select(Post).where(Post.post_id == post_id)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail=f"Post '{post_id}' not found")
    
    response_data = post.to_dict()
    
    if include_comments:
        # Get comments
        comments_query = (
            select(Comment)
            .where(Comment.post_id == post.id)
            .order_by(Comment.commented_at.desc())
            .limit(50)
        )
        comments_result = await db.execute(comments_query)
        comments = [c.to_dict() for c in comments_result.scalars().all()]
        response_data["comments"] = comments
    else:
        response_data["comments"] = []
    
    # Cache result
    await redis_client.set(cache_key, response_data)
    
    return PostDetailResponse(**response_data)


@router.get("/{post_id}/comments")
async def get_post_comments(
    post_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comments for a specific post with pagination.
    """
    # Find post
    post_query = select(Post).where(Post.post_id == post_id)
    post_result = await db.execute(post_query)
    post = post_result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail=f"Post '{post_id}' not found")
    
    # Get comments with pagination
    offset = (page - 1) * page_size
    
    comments_query = (
        select(Comment)
        .where(Comment.post_id == post.id)
        .order_by(Comment.commented_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    count_query = select(func.count(Comment.id)).where(Comment.post_id == post.id)
    
    comments_result = await db.execute(comments_query)
    count_result = await db.execute(count_query)
    
    comments = comments_result.scalars().all()
    total = count_result.scalar()
    
    return {
        "items": [c.to_dict() for c in comments],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/recent/{page_id}")
async def get_recent_posts(
    page_id: str,
    limit: int = Query(15, ge=1, le=25),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent 10-15 posts for a specific page.
    This endpoint is optimized for the common use case of getting recent posts.
    """
    # Find page
    page_query = select(Page).where(Page.page_id == page_id)
    page_result = await db.execute(page_query)
    db_page = page_result.scalar_one_or_none()
    
    if not db_page:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found")
    
    # Check cache
    cache_key = redis_client.cache_key("recent_posts", page_id, limit)
    cached = await redis_client.get(cache_key)
    if cached:
        return cached
    
    # Get recent posts
    posts_query = (
        select(Post)
        .where(Post.page_id == db_page.id)
        .order_by(Post.posted_at.desc())
        .limit(limit)
    )
    
    posts_result = await db.execute(posts_query)
    posts = [p.to_dict() for p in posts_result.scalars().all()]
    
    response = {
        "page_id": page_id,
        "page_name": db_page.name,
        "posts": posts,
        "count": len(posts)
    }
    
    # Cache for 5 minutes
    await redis_client.set(cache_key, response)
    
    return response
