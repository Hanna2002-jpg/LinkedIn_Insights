"""
LinkedIn Comment Model
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Comment(Base):
    """LinkedIn Comment entity"""
    
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(255), unique=True, nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    
    # Comment Content
    text = Column(Text, nullable=True)
    
    # Author Information
    author_id = Column(String(255), nullable=True)
    author_name = Column(String(255), nullable=True)
    author_title = Column(String(500), nullable=True)
    author_profile_url = Column(String(1000), nullable=True)
    author_profile_picture = Column(String(1000), nullable=True)
    
    # Engagement
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # Parent comment (for nested replies)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    
    # Timestamps
    commented_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional Data
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])
    
    def __repr__(self):
        return f"<Comment(comment_id='{self.comment_id}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "text": self.text,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "author_title": self.author_title,
            "author_profile_url": self.author_profile_url,
            "author_profile_picture": self.author_profile_picture,
            "like_count": self.like_count,
            "reply_count": self.reply_count,
            "parent_comment_id": self.parent_comment_id,
            "commented_at": self.commented_at,
            "created_at": self.created_at
        }
