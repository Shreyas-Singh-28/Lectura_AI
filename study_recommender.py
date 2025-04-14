from keybert import KeyBERT
import requests
import wikipedia
import os
import re
from dotenv import load_dotenv
import logging

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_title(title):
    return re.sub(r'#\w+\s*', '', title).strip()

def extract_keywords(text):
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

def search_youtube(keyword, max_results=3):
    if not YOUTUBE_API_KEY:
        logger.error("YouTube API key missing")
        return []
    
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                'part': 'snippet',
                'q': keyword,
                'key': YOUTUBE_API_KEY,
                'maxResults': max_results,
                'type': 'video',
                'relevanceLanguage': 'en'
            },
            timeout=10
        )
        if response.status_code == 200:
            return [{
                'title': clean_title(item['snippet']['title']),
                'url': f"https://youtube.com/watch?v={item['id']['videoId']}"
            } for item in response.json().get('items', [])]
        logger.error(f"YouTube API error: {response.status_code}")
        return []
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        return []

def search_wikipedia(keyword):
    try:
        results = []
        search_results = wikipedia.search(keyword)[:3]
        
        for result in search_results:
            try:
                page = wikipedia.page(result, auto_suggest=False)
                results.append({
                    'title': page.title,
                    'url': page.url
                })
            except wikipedia.DisambiguationError:
                results.append({
                    'title': result,
                    'url': f"https://en.wikipedia.org/wiki/{result.replace(' ', '_')}"
                })
            except wikipedia.PageError:
                continue
        return results
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
        return []

def get_khan_academy_links(keyword):
    return [{
        'title': f"Khan Academy: {keyword}",
        'url': f"https://www.khanacademy.org/search?referer=%2F&page_search_query={keyword.replace(' ', '+')}"
    }]

def process_text(text):
    keywords = extract_keywords(text)
    logger.info(f"Extracted keywords: {keywords}")
    
    recommendations = {
        'youtube': {},
        'wikipedia': {},
        'khan': {}
    }
    
    for keyword in keywords:
        for video in search_youtube(keyword):
            recommendations['youtube'][video['url']] = video
        
        for page in search_wikipedia(keyword):
            recommendations['wikipedia'][page['url']] = page
        
        for link in get_khan_academy_links(keyword):
            recommendations['khan'][link['url']] = link
    
    return {
        'youtube': list(recommendations['youtube'].values()),
        'wikipedia': list(recommendations['wikipedia'].values()),
        'khan': list(recommendations['khan'].values())
    }
