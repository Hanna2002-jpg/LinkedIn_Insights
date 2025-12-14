"""
LinkedIn Post Model
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Post(Base):
    """LinkedIn Post entity"""
    
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), unique=True, nullable=False, index=True)  # LinkedIn post ID
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    text = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=True)  # text, image, video, article, etc.
    
    # Media
    media_url = Column(String(1000), nullable=True)
    media_s3_url = Column(String(1000), nullable=True)  # Cloned to S3
    media_type = Column(String(50), nullable=True)  # image, video, document
    
    # Engagement Metrics
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # Post Metadata
    posted_at = Column(DateTime(timezone=True), nullable=True)
    author_name = Column(String(255), nullable=True)
    author_title = Column(String(500), nullable=True)
    
    # Additional Data
    hashtags = Column(JSON, nullable=True)  # List of hashtags
    mentions = Column(JSON, nullable=True)  # List of mentioned users/pages
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    page = relationship("Page", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Post(post_id='{self.post_id}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "post_id": self.post_id,
            "page_id": self.page_id,
            "text": self.text,
            "content_type": self.content_type,
            "media_url": self.media_s3_url or self.media_url,
            "media_type": self.media_type,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "view_count": self.view_count,
            "posted_at": self.posted_at,
            "author_name": self.author_name,
            "author_title": self.author_title,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
