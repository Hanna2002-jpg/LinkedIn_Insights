"""
LinkedIn API Service
Handles all LinkedIn API interactions
"""
import httpx
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime
from app.core.config import settings
from app.core.cache import redis_client

class LinkedInService:
    """Service for LinkedIn API operations"""
    
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(self):
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401"
        }
    
    async def get_organization_by_vanity_name(self, vanity_name: str) -> Optional[Dict[str, Any]]:
        """
        Get organization details by vanity name (page_id)
        
        Args:
            vanity_name: The URL slug of the company (e.g., 'deepsolv')
        
        Returns:
            Organization data dictionary or None
        """
        # Check cache first
        cache_key = redis_client.cache_key("org", vanity_name)
        cached = await redis_client.get(cache_key)
        if cached:
            return cached
        
        async with httpx.AsyncClient() as client:
            try:
                # First, lookup organization by vanity name
                lookup_url = f"{self.BASE_URL}/organizations?q=vanityName&vanityName={vanity_name}"
                response = await client.get(lookup_url, headers=self._get_headers())
                
                if response.status_code == 200:
                    data = response.json()
                    elements = data.get("elements", [])
                    
                    if elements:
                        org = elements[0]
                        org_id = org.get("id")
                        
                        # Get full organization details
                        org_data = await self._get_organization_details(client, org_id)
                        
                        # Cache the result
                        await redis_client.set(cache_key, org_data)
                        
                        return org_data
                
                return None
                
            except httpx.HTTPError as e:
                print(f"LinkedIn API error: {e}")
                return None
    
    async def _get_organization_details(self, client: httpx.AsyncClient, org_id: str) -> Dict[str, Any]:
        """Get detailed organization information"""
        detail_url = f"{self.BASE_URL}/organizations/{org_id}"
        
        # Add projections for additional fields
        params = {
            "projection": "(id,name,vanityName,localizedName,description,localizedDescription,"
                         "website,industries,staffCountRange,locations,logoV2,coverPhotoV2,"
                         "foundedOn,specialties,organizationType)"
        }
        
        response = await client.get(detail_url, headers=self._get_headers(), params=params)
        
        if response.status_code == 200:
            org = response.json()
            
            # Get follower count
            follower_count = await self._get_follower_count(client, org_id)
            
            return {
                "linkedin_id": str(org.get("id")),
                "name": org.get("localizedName") or org.get("name"),
                "page_id": org.get("vanityName"),
                "description": org.get("localizedDescription") or org.get("description"),
                "website": org.get("website", {}).get("localized", {}).get("en_US"),
                "industry": self._extract_industry(org.get("industries", [])),
                "company_size": self._extract_staff_count(org.get("staffCountRange")),
                "headquarters": self._extract_headquarters(org.get("locations", [])),
                "founded_year": self._extract_founded_year(org.get("foundedOn")),
                "company_type": org.get("organizationType"),
                "specialties": org.get("specialties", []),
                "locations": org.get("locations", []),
                "profile_picture_url": self._extract_logo_url(org.get("logoV2")),
                "follower_count": follower_count,
                "url": f"https://www.linkedin.com/company/{org.get('vanityName')}"
            }
        
        return {}
    
    async def _get_follower_count(self, client: httpx.AsyncClient, org_id: str) -> int:
        """Get organization follower count"""
        url = f"{self.BASE_URL}/organizationalEntityFollowerStatistics?q=organizationalEntity&organizationalEntity=urn:li:organization:{org_id}"
        
        try:
            response = await client.get(url, headers=self._get_headers())
            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                if elements:
                    return elements[0].get("followerCounts", {}).get("organicFollowerCount", 0)
        except Exception:
            pass
        
        return 0
    
    async def get_organization_posts(
        self, 
        org_id: str, 
        count: int = 25,
        start: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get organization posts
        
        Args:
            org_id: LinkedIn organization ID
            count: Number of posts to fetch (max 25)
            start: Starting index for pagination
        
        Returns:
            List of post data dictionaries
        """
        cache_key = redis_client.cache_key("posts", org_id, start, count)
        cached = await redis_client.get(cache_key)
        if cached:
            return cached
        
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/ugcPosts?q=authors&authors=List(urn:li:organization:{org_id})&count={count}&start={start}"
            
            try:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    data = response.json()
                    posts = []
                    
                    for element in data.get("elements", []):
                        post = self._parse_post(element)
                        if post:
                            posts.append(post)
                    
                    # Cache results
                    await redis_client.set(cache_key, posts)
                    
                    return posts
                
            except httpx.HTTPError as e:
                print(f"Error fetching posts: {e}")
        
        return []
    
    def _parse_post(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a UGC post element"""
        try:
            specific_content = element.get("specificContent", {})
            share_content = specific_content.get("com.linkedin.ugc.ShareContent", {})
            
            # Extract text
            share_commentary = share_content.get("shareCommentary", {})
            text = share_commentary.get("text", "")
            
            # Extract media
            media = share_content.get("media", [])
            media_url = None
            media_type = None
            
            if media:
                first_media = media[0]
                media_type = first_media.get("mediaType")
                media_url = first_media.get("originalUrl") or first_media.get("thumbnails", [{}])[0].get("url")
            
            # Extract engagement (requires additional API call in production)
            social_detail = element.get("socialDetail", {})
            
            return {
                "post_id": element.get("id"),
                "text": text,
                "content_type": self._determine_content_type(share_content),
                "media_url": media_url,
                "media_type": media_type,
                "posted_at": self._parse_timestamp(element.get("created", {}).get("time")),
                "like_count": social_detail.get("totalLikes", 0),
                "comment_count": social_detail.get("totalComments", 0),
                "share_count": social_detail.get("totalShares", 0),
                "hashtags": self._extract_hashtags(text),
                "mentions": self._extract_mentions(text)
            }
        except Exception as e:
            print(f"Error parsing post: {e}")
            return None
    
    async def get_post_comments(
        self, 
        post_urn: str, 
        count: int = 50
    ) -> List[Dict[str, Any]]:
        """Get comments on a post"""
        cache_key = redis_client.cache_key("comments", post_urn)
        cached = await redis_client.get(cache_key)
        if cached:
            return cached
        
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/socialActions/{post_urn}/comments?count={count}"
            
            try:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    data = response.json()
                    comments = []
                    
                    for element in data.get("elements", []):
                        comment = {
                            "comment_id": element.get("id"),
                            "text": element.get("message", {}).get("text"),
                            "author_id": element.get("actor"),
                            "like_count": element.get("likesSummary", {}).get("totalLikes", 0),
                            "commented_at": self._parse_timestamp(element.get("created", {}).get("time"))
                        }
                        comments.append(comment)
                    
                    await redis_client.set(cache_key, comments)
                    return comments
                    
            except httpx.HTTPError as e:
                print(f"Error fetching comments: {e}")
        
        return []
    
    async def get_organization_employees(
        self, 
        org_id: str, 
        count: int = 50,
        start: int = 0
    ) -> List[Dict[str, Any]]:
        """Get employees of an organization"""
        # Note: This requires Organization Access API permissions
        cache_key = redis_client.cache_key("employees", org_id, start, count)
        cached = await redis_client.get(cache_key)
        if cached:
            return cached
        
        async with httpx.AsyncClient() as client:
            # Using People Search API with current company filter
            url = f"{self.BASE_URL}/people?q=currentCompany&currentCompany=urn:li:organization:{org_id}&count={count}&start={start}"
            
            try:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    data = response.json()
                    employees = []
                    
                    for element in data.get("elements", []):
                        employee = self._parse_employee(element)
                        if employee:
                            employees.append(employee)
                    
                    await redis_client.set(cache_key, employees)
                    return employees
                    
            except httpx.HTTPError as e:
                print(f"Error fetching employees: {e}")
        
        return []
    
    def _parse_employee(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse employee data"""
        try:
            return {
                "linkedin_id": element.get("id"),
                "first_name": element.get("firstName", {}).get("localized", {}).get("en_US"),
                "last_name": element.get("lastName", {}).get("localized", {}).get("en_US"),
                "headline": element.get("headline", {}).get("localized", {}).get("en_US"),
                "profile_url": f"https://www.linkedin.com/in/{element.get('vanityName')}",
                "profile_picture_url": self._extract_profile_picture(element.get("profilePicture")),
                "location": element.get("location", {}).get("name"),
                "industry": element.get("industry")
            }
        except Exception:
            return None
    
    # Helper methods
    def _extract_industry(self, industries: List) -> Optional[str]:
        """Extract primary industry"""
        if industries:
            return industries[0] if isinstance(industries[0], str) else str(industries[0])
        return None
    
    def _extract_staff_count(self, staff_range: Optional[Dict]) -> Optional[str]:
        """Extract staff count range"""
        if staff_range:
            start = staff_range.get("start", 0)
            end = staff_range.get("end")
            if end:
                return f"{start}-{end}"
            return f"{start}+"
        return None
    
    def _extract_headquarters(self, locations: List) -> Optional[str]:
        """Extract headquarters location"""
        for loc in locations:
            if loc.get("isHeadquarters"):
                city = loc.get("city")
                country = loc.get("country")
                return f"{city}, {country}" if city and country else city or country
        return None
    
    def _extract_founded_year(self, founded: Optional[Dict]) -> Optional[int]:
        """Extract founded year"""
        if founded:
            return founded.get("year")
        return None
    
    def _extract_logo_url(self, logo: Optional[Dict]) -> Optional[str]:
        """Extract logo URL"""
        if logo:
            elements = logo.get("cropped~", {}).get("elements", [])
            if elements:
                # Get largest image
                largest = max(elements, key=lambda x: x.get("data", {}).get("width", 0))
                return largest.get("identifiers", [{}])[0].get("identifier")
        return None
    
    def _extract_profile_picture(self, picture: Optional[Dict]) -> Optional[str]:
        """Extract profile picture URL"""
        if picture:
            elements = picture.get("displayImage~", {}).get("elements", [])
            if elements:
                largest = max(elements, key=lambda x: x.get("data", {}).get("width", 0))
                return largest.get("identifiers", [{}])[0].get("identifier")
        return None
    
    def _determine_content_type(self, share_content: Dict) -> str:
        """Determine post content type"""
        share_media_category = share_content.get("shareMediaCategory")
        if share_media_category:
            return share_media_category.lower()
        return "text"
    
    def _parse_timestamp(self, timestamp: Optional[int]) -> Optional[datetime]:
        """Parse LinkedIn timestamp"""
        if timestamp:
            return datetime.fromtimestamp(timestamp / 1000)
        return None
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        import re
        return re.findall(r'#(\w+)', text)
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        import re
        return re.findall(r'@(\w+)', text)


# Singleton instance
linkedin_service = LinkedInService()
