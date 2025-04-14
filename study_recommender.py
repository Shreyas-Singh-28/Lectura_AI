from keybert import KeyBERT
import requests
import wikipedia
import os
import re
from dotenv import load_dotenv
import logging
from typing import Dict, List

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_title(title: str) -> str:
    """Remove hashtags and clean whitespace from titles"""
    return re.sub(r'#\w+\s*', '', title).strip()

def extract_keywords(text: str) -> List[str]:
    """Extract top keywords using KeyBERT"""
    try:
        kw_model = KeyBERT()
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=5
        )
        return [kw[0] for kw in keywords]
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []

def search_youtube(keyword: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search YouTube for educational content"""
    if not YOUTUBE_API_KEY:
        logger.error("YouTube API key missing")
        return []
    
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                'part': 'snippet',
                'q': f"{keyword} tutorial",
                'key': YOUTUBE_API_KEY,
                'maxResults': max_results,
                'type': 'video',
                'relevanceLanguage': 'en',
                'videoDuration': 'medium'
            },
            timeout=10
        )
        if response.status_code == 200:
            return [{
                'title': clean_title(item['snippet']['title']),
                'url': f"https://youtube.com/watch?v={item['id']['videoId']}",
                'source': 'YouTube'
            } for item in response.json().get('items', [])]
        logger.error(f"YouTube API error: {response.status_code}")
        return []
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        return []

def search_wikipedia(keyword: str) -> List[Dict[str, str]]:
    """Search Wikipedia for relevant articles"""
    try:
        results = []
        search_results = wikipedia.search(keyword)[:3]
        
        for result in search_results:
            try:
                page = wikipedia.page(result, auto_suggest=False)
                results.append({
                    'title': page.title,
                    'url': page.url,
                    'source': 'Wikipedia'
                })
            except wikipedia.DisambiguationError:
                results.append({
                    'title': result,
                    'url': f"https://en.wikipedia.org/wiki/{result.replace(' ', '_')}",
                    'source': 'Wikipedia'
                })
            except wikipedia.PageError:
                continue
        return results
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
        return []

def get_khan_academy_links(keyword: str) -> List[Dict[str, str]]:
    """Generate Khan Academy search links"""
    return [{
        'title': f"{keyword} (Khan Academy)",
        'url': f"https://www.khanacademy.org/search?referer=%2F&page_search_query={keyword.replace(' ', '+')}",
        'source': 'Khan Academy'
    }]

def generate_recommendations(text: str) -> str:
    """Main function to generate formatted recommendations"""
    keywords = extract_keywords(text)
    logger.info(f"Extracted keywords: {keywords}")
    
    if not keywords:
        return "No key concepts could be extracted from the text."
    
    # Get recommendations from all sources
    recommendations = []
    
    for keyword in keywords:
        # YouTube videos
        for video in search_youtube(keyword):
            recommendations.append(f"🎥 {video['title']}\n   {video['url']}")
        
        # Wikipedia articles
        for article in search_wikipedia(keyword):
            recommendations.append(f"📚 {article['title']}\n   {article['url']}")
        
        # Khan Academy links
        for link in get_khan_academy_links(keyword):
            recommendations.append(f"🏫 {link['title']}\n   {link['url']}")
    
    if not recommendations:
        return "No recommendations could be generated for the extracted concepts."
    
    # Format the output
    header = "Here are your personalized study recommendations:\n\n"
    keyword_header = f"Based on key concepts: {', '.join(keywords)}\n\n"
    recommendations_str = "\n\n".join(recommendations)
    
    return header + keyword_header + recommendations_str