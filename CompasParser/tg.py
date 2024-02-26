from .models import NewsSource
import re
from telethon.sync import TelegramClient
from telethon.tl import functions, types
from datetime import datetime
import asyncio


def extract_channel_name(url):
    # Извлечение имени канала из URL
    match = re.search(r'https://t.me(/s)?/([A-Za-z0-9_]+)', url)
    if match:   
        return match.group(2)
    else:
        return None

async def telegram(api_id, api_hash, phone, channel_url, start_date=None, end_date=None):
    # Извлечение имени канала из URL
    channel_username = extract_channel_name(channel_url)
    print(channel_username)
    if not channel_username:
        print("Invalid channel URL")
        return

    # Инициализация клиента Telegram с номером телефона
    client = TelegramClient(phone, api_id, api_hash)
    await client.start()
    # Ensure the connection is still alive
    if not client.is_connected():
        await client.connect()

    async with client:
        posts = []
        # Получение информации о канале
        entity = await client.get_entity(channel_username)
        
        if isinstance(entity, types.Channel):
            async for message in client.iter_messages(entity, limit=None):
                if isinstance(message, types.Message) and message.date:
                    post_date = message.date
                    # Проверка на дату, чтобы собирать только посты в заданном временном диапазоне
                    if (not start_date or start_date <= post_date) and (not end_date or post_date <= end_date):
                        
                        #print(post_date)
                        group_title = entity.title
                        participants = entity.participants_count
                        print(group_title)
                        # Подготовка данных о посте
                        if message.reactions:
                            reactions = message.reactions.results
                            count_reactions = sum(reaction.count for reaction in reactions)
                        else:
                            count_reactions = 0

                        if message.replies:
                            replies = message.replies.replies
                        else:
                            replies = 0

                        post_data = {
                            'channel_username': channel_username,
                            'group_url': channel_url,
                            'group_title': group_title,
                            'participants': participants,
                            'title': message.text[:50] + '...',
                            'content': message.text,
                            'date_published': post_date,
                            'link': f"https://t.me/{channel_username}/{message.id}",
                            'views': message.views,
                            'comments': replies,
                            'total_reactions': count_reactions
                        }
                        posts.append(post_data)
                    else:
                        break
        print("Finished parsing the channel")
    return posts
