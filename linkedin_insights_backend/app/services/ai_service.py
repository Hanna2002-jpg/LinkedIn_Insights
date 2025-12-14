"""
AI Service
Handles AI-powered analysis using OpenAI
"""
import openai
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from app.core.config import settings

class AIService:
    """Service for AI-powered analysis"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate_page_summary(
        self,
        page_data: Dict[str, Any],
        posts_data: List[Dict[str, Any]] = None,
        employees_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI summary for a LinkedIn page
        
        Args:
            page_data: Page information
            posts_data: List of recent posts
            employees_data: List of employees/followers
        
        Returns:
            AI-generated summary and insights
        """
        # Prepare context for the AI
        context = self._prepare_context(page_data, posts_data, employees_data)
        
        # Create the prompt
        prompt = self._create_analysis_prompt(context)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert LinkedIn analytics consultant. 
                        Analyze the provided company page data and generate insightful, 
                        actionable business intelligence. Focus on:
                        1. Company positioning and brand identity
                        2. Content strategy effectiveness
                        3. Audience engagement patterns
                        4. Industry benchmarking
                        5. Growth opportunities
                        
                        Provide your analysis in a structured JSON format."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the response
            analysis = json.loads(response.choices[0].message.content)
            
            return self._format_summary_response(page_data, analysis)
            
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            return self._generate_fallback_summary(page_data)
    
    def _prepare_context(
        self,
        page_data: Dict[str, Any],
        posts_data: List[Dict[str, Any]] = None,
        employees_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare context data for AI analysis"""
        context = {
            "page": {
                "name": page_data.get("name"),
                "industry": page_data.get("industry"),
                "description": page_data.get("description"),
                "follower_count": page_data.get("follower_count", 0),
                "employee_count": page_data.get("employee_count", 0),
                "company_size": page_data.get("company_size"),
                "specialties": page_data.get("specialties", []),
                "headquarters": page_data.get("headquarters"),
                "founded_year": page_data.get("founded_year"),
                "company_type": page_data.get("company_type")
            }
        }
        
        if posts_data:
            # Aggregate post metrics
            total_likes = sum(p.get("like_count", 0) for p in posts_data)
            total_comments = sum(p.get("comment_count", 0) for p in posts_data)
            total_shares = sum(p.get("share_count", 0) for p in posts_data)
            
            context["content"] = {
                "total_posts_analyzed": len(posts_data),
                "total_engagement": total_likes + total_comments + total_shares,
                "avg_likes": total_likes / len(posts_data) if posts_data else 0,
                "avg_comments": total_comments / len(posts_data) if posts_data else 0,
                "avg_shares": total_shares / len(posts_data) if posts_data else 0,
                "content_types": self._analyze_content_types(posts_data),
                "top_hashtags": self._get_top_hashtags(posts_data),
                "sample_posts": [
                    {"text": p.get("text", "")[:200], "engagement": p.get("like_count", 0)}
                    for p in sorted(posts_data, key=lambda x: x.get("like_count", 0), reverse=True)[:5]
                ]
            }
        
        if employees_data:
            context["employees"] = {
                "total_analyzed": len(employees_data),
                "top_titles": self._get_top_values([e.get("current_title") for e in employees_data]),
                "locations": self._get_top_values([e.get("location") for e in employees_data]),
                "industries": self._get_top_values([e.get("industry") for e in employees_data])
            }
        
        return context
    
    def _create_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create analysis prompt from context"""
        return f"""Analyze this LinkedIn company page data and provide insights:

Company Information:
{json.dumps(context.get('page', {}), indent=2)}

Content Performance (if available):
{json.dumps(context.get('content', {}), indent=2)}

Employee/Follower Data (if available):
{json.dumps(context.get('employees', {}), indent=2)}

Please provide your analysis in the following JSON structure:
{{
    "summary": "A 2-3 sentence executive summary of the company's LinkedIn presence",
    "page_type": "The type of company (startup/enterprise/agency/etc)",
    "industry_classification": "Refined industry classification",
    "key_insights": [
        {{"category": "Branding", "insight": "...", "confidence": 0.9}},
        {{"category": "Content", "insight": "...", "confidence": 0.85}},
        {{"category": "Engagement", "insight": "...", "confidence": 0.8}}
    ],
    "follower_analysis": {{
        "growth_trend": "growing/stable/declining",
        "engagement_rate": 0.05,
        "top_industries": ["tech", "finance"],
        "top_locations": ["USA", "India"]
    }},
    "content_analysis": {{
        "posting_frequency": "daily/weekly/monthly",
        "best_performing_topics": ["innovation", "culture"],
        "best_posting_times": ["Tuesday 10am", "Thursday 2pm"],
        "content_mix_recommendation": "..."
    }},
    "recommendations": [
        "Specific actionable recommendation 1",
        "Specific actionable recommendation 2",
        "Specific actionable recommendation 3"
    ]
}}"""
    
    def _format_summary_response(
        self, 
        page_data: Dict[str, Any], 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format the AI response into the expected structure"""
        return {
            "page_id": page_data.get("page_id"),
            "page_name": page_data.get("name"),
            "summary": analysis.get("summary", ""),
            "page_type": analysis.get("page_type", "unknown"),
            "industry_classification": analysis.get("industry_classification", page_data.get("industry", "")),
            "key_insights": analysis.get("key_insights", []),
            "follower_analysis": {
                "total_count": page_data.get("follower_count", 0),
                "growth_trend": analysis.get("follower_analysis", {}).get("growth_trend"),
                "engagement_rate": analysis.get("follower_analysis", {}).get("engagement_rate"),
                "top_industries": analysis.get("follower_analysis", {}).get("top_industries", []),
                "top_locations": analysis.get("follower_analysis", {}).get("top_locations", [])
            },
            "content_analysis": {
                "total_posts": len(page_data.get("posts", [])) if page_data.get("posts") else 0,
                "avg_likes": 0,
                "avg_comments": 0,
                "avg_shares": 0,
                "top_performing_topics": analysis.get("content_analysis", {}).get("best_performing_topics", []),
                "posting_frequency": analysis.get("content_analysis", {}).get("posting_frequency"),
                "best_posting_times": analysis.get("content_analysis", {}).get("best_posting_times", [])
            },
            "recommendations": analysis.get("recommendations", []),
            "generated_at": datetime.now()
        }
    
    def _generate_fallback_summary(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic summary when AI fails"""
        return {
            "page_id": page_data.get("page_id"),
            "page_name": page_data.get("name"),
            "summary": f"{page_data.get('name')} is a {page_data.get('industry', 'company')} with {page_data.get('follower_count', 0):,} followers on LinkedIn.",
            "page_type": "company",
            "industry_classification": page_data.get("industry", ""),
            "key_insights": [],
            "follower_analysis": {
                "total_count": page_data.get("follower_count", 0),
                "growth_trend": None,
                "engagement_rate": None,
                "top_industries": [],
                "top_locations": []
            },
            "content_analysis": {
                "total_posts": 0,
                "avg_likes": 0,
                "avg_comments": 0,
                "avg_shares": 0,
                "top_performing_topics": [],
                "posting_frequency": None,
                "best_posting_times": []
            },
            "recommendations": [
                "Consider posting more regularly to increase engagement",
                "Engage with your audience by responding to comments",
                "Share industry insights to establish thought leadership"
            ],
            "generated_at": datetime.now()
        }
    
    def _analyze_content_types(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze content type distribution"""
        types = {}
        for post in posts:
            content_type = post.get("content_type", "text")
            types[content_type] = types.get(content_type, 0) + 1
        return types
    
    def _get_top_hashtags(self, posts: List[Dict[str, Any]], limit: int = 10) -> List[str]:
        """Get most used hashtags"""
        hashtag_counts = {}
        for post in posts:
            for tag in post.get("hashtags", []):
                hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        
        sorted_tags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, count in sorted_tags[:limit]]
    
    def _get_top_values(self, values: List[Optional[str]], limit: int = 5) -> List[str]:
        """Get most common values from a list"""
        counts = {}
        for value in values:
            if value:
                counts[value] = counts.get(value, 0) + 1
        
        sorted_values = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [v for v, c in sorted_values[:limit]]


# Singleton instance
ai_service = AIService()
