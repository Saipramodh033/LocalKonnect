"""
Google Gemini AI Integration

Provides AI capabilities for:
- Contractor onboarding assistance
- Review sentiment analysis and summarization
- Fraud pattern detection
"""

import google.generativeai as genai
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    logger.warning("Gemini API key not configured")
    model = None


def analyze_sentiment(review_text):
    """
    Analyze sentiment of review text.
    
    Args:
        review_text: Review text to analyze
    
    Returns:
        dict: {
            'score': float (-1 to 1),
            'summary': str,
            'themes': list
        }
    """
    if not model:
        return {'score': 0.0, 'summary': '', 'themes': []}
    
    try:
        prompt = f"""
        Analyze the sentiment of this contractor review and provide:
        1. Sentiment score (-1 for very negative, 0 for neutral, 1 for very positive)
        2. A brief one-sentence summary
        3. Key themes mentioned (as a list)
        
        Review: "{review_text}"
        
        Respond in JSON format:
        {{
            "score": <float>,
            "summary": "<string>",
            "themes": [<list of strings>]
        }}
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {'score': 0.0, 'summary': '', 'themes': []}


def summarize_reviews(reviews_text_list):
    """
    Summarize multiple reviews for a contractor service.
    
    Args:
        reviews_text_list: List of review texts
    
    Returns:
        dict: {
            'summary': str,
            'positive_highlights': list,
            'negative_highlights': list,
            'overall_sentiment': str
        }
    """
    if not model or not reviews_text_list:
        return {
            'summary': 'No reviews available',
            'positive_highlights': [],
            'negative_highlights': [],
            'overall_sentiment': 'neutral'
        }
    
    try:
        reviews_combined = "\n\n".join([f"Review {i+1}: {text}" for i, text in enumerate(reviews_text_list)])
        
        prompt = f"""
        Summarize these contractor reviews and extract key insights:
        
        {reviews_combined}
        
        Provide:
        1. Overall summary (2-3 sentences)
        2. Top 3 positive highlights
        3. Top 3 areas for improvement (if mentioned)
        4. Overall sentiment (positive/neutral/negative)
        
        Respond in JSON format:
        {{
            "summary": "<string>",
            "positive_highlights": [<list>],
            "negative_highlights": [<list>],
            "overall_sentiment": "<string>"
        }}
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        
        return result
    
    except Exception as e:
        logger.error(f"Error summarizing reviews: {e}")
        return {
            'summary': 'Error summarizing reviews',
            'positive_highlights': [],
            'negative_highlights': [],
            'overall_sentiment': 'neutral'
        }


def check_fraud_likelihood(feedback):
    """
    Check fraud likelihood for a feedback entry using AI.
    
    Args:
        feedback: Feedback instance
    
    Returns:
        dict: {
            'confidence': float (0-1),
            'reason': str,
            'evidence': dict
        }
    """
    if not model:
        return {'confidence': 0.0, 'reason': '', 'evidence': {}}
    
    try:
        # Gather context
        customer = feedback.customer
        service = feedback.contractor_service
        
        # Count recent trusts from this customer
        from apps.trust.models import Feedback
        recent_trusts = Feedback.objects.filter(
            customer=customer,
            created_at__gte=feedback.created_at
        ).count()
        
        context = f"""
        Customer: {customer.email}
        Account age: {(feedback.created_at - customer.created_at).days} days
        Total trusts given: {recent_trusts}
        Email verified: {customer.is_email_verified}
        Feedback text: "{feedback.text or 'N/A'}"
        Has verification proof: {feedback.is_verified}
        """
        
        prompt = f"""
        Analyze this trust mark for potential fraud indicators:
        
        {context}
        
        Consider:
        - New accounts giving multiple trusts quickly
        - Generic or suspicious review text
        - Lack of verification
        - Unusual patterns
        
        Provide fraud likelihood (0-1) and reasoning in JSON:
        {{
            "confidence": <float 0-1>,
            "reason": "<string>",
            "evidence": {{"key": "value"}}
        }}
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        
        return result
    
    except Exception as e:
        logger.error(f"Error checking fraud likelihood: {e}")
        return {'confidence': 0.0, 'reason': str(e), 'evidence': {}}


def contractor_onboarding_assistant(user_message, conversation_history=None):
    """
    AI assistant for contractor onboarding.
    
    Args:
        user_message: User's message
        conversation_history: List of previous messages
    
    Returns:
        str: AI response
    """
    if not model:
        return "AI assistant is not available at this time."
    
    try:
        context = """
        You are a helpful assistant for LocalKonnect, a platform connecting customers with trusted contractors.
        Help contractors:
        - Understand how to complete their profile
        - Choose service categories
        - Set their service area
        - Upload verification documents
        - Understand the trust scoring system
        
        Be friendly, concise, and helpful.
        """
        
        if conversation_history:
            history_text = "\n".join([
                f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}"
                for i, msg in enumerate(conversation_history)
            ])
            full_prompt = f"{context}\n\nConversation:\n{history_text}\n\nUser: {user_message}\n\nAssistant:"
        else:
            full_prompt = f"{context}\n\nUser: {user_message}\n\nAssistant:"
        
        response = model.generate_content(full_prompt)
        return response.text
    
    except Exception as e:
        logger.error(f"Error in onboarding assistant: {e}")
        return "I'm having trouble processing your request. Please try again."


def detect_review_manipulation_patterns(reviews_data):
    """
    Detect manipulation patterns across multiple reviews.
    
    Args:
        reviews_data: List of review dictionaries
    
    Returns:
        dict: Detected patterns and confidence
    """
    if not model or not reviews_data:
        return {'patterns': [], 'confidence': 0.0}
    
    try:
        reviews_text = json.dumps(reviews_data, indent=2)
        
        prompt = f"""
        Analyze these reviews for manipulation patterns:
        
        {reviews_text}
        
        Look for:
        - Repetitive language or phrases
        - Unnatural writing patterns
        - Coordinated timing
        - Similar IP addresses or users
        
        Respond in JSON:
        {{
            "patterns": [<list of detected patterns>],
            "confidence": <float 0-1>,
            "explanation": "<string>"
        }}
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        
        return result
    
    except Exception as e:
        logger.error(f"Error detecting manipulation patterns: {e}")
        return {'patterns': [], 'confidence': 0.0, 'explanation': str(e)}
