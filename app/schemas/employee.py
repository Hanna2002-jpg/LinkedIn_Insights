"""
Employee Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EmployeeResponse(BaseModel):
    """Employee response schema"""
    id: int
    linkedin_id: str
    page_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    headline: Optional[str] = None
    profile_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    connections_count: Optional[int] = None
    is_following: bool = False
    is_follower: bool = False
    is_employee: bool = True
    skills: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EmployeeListResponse(BaseModel):
    """Paginated employee list response"""
    items: List[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class FollowerResponse(BaseModel):
    """Follower/Following response"""
    followers: List[EmployeeResponse]
    following: List[EmployeeResponse]
    total_followers: int
    total_following: int
