# study_recommender.py
from keybert import KeyBERT
import requests
import wikipedia
import os
import re
from dotenv import load_dotenv
import logging
from typing import Dict, List
import cleanup

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_title(title: str) -> str:
    """Remove hashtags and clean whitespace from titles"""
    return re.sub(r'#\w+\s*', '', title).strip()

def extract_keywords(text: str) -> List[str]:
    """Extract and display top keywords using KeyBERT"""
    try:
        print("\n🔍 Extracting keywords...")
        kw_model = KeyBERT()
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=5
        )
        extracted_keywords = [kw[0] for kw in keywords]
        
        # Display keywords in terminal
        print("✅ Extracted Keywords:")
        for idx, keyword in enumerate(extracted_keywords, 1):
            print(f"   {idx}. {keyword}")
            
        return extracted_keywords
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        print("❌ Keyword extraction failed")
        return []

def search_youtube(keyword: str) -> List[Dict[str, str]]:
    """Search YouTube with progress indication"""
    if not YOUTUBE_API_KEY:
        print("⚠️ YouTube API key missing - skipping YouTube search")
        return []
    
    try:
        print(f"   Searching YouTube for: '{keyword}'...", end="", flush=True)
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                'part': 'snippet',
                'q': f"{keyword} tutorial",
                'key': YOUTUBE_API_KEY,
                'maxResults': 7,
                'type': 'video',
                'relevanceLanguage': 'en'
            },
            timeout=15
        )
        results = [{
            'title': clean_title(item['snippet']['title']),
            'url': f"https://youtube.com/watch?v={item['id']['videoId']}",
            'type': 'youtube'
        } for item in response.json().get('items', []) if item['id'].get('videoId')]
        
        print(f" found {len(results)} videos")
        return results
        
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        print(f"❌ YouTube search failed for '{keyword}'")
        return []

def search_wikipedia(keyword: str) -> List[Dict[str, str]]:
    """Search Wikipedia with progress indication"""
    try:
        print(f"   Searching Wikipedia for: '{keyword}'...", end="", flush=True)
        results = [{
            'title': result,
            'url': f"https://en.wikipedia.org/wiki/{result.replace(' ', '_')}",
            'type': 'wikipedia'
        } for result in wikipedia.search(keyword)[:7]]
        
        print(f" found {len(results)} articles")
        return results
        
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
        print(f"❌ Wikipedia search failed for '{keyword}'")
        return []

def get_khan_academy_links(keyword: str) -> List[Dict[str, str]]:
    """Generate Khan Academy links with progress indication"""
    print(f"   Generating Khan Academy links for: '{keyword}'...", end="", flush=True)
    results = [{
        'title': f"{keyword} (Khan Academy)",
        'url': f"https://www.khanacademy.org/search?referer=%2F&page_search_query={keyword.replace(' ', '+')}",
        'type': 'khan_academy'
    } for _ in range(5)]
    
    print(f" generated {len(results)} links")
    return results

def generate_recommendations(text: str) -> Dict[str, List[Dict[str, str]]]:
    """Main function with enhanced progress tracking"""
    print("\n🌟 Starting recommendation generation")
    print("=================================")
    
    keywords = extract_keywords(text)
    if not keywords:
        print("⛔ No keywords extracted - cannot generate recommendations")
        return {'youtube': [], 'wikipedia': [], 'khan_academy': []}
    
    recommendations = {
        'youtube': [],
        'wikipedia': [],
        'khan_academy': []
    }
    
    # Process each keyword
    for keyword in keywords:
        recommendations['youtube'].extend(search_youtube(keyword))
        recommendations['wikipedia'].extend(search_wikipedia(keyword))
        recommendations['khan_academy'].extend(get_khan_academy_links(keyword))
    
    # Remove duplicates
    for category in recommendations:
        seen = set()
        recommendations[category] = [x for x in recommendations[category] 
            if not (x['url'] in seen or seen.add(x['url']))]
    
    # Final summary
    print("\n📊 Recommendation Results:")
    print(f"   YouTube Videos: {len(recommendations['youtube'])}")
    print(f"   Wikipedia Articles: {len(recommendations['wikipedia'])}")
    print(f"   Khan Academy Links: {len(recommendations['khan_academy'])}")
    print("=================================")
    print("✅ Recommendation generation complete\n")
    
    return recommendations