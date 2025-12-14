"""
Post Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    """Base post schema"""
    text: Optional[str] = None
    content_type: Optional[str] = None

class PostCreate(PostBase):
    """Schema for creating a post"""
    post_id: str
    page_id: int

class PostResponse(BaseModel):
    """Post response schema"""
    id: int
    post_id: str
    page_id: int
    text: Optional[str] = None
    content_type: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    view_count: int = 0
    posted_at: Optional[datetime] = None
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PostListResponse(BaseModel):
    """Paginated post list response"""
    items: List[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PostDetailResponse(PostResponse):
    """Detailed post response with comments"""
    comments: List[dict] = []
