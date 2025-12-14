"""
LinkedIn Employee/User Model
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Employee(Base):
    """LinkedIn Employee/User entity"""
    
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    linkedin_id = Column(String(255), unique=True, nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    
    # Profile Information
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    full_name = Column(String(500), nullable=True)
    headline = Column(String(500), nullable=True)
    
    # Profile URLs
    profile_url = Column(String(1000), nullable=True)
    profile_picture_url = Column(String(1000), nullable=True)
    profile_picture_s3_url = Column(String(1000), nullable=True)
    
    # Current Position
    current_title = Column(String(500), nullable=True)
    current_company = Column(String(500), nullable=True)
    
    # Location
    location = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Professional Details
    industry = Column(String(255), nullable=True)
    connections_count = Column(Integer, nullable=True)
    
    # Status
    is_following = Column(Boolean, default=False)
    is_follower = Column(Boolean, default=False)
    is_employee = Column(Boolean, default=True)
    
    # Experience and Education Summary
    experience_summary = Column(JSON, nullable=True)
    education_summary = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    
    # Additional Data
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    page = relationship("Page", back_populates="employees")
    
    def __repr__(self):
        return f"<Employee(linkedin_id='{self.linkedin_id}', name='{self.full_name}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "linkedin_id": self.linkedin_id,
            "page_id": self.page_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "headline": self.headline,
            "profile_url": self.profile_url,
            "profile_picture_url": self.profile_picture_s3_url or self.profile_picture_url,
            "current_title": self.current_title,
            "current_company": self.current_company,
            "location": self.location,
            "country": self.country,
            "industry": self.industry,
            "connections_count": self.connections_count,
            "is_following": self.is_following,
            "is_follower": self.is_follower,
            "is_employee": self.is_employee,
            "skills": self.skills,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
