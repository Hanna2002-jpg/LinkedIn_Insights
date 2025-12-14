"""
Storage Service
Handles file uploads to S3/GCS
"""
import aioboto3
import aiohttp
import hashlib
from typing import Optional, Tuple
from datetime import datetime
import mimetypes
from app.core.config import settings

class StorageService:
    """Service for cloud storage operations"""
    
    def __init__(self):
        self.bucket = settings.AWS_S3_BUCKET
        self.region = settings.AWS_REGION
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
    
    async def upload_from_url(
        self, 
        url: str, 
        folder: str = "images",
        custom_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Download file from URL and upload to S3
        
        Args:
            url: Source URL to download from
            folder: S3 folder path
            custom_filename: Optional custom filename
        
        Returns:
            S3 URL of uploaded file or None on failure
        """
        if not url:
            return None
        
        try:
            # Download the file
            content, content_type = await self._download_file(url)
            if not content:
                return None
            
            # Generate filename
            if custom_filename:
                filename = custom_filename
            else:
                filename = self._generate_filename(url, content_type)
            
            # Full S3 key
            s3_key = f"{folder}/{filename}"
            
            # Upload to S3
            async with self.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=content,
                    ContentType=content_type,
                    ACL='public-read'
                )
            
            # Return public URL
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
            
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return None
    
    async def _download_file(self, url: str) -> Tuple[Optional[bytes], str]:
        """Download file from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('Content-Type', 'application/octet-stream')
                        return content, content_type
        except Exception as e:
            print(f"Error downloading file: {e}")
        
        return None, 'application/octet-stream'
    
    def _generate_filename(self, url: str, content_type: str) -> str:
        """Generate unique filename"""
        # Get extension from content type
        extension = mimetypes.guess_extension(content_type) or '.bin'
        
        # Generate hash from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{timestamp}_{url_hash}{extension}"
    
    async def upload_bytes(
        self, 
        content: bytes, 
        filename: str,
        folder: str = "uploads",
        content_type: str = 'application/octet-stream'
    ) -> Optional[str]:
        """
        Upload bytes directly to S3
        
        Args:
            content: File content as bytes
            filename: Filename to use
            folder: S3 folder path
            content_type: MIME type of the file
        
        Returns:
            S3 URL of uploaded file
        """
        try:
            s3_key = f"{folder}/{filename}"
            
            async with self.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=content,
                    ContentType=content_type,
                    ACL='public-read'
                )
            
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
            
        except Exception as e:
            print(f"Error uploading bytes to S3: {e}")
            return None
    
    async def delete_file(self, s3_url: str) -> bool:
        """Delete file from S3"""
        try:
            # Extract key from URL
            key = s3_url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[1]
            
            async with self.session.client('s3') as s3:
                await s3.delete_object(Bucket=self.bucket, Key=key)
            
            return True
            
        except Exception as e:
            print(f"Error deleting from S3: {e}")
            return False
    
    async def clone_page_images(
        self, 
        profile_picture_url: Optional[str],
        page_id: str
    ) -> Optional[str]:
        """Clone page profile picture to S3"""
        if not profile_picture_url:
            return None
        
        return await self.upload_from_url(
            url=profile_picture_url,
            folder=f"pages/{page_id}",
            custom_filename="profile_picture.jpg"
        )
    
    async def clone_post_media(
        self, 
        media_url: Optional[str],
        page_id: str,
        post_id: str
    ) -> Optional[str]:
        """Clone post media to S3"""
        if not media_url:
            return None
        
        return await self.upload_from_url(
            url=media_url,
            folder=f"pages/{page_id}/posts/{post_id}"
        )


# Singleton instance
storage_service = StorageService()
