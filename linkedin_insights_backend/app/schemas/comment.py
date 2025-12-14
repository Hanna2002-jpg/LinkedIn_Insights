"""
Comment Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CommentResponse(BaseModel):
    """Comment response schema"""
    id: int
    comment_id: str
    post_id: int
    text: Optional[str] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_profile_url: Optional[str] = None
    author_profile_picture: Optional[str] = None
    like_count: int = 0
    reply_count: int = 0
    parent_comment_id: Optional[int] = None
    commented_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    replies: List["CommentResponse"] = []
    
    class Config:
        from_attributes = True

class CommentListResponse(BaseModel):
    """Paginated comment list response"""
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int
