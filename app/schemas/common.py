"""
Common Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List
from datetime import datetime

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size

class FilterParams(BaseModel):
    """Common filter parameters"""
    name: Optional[str] = Field(None, description="Search by name (partial match)")
    industry: Optional[str] = Field(None, description="Filter by industry")
    min_followers: Optional[int] = Field(None, ge=0, description="Minimum follower count")
    max_followers: Optional[int] = Field(None, ge=0, description="Maximum follower count")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
