"""
Page Schemas
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class PageBase(BaseModel):
    """Base page schema"""
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None

class PageCreate(PageBase):
    """Schema for creating a page"""
    page_id: str = Field(..., description="LinkedIn page URL slug (e.g., 'deepsolv')")

class PageUpdate(BaseModel):
    """Schema for updating a page"""
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None

class PageResponse(BaseModel):
    """Page response schema"""
    id: int
    page_id: str
    linkedin_id: Optional[str] = None
    name: str
    url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    founded_year: Optional[int] = None
    company_type: Optional[str] = None
    follower_count: int = 0
    employee_count: int = 0
    specialties: Optional[List[str]] = None
    locations: Optional[List[dict]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_scraped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PageListResponse(BaseModel):
    """Paginated page list response"""
    items: List[PageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PageDetailResponse(PageResponse):
    """Detailed page response with posts and employees count"""
    posts_count: int = 0
    recent_posts: List[dict] = []
