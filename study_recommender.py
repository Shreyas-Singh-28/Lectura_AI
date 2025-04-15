# study_recommender.py (modified)
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
    return re.sub(r'#\w+\s*', '', title).strip()

def extract_keywords(text: str) -> List[str]:
    try:
        kw_model = KeyBERT()
        keywords = kw_model.extract_keywords(
            text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5
        )
        return [kw[0] for kw in keywords]
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []

def search_youtube(keyword: str) -> List[Dict[str, str]]:
    if not YOUTUBE_API_KEY:
        return []
    
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                'part': 'snippet',
                'q': f"{keyword} tutorial",
                'key': YOUTUBE_API_KEY,
                'maxResults': 7,
                'type': 'video'
            },
            timeout=10
        )
        return [{
            'title': clean_title(item['snippet']['title']),
            'url': f"https://youtube.com/watch?v={item['id']['videoId']}",
            'type': 'youtube'
        } for item in response.json().get('items', []) if item['id'].get('videoId')]
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        return []

def search_wikipedia(keyword: str) -> List[Dict[str, str]]:
    try:
        return [{
            'title': result,
            'url': f"https://en.wikipedia.org/wiki/{result.replace(' ', '_')}",
            'type': 'wikipedia'
        } for result in wikipedia.search(keyword)[:7]]
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
        return []

def get_khan_academy_links(keyword: str) -> List[Dict[str, str]]:
    return [{
        'title': f"{keyword} (Khan Academy)",
        'url': f"https://www.khanacademy.org/search?referer=%2F&page_search_query={keyword.replace(' ', '+')}",
        'type': 'khan_academy'
    } for _ in range(5)]

def generate_recommendations(text: str) -> Dict[str, List[Dict[str, str]]]:
    keywords = extract_keywords(text)
    recommendations = {
        'youtube': [],
        'wikipedia': [],
        'khan_academy': []
    }
    
    for keyword in keywords:
        recommendations['youtube'].extend(search_youtube(keyword))
        recommendations['wikipedia'].extend(search_wikipedia(keyword))
        recommendations['khan_academy'].extend(get_khan_academy_links(keyword))
    
    # Remove duplicates
    for category in recommendations:
        seen = set()
        recommendations[category] = [x for x in recommendations[category] 
            if not (x['url'] in seen or seen.add(x['url']))]
    
    return recommendations