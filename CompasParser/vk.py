from datetime import datetime, timedelta
import vk_api
from vk_api.exceptions import ApiError
import re
from django.contrib.auth.models import User
from .models import SocialData, NewsSource, ParsedNews
import requests
from django.utils import timezone
import pytz
import time
from django.db.models import Q
# Функция для извлечения числового идентификатора группы из URL
def extract_group_id_from_url(url):
    url = str(url)
    match = re.match(r'https://vk.com/([^/?]+)', url)
    if match:
        group_screen_name = match.group(1)
        return group_screen_name
    return None

# Функция для разрешения screen_name в числовой идентификатор
def resolve_screen_name(vk, screen_name):
    if re.match(r'^-?\d+$', screen_name):
        return str(screen_name)

    response = vk.utils.resolveScreenName(screen_name=screen_name)
    if response and 'object_id' in response:
        return str(response['object_id'])
    return None


# Функция для парсинга группы VK
def parse_vk_group(user, token, group_url, start_date=None, end_date=None):
    version = '5.131'  # Версия VK API

    # Авторизация в VK API
    vk_session = vk_api.VkApi(token=token, api_version=version)
    vk = vk_session.get_api()
    posts = []
    
    try:
        group_screen_name = extract_group_id_from_url(group_url)
        if group_screen_name:
            group_id = resolve_screen_name(vk, group_screen_name)

            if group_id is not None:
                group_id = int(group_id)
                
                print(group_screen_name)
                # if not group_screen_name.endswith("/"):
                #     group_screen_name += "/"
                news_source = NewsSource.objects.filter(
                    Q(url=f"https://vk.com/{group_screen_name}") | Q(url=f"https://vk.com/{group_screen_name}/")).first()
                #print(news_source)
                group_info = vk.groups.getById(group_ids=group_id, fields='members_count, name')[0]
                
                if 'members_count' in group_info and news_source:
                    
                    subscribers_count = group_info['members_count']
                    name = group_info['name']
                    
                    news_source.owner = group_id
                    news_source.name = name
                    news_source.members_count = subscribers_count
                    news_source.save()
                else:
                    news_source.selected = False
                    news_source.save()
                    return posts
                    
                wall_count = 100
                flag = 0 # на случай, если в сообществе есть закрепленная запись старше самой новой записи на стене, потому что парсер начинает с нее и не парсит дальше, если эта дата не входит в диапазон
                for offset in range(0, 10000, wall_count):  # Adjust the range as needed
                    wall = vk.wall.get(
                        owner_id='-' + str(group_id),
                        count=wall_count,
                        offset=offset
                    )

                    if not wall['items']:
                        break  # Exit if no more posts are available

                        
                    flag = 0  # флаг для подсчета количества постов, удовлетворяющих условию
                    for post in wall['items']:
                        post_date = datetime.fromtimestamp(post['date'], tz=pytz.utc)
                        if start_date and post_date < start_date:
                            flag += 1  # Увеличиваем счетчик постов, чья дата меньше start_date
                            if flag >= 2:
                            # Возвращаем список постов, если обнаружены два подряд поста с датами меньше start_date
                                return posts
                        elif end_date and post_date > end_date:
                            continue  # Пропускаем пост, если его дата больше чем end_date
                        else:
                            flag = 0  # Сбрасываем счетчик, если текущий пост не удовлетворяет условиям

#                     for post in wall['items']:
#                         post_date = datetime.fromtimestamp(post['date'], tz=pytz.utc)
#                         print(post_date)
#                         if end_date and post_date > end_date:
#                             continue  # Skip the post if it's beyond the end_date

#                         if start_date and post_date < start_date:
#                             flag += 1  # Увеличиваем счетчик постов, чья дата меньше start_date
#                             if flag >= 2:
#                                 # Возвращаем список постов, если обнаружены два подряд поста с датами меньше start_date
#                                 return posts
#                             else:
#                                 continue

                        likes_count = post['likes']['count'] if 'likes' in post else 0
                        comments_count = post['comments']['count'] if 'comments' in post else 0
                        views_count = post['views']['count'] if 'views' in post else 0
                        reposts_count = post['reposts']['count'] if 'reposts' in post else 0

                        post_data = {
                            'title': post['text'][:50] + '...',
                            'content': post['text'],
                            'date_published': post_date,
                            'link': f"https://vk.com/{group_screen_name}?w=wall-{group_id}_{post['id']}",
                            'likes': likes_count,
                            'comments': comments_count,
                            'views': views_count,
                            'reposts': reposts_count,
                        }
                        
                        posts.append(post_data)
                        #print(posts)
    except ApiError as e:
        print(f"Error fetching data for group {group_screen_name}: {e}")

    return posts