"""
AI Summary Schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict,Any
from datetime import datetime

class AISummaryRequest(BaseModel):
    """Request for AI summary"""
    page_id: str
    include_posts: bool = True
    include_employees: bool = True

class PageInsight(BaseModel):
    """Individual page insight"""
    category: str
    insight: str
    confidence: float

class FollowerAnalysis(BaseModel):
    """Follower analysis data"""
    total_count: int
    growth_trend: Optional[str] = None
    top_industries: List[str] = []
    top_locations: List[str] = []
    engagement_rate: Optional[float] = None

class ContentAnalysis(BaseModel):
    """Content analysis data"""
    total_posts: int
    avg_likes: float
    avg_comments: float
    avg_shares: float
    top_performing_topics: List[str] = []
    posting_frequency: Optional[str] = None
    best_posting_times: List[str] = []

class AISummaryResponse(BaseModel):
    """AI Summary response"""
    page_id: str
    page_name: str
    summary: str
    page_type: str
    industry_classification: str
    key_insights: List[PageInsight]
    follower_analysis: FollowerAnalysis
    content_analysis: ContentAnalysis
    recommendations: List[str]
    generated_at: datetime
    
    class Config:
        from_attributes = True

class QuickSummaryResponse(BaseModel):
    """Quick summary response"""
    page_id: str
    summary: str
    key_stats: Dict[str, Any]
    generated_at: datetime
