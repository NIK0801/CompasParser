from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from django.utils import timezone
import time
import feedparser
import requests
from django.core.cache import cache

# Modify the parse_news_from_source function
def parse_news_from_source(source_url, start_date=None, end_date=None): 
    cache_key = f'rss_{source_url}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    news_list = []
   
    try:
        rss_feed = feedparser.parse(source_url)
        for entry in rss_feed.entries:
            published_time_struct = entry.published_parsed
            published_datetime = datetime.fromtimestamp(time.mktime(published_time_struct))
            published_datetime = timezone.make_aware(published_datetime, timezone.utc)         

            # Check if the date falls within the specified date range
            if (not start_date or start_date <= published_datetime) and (not end_date or published_datetime <= end_date):
                #print(entry.description)
                try:
                    news_item = {
                        'title': entry.title[:200],
                        'content': entry.description,
                        'date_published': published_datetime,
                        'link': entry.link,
                    }
                except:
                    news_item = {
                        'title': entry.title[:200],
                        'content': entry.title[:200],
                        'date_published': published_datetime,
                        'link': entry.link,
                    }
                news_list.append(news_item)
    except Exception as e:
        print(f"Error while parsing news from {source_url}: {e}")
        
    cache.set(cache_key, news_list, timeout=3600)  # Cache for 1 hour
    return news_list    
