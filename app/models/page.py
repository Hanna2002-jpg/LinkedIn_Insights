"""
LinkedIn Page Model
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Page(Base):
    """LinkedIn Page entity"""
    
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_id = Column(String(255), unique=True, nullable=False, index=True)  # URL slug (e.g., "deepsolv")
    linkedin_id = Column(String(255), unique=True, nullable=True)  # Platform-specific ID
    
    # Basic Details
    name = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True)
    profile_picture_url = Column(String(1000), nullable=True)
    profile_picture_s3_url = Column(String(1000), nullable=True)  # Cloned to S3
    description = Column(Text, nullable=True)
    tagline = Column(String(500), nullable=True)
    
    # Company Details
    website = Column(String(500), nullable=True)
    industry = Column(String(255), nullable=True)
    company_size = Column(String(100), nullable=True)
    headquarters = Column(String(500), nullable=True)
    founded_year = Column(Integer, nullable=True)
    company_type = Column(String(100), nullable=True)
    
    # Metrics
    follower_count = Column(Integer, default=0)
    employee_count = Column(Integer, default=0)
    
    # Additional Data
    specialties = Column(JSON, nullable=True)  # List of specialties
    locations = Column(JSON, nullable=True)  # List of office locations
    extra_data = Column(JSON, nullable=True)  # Any additional fields
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    posts = relationship("Post", back_populates="page", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Page(page_id='{self.page_id}', name='{self.name}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "page_id": self.page_id,
            "linkedin_id": self.linkedin_id,
            "name": self.name,
            "url": self.url,
            "profile_picture_url": self.profile_picture_s3_url or self.profile_picture_url,
            "description": self.description,
            "tagline": self.tagline,
            "website": self.website,
            "industry": self.industry,
            "company_size": self.company_size,
            "headquarters": self.headquarters,
            "founded_year": self.founded_year,
            "company_type": self.company_type,
            "follower_count": self.follower_count,
            "employee_count": self.employee_count,
            "specialties": self.specialties,
            "locations": self.locations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_scraped_at": self.last_scraped_at
        }
