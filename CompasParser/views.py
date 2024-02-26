from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta, date
import pandas as pd

from bs4 import BeautifulSoup
import feedparser
import requests



from django.urls import reverse

import random
import time
import json
import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

import asyncio
from asgiref.sync import sync_to_async


import pymorphy2

from .models import NewsSource, ParsedNews, KeywordBag, Parsers, SocialData
from .forms import AddNewsSourceForm, AddVKTelegramSourceForm, SocialDataForm

from .vk import parse_vk_group
from .rss import parse_news_from_source
from .tg import telegram


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.first_login:
                # Если это первый вход пользователя, перенаправьте его на страницу смены пароля
                user.first_login = False
                user.save()
                return redirect('change_password')
            else:
                return redirect('parsed_news')
        else:
            messages.error(request, 'Ошибка входа. Проверьте правильность учетных данных.')
        
    return render(request, 'login_page.html')

# функция для выхода
@login_required(login_url='/compasnews/login/')
def logout_view(request):
    logout(request)
    return redirect('login_page')

# функция смены пароля (сейчас не используется, тк идет аутентификация через некстклауд)
@login_required(login_url='/compasnews/login/')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if request.user.check_password(old_password) and new_password1 == new_password2:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep the user logged in
            messages.success(request, 'Пароль успешно изменен.')
            return redirect('parsed_news')
        else:
            messages.error(request, 'Ошибка смены пароля. Проверьте введенные данные.')

    return render(request, 'change_password.html')

# функция для добавления и управления учетными данными приложений ВК и ТГ
@login_required(login_url='/compasnews/login/')
def social_data_config(request):
    user = request.user
    try:
        social_data = SocialData.objects.get(user=user)
    except SocialData.DoesNotExist:
        social_data = SocialData(user=user)

    if request.method == 'POST':
        form = SocialDataForm(request.POST, instance=social_data)
        if form.is_valid():
            social_data = form.save(commit=False)
            # Получаем номер телефона из формы
            phone_number = form.cleaned_data.get('phone_number', None)
            if phone_number is not None:
                # Преобразовываем номер телефона в нужный формат, например: +XXXXXXXXXXX
                formatted_phone_number = '+' + ''.join(filter(str.isdigit, phone_number))
                social_data.phone_number = formatted_phone_number
            else:
                social_data.phone_number = None  # Если номер не введен, сохраняем его как None
            social_data.save()
            
            return redirect('social_data_config')
    else:
        form = SocialDataForm(instance=social_data)

    return render(request, 'social_data_config.html', {'form': form,
                                                       'social_data': social_data})

# Функция для отображения и изменения статуса Парсеров(активен\неактивен)
@login_required(login_url='/compasnews/login/')
def parsers_status(request):
    if request.method == "POST":
        # Handle form submission
        for parser in Parsers.objects.filter(user=request.user):
            parser_id = f"parser_{parser.id}"
            if parser_id in request.POST:
                parser.status = 1  # Assuming 1 represents "checked" status
            else:
                parser.status = 0  # Assuming 0 represents "unchecked" status
            parser.save()
    # Retrieve the list of parsers
    parsers = Parsers.objects.filter(user=request.user)

    return render(request, 'parsers_status.html', {'parsers': parsers})

# функция отображения и добавления новостных источников и валидации ссылок, где есть RSS
@login_required(login_url='/compasnews/login/')
def news_sources(request):
    user = request.user
    sources = NewsSource.objects.filter(user=user)
    try:
        social_data = SocialData.objects.get(user=user)
    except SocialData.DoesNotExist:
        social_data = SocialData(user=user)
    error_message = None

    # Pagination logic
    paginator = Paginator(sources, 10)  # Display 10 sources per page
    page = request.GET.get('page')
    sources = paginator.get_page(page)

    # Get a list of parsers
    parsers = Parsers.objects.filter(user=user)

    rss_form = AddNewsSourceForm()
    vk_telegram_form = AddVKTelegramSourceForm()
    success_message = ""
    error_message = ""
    if request.method == 'POST':
        if 'rss_submit' in request.POST:
            rss_form = AddNewsSourceForm(request.POST)
            if rss_form.is_valid():
                url = rss_form.cleaned_data['url']
                rss_url = rss_form.cleaned_data['rss_url']
                parser = rss_form.cleaned_data['parser']
                parser_id = parser.id
                parser = Parsers.objects.get(id=parser_id)
                
                if url:
                    # Check for duplicates based on the URL
                    if not NewsSource.objects.filter(user=user, url=url).exists():
                        try:
                            response = requests.get(url)
                            soup = BeautifulSoup(response.content, 'html.parser')
                            rss_links = []
                            source_name = 'Unknown Source'  # Default name if not found
                            for link_tag in soup.find_all('link', type='application/rss+xml'):
                                rss_links.append(link_tag.get('href'))
                                source_name = link_tag.get('title', source_name)
                            if rss_links:
                                NewsSource.objects.create(user=user, name=source_name, rss_url=rss_links[0], url=url, parser=parser)
                                success_message = "Источник успешно добавлен!"
                            else:
                                error_message = "На сайте не найдена RSS лента. Добавление невозможно. Можете попробовать найти ее сами и вставить ее URL в соответствующую строку для RSS."
                        except Exception as e:
                            error_message = f"Error URL: {str(e)}"
                    else:
                        error_message = "Источник с указанным URL уже существует!"

                elif rss_url:
                    # Check for duplicates based on the RSS URL
                    try:
                        rss_feed = feedparser.parse(rss_url)
                        print(rss_feed)
                        print(rss_feed.entries)
                        if 'title' in rss_feed.feed:
                            source_name = rss_feed.feed.title
                        elif 'title' in rss_feed.channel:
                            source_name = rss_feed.channel.title
                        else:
                            source_name = 'Unknown Source'
                            
                        if 'link' in rss_feed.feed:
                            source_link = rss_feed.feed.link
                        elif 'link' in rss_feed.channel:
                            source_link = rss_feed.channel.link
                        else:
                            source_link = None  
                        if not NewsSource.objects.filter(user=user, url=source_link).exists():
                            NewsSource.objects.create(user=user, name=source_name, rss_url=rss_url, url=source_link, parser=parser)
                            success_message = "Источник успешно добавлен!"
                        else:
                            error_message = "Источник с указанным URL уже существует!"
                    except Exception as e:
                        error_message = f"Ошибка анализа RSS-ленты: {str(e)}"
            
        elif 'vk_telegram_submit' in request.POST:
            vk_telegram_form = AddVKTelegramSourceForm(request.POST)
            if vk_telegram_form.is_valid():
                
                        
                parser = vk_telegram_form.cleaned_data['parser']
                url = vk_telegram_form.cleaned_data['url']
                owner = None
                if "https://vk.com" in url:

                    domain = re.match(r'https://vk.com/([^/?]+)', url)
                    if domain:
                        domain = domain.group(1)
                    response = requests.get('https://api.vk.com/method/groups.getById?',
                                params={'access_token' : social_data.vk_app_token,
                                        'v' : 5.131,
                                        'group_ids' : domain,
                                        'fields': 'description, members_count'}
                                   )
                    data = response.json()['response']
                    owner = data[0]['id']              
                
                if "https://web.telegram.org" in url:
                    # Ищем часть URL, содержащую имя канала
                    match = re.search(r'https://web\.telegram\.org/k/#@(.+)', url)
                    if match:
                        channel_name = match.group(1)
                        # Создаем новый URL
                        url = f"https://t.me/{channel_name}"
                        url = url.replace("t.me/s/", "t.me/")  # Убираем "s/" (если есть)
                        domain = re.match(r'https://t.me/([^/?]+)', url)
                        if domain:
                            domain = domain.group(1)
                
                if "https://t.me" in url:
                    url = url.replace("t.me/s/", "t.me/")  # Убираем "s/" (если есть)
                    domain = re.match(r'https://t.me/([^/?]+)', url)
                    if domain:
                        domain = domain.group(1)
                    
                parser_id = parser.id
                parser = Parsers.objects.get(id=parser_id)
                # Check for duplicates based on the URL
                
                if not NewsSource.objects.filter(user=user, url=url).exists():
                    NewsSource.objects.create(user=user, url=url, parser=parser, owner=owner)
                    success_message = "Источник успешно добавлен!"
                else:
                    error_message = "Источник с указанным URL уже существует!"

    return render(request, 'news_sources.html', {'sources': sources,
                                                 'rss_form': rss_form,
                                                 'vk_telegram_form': vk_telegram_form,
                                                 'error_message': error_message,
                                                 'success_message': success_message,
                                                 'parsers': parsers})

# функция для включения и отключения новостных источников
@login_required(login_url='/compasnews/login/')
def manage_news_sources(request):
    user = request.user
    if request.method == 'POST':       
        selected_source_ids = request.POST.getlist('selected_sources')
        unselected_sources = NewsSource.objects.filter(user=user).exclude(id__in=selected_source_ids)
        NewsSource.objects.filter(user=user, id__in=unselected_sources).update(selected=False)
        NewsSource.objects.filter(user=user, id__in=selected_source_ids).update(selected=True)
    sources = NewsSource.objects.filter(user=user)
    return render(request, 'manage_news_sources.html', {'sources': sources})

# функция для удаления новостных источников
@login_required(login_url='/compasnews/login/')
def delete_news_source(request, source_id):
    NewsSource.objects.filter(id=source_id, user=request.user).delete()
    return redirect('manage_news_sources')

# функция для управления ключевыми словами
@login_required(login_url='/compasnews/login/')
def manage_keyword_bags(request):
    user = request.user
    keyword_bag, created = KeywordBag.objects.get_or_create(user=user)
    if request.method == 'POST':
        bag1_words = request.POST.get('bag1', '').strip()
        bag2_words = request.POST.get('bag2', '').strip()
        bag_arch = request.POST.get('bag_arch', '').strip()
        # Уберите пробелы вокруг запятых в строках
        bag1_words = ','.join(word.strip() for word in bag1_words.split(','))
        bag2_words = ','.join(word.strip() for word in bag2_words.split(','))
        bag_arch = ','.join(word.strip() for word in bag_arch.split(','))
        
        keyword_bag.bag1 = bag1_words
        keyword_bag.bag2 = bag2_words
        keyword_bag.bag_arch = bag_arch
        keyword_bag.save()

    return render(request, 'manage_keyword_bags.html', {'keyword_bag': keyword_bag})

# функция для отображения и фильтрации новостей
@login_required(login_url='/compasnews/login/')
def parsed_news(request):
    user = request.user
    #search_query = request.GET.get('q')
    news = ParsedNews.objects.filter(user=user).order_by('-date_published')

    filter_start_date = request.GET.get('filter_start_date')
    filter_end_date = request.GET.get('filter_end_date')
    
    if filter_start_date:
        filter_start_date = datetime.strptime(filter_start_date, '%Y-%m-%d')
        filter_start_date = filter_start_date.replace(hour=0, minute=0, second=0)
    if filter_end_date:
        filter_end_date = datetime.strptime(filter_end_date, '%Y-%m-%d')
        filter_end_date = filter_end_date.replace(hour=23, minute=59, second=59)
    # Search query
    search_query = request.GET.get('q')
    
    if filter_start_date and filter_end_date:
        # Apply date filtering
        news = news.filter(date_published__range=(filter_start_date, filter_end_date))
    
    if search_query:
        
        # Создать экземпляр морфологического анализатора
        morph = pymorphy2.MorphAnalyzer()

        # Разбить строку поиска на отдельные слова
        search_words = re.split(r'\s+', search_query.strip())

        # Привести каждое слово к нормальной форме
        normalized_words = [morph.parse(word)[0].normal_form for word in search_words]

        # Создать список Q объектов для каждого слова и его нормальной формы
        q_objects = []
        for word, norm_word in zip(search_words, normalized_words):
            q_objects.append(
                Q(title__icontains=word) | Q(content__icontains=word) |
                Q(title__icontains=norm_word) | Q(content__icontains=norm_word)
            )

        # Комбинировать Q объекты с использованием логического ИЛИ
        combined_q_object = q_objects.pop()
        for q_obj in q_objects:
            combined_q_object &= q_obj

        # Применить фильтр с комбинированным Q объектом
        news = news.filter(combined_q_object)


    total_news_count = ParsedNews.objects.filter(user=user).count()
    # Get the page number from the query parameters
    page_number = request.GET.get('page')
    page_number = int(page_number) if page_number else 1

    # Create a Paginator with 100 items per page
    paginator = Paginator(news, 100)

    try:
        # Get the specified page
        news_page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        news_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page
        news_page = paginator.page(paginator.num_pages)

    start_date = request.POST.get('start_date', (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    end_date = request.POST.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    if request.method == 'POST':
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            start_date = start_date.replace(hour=0, minute=0, second=0)
            start_date = timezone.make_aware(start_date, timezone.utc)
            print(start_date)
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            end_date = timezone.make_aware(end_date, timezone.utc)
        
        trigger_parse_news(request, start_date, end_date)
        
        return HttpResponseRedirect(request.path_info)

    parsers = Parsers.objects.filter(user=user)

    return render(request, 'parsed_news.html', {'parsers': parsers,
                                                'news': news_page,
                                                'total_news_count': total_news_count,
                                                'filtered_news_count': paginator.count,
                                                'start_date': start_date,
                                                'end_date': end_date,
                                                'filter_start_date': filter_start_date.strftime('%Y-%m-%d') if filter_start_date else '',
                                                'filter_end_date': filter_end_date.strftime('%Y-%m-%d') if filter_end_date else '',
                                                'search_query': search_query,
                                               })

# функция запуска парсеров (добавится логика в зависимости от статуса парсеров, включен или нет)
@login_required(login_url='/compasnews/login/')
def trigger_parse_news(request, start_date, end_date):
    user = request.user

    # Получите все активные парсеры
    active_parsers = Parsers.objects.filter(user=user, status=True)


    for parser in active_parsers:
        parser_name = parser.name
        if parser_name == 'СайтыRSS':
            # Если это парсер RSS и статус True, выполните парсинг
            parse_rss(request, start_date, end_date)
        elif parser_name == 'ВКонтакте':
            # Если это парсер ВКонтакте и статус True, выполните парсинг
            parse_vk(request, start_date, end_date)
        elif parser_name == 'Телеграм':
            # Если это парсер Телеграм и статус True, выполните парсинг
            parse_tg(request, start_date, end_date)

    # После завершения парсинга всех парсеров, вы можете показать сообщение об успехе пользователю.
    messages.success(request, 'Сбор новостей успешно завершен.')
    # Перенаправьте пользователя обратно на страницу parsed_news.
    return redirect('parsed_news')

# функция для запуска функции парсинга с ВКонтакте и фльтрации и записи их в базу
@login_required(login_url='/compasnews/login/')
def parse_vk(request, start_date, end_date):
    user = request.user
    sources = NewsSource.objects.filter(user=user, parser__name="ВКонтакте", selected=True)
    
    print(sources)
    # Замените значениями параметры из вашей модели VK API (token, version)
    social_data = SocialData.objects.get(user=user)
    token = social_data.vk_app_token  # Получите токен из модели SocialData
 
    keyword_bag, created = KeywordBag.objects.get_or_create(user=user)
    keywords1 = keyword_bag.bag1.lower().split(',')
    keywords2 = keyword_bag.bag2.lower().split(',')

    for source in sources:
        news_list = parse_vk_group(user, token, source.url, start_date, end_date)
        filtered_news = filter_news_by_keywords(news_list, keywords1, keywords2)
        #print(news_list)
        for post in filtered_news:
            # Check if a news article with the same title and source already exists
            existing_news = ParsedNews.objects.filter(user=user, link=post['link']).first()
            if not existing_news:
                # If it doesn't exist, save the news article
                ParsedNews.objects.create(
                    user=user,
                    title=post['title'],
                    content=post['content'],
                    date_published=post['date_published'],
                    link=post['link'],
                    source=source,
                    comments=post['comments'],
                    likes=post['likes'],
                    reposts=post['reposts'],
                    views=post['views'],
                )
            else:
                existing_news.comments = post['comments']
                existing_news.likes = post['likes']
                existing_news.views = post['views']
                existing_news.save()

# функция для запуска функции парсинга с RSS и фльтрации и записи их в базу
@login_required(login_url='/compasnews/login/')
def parse_rss(request, start_date, end_date):
    user = request.user
    sources = NewsSource.objects.filter(user=user, parser__name='СайтыRSS', selected=True)
    keyword_bag, created = KeywordBag.objects.get_or_create(user=user)
    keywords1 = keyword_bag.bag1.lower().split(',')
    keywords2 = keyword_bag.bag2.lower().split(',')

    for source in sources:
        news_list = parse_news_from_source(source.rss_url, start_date, end_date)
        filtered_news = filter_news_by_keywords(news_list, keywords1, keywords2)

        for news_item in filtered_news:
            # Check if a news article with the same title and source already exists
            existing_news = ParsedNews.objects.filter(user=user, link=news_item['link'][:200]).first()

            if not existing_news:
                # If it doesn't exist, save the news article
                ParsedNews.objects.create(
                    user=user,
                    title=news_item['title'][:200],
                    content=news_item['content'],
                    date_published=news_item['date_published'],
                    link=news_item['link'][:200],
                    source=source,
                )

# функция для запуска функции парсинга с ВКонтакте и фльтрации и записи их в базу
@login_required(login_url='/compasnews/login/')
def parse_tg(request, start_date, end_date):
    user = request.user
    sources = NewsSource.objects.filter(user=user, parser__name="Телеграм", selected=True)
    
    print(sources)
    # Замените значениями параметры из вашей модели VK API (token, version)
    social_data = SocialData.objects.get(user=user)
    telegram_api_id = social_data.telegram_api_id  # Получите токен из модели SocialData
    telegram_api_hash = social_data.telegram_api_hash
    phone = social_data.phone_number
    keyword_bag, created = KeywordBag.objects.get_or_create(user=user)
    keywords1 = keyword_bag.bag1.lower().split(',')
    keywords2 = keyword_bag.bag2.lower().split(',')

    for source in sources:
        try:
            news_list = asyncio.run(telegram(telegram_api_id, telegram_api_hash, phone, source.url, start_date, end_date))
            # print(news_list)
            filtered_news = filter_news_by_keywords(news_list, keywords1, keywords2)

            for post in filtered_news:
            
                news_source = NewsSource.objects.filter(user=user, url=post['group_url']).first()

                domain = re.match(r'https://t.me/([^/?]+)', post['group_url'])
                if domain:
                    domain = domain.group(1)
                # Если запись уже существует, обновить информацию
                if news_source:
                    news_source.owner = domain
                    news_source.name = post['group_title']
                    news_source.members_count = post['participants']
                    news_source.save()
                
                # Check if a news article with the same title and source already exists
                existing_news = ParsedNews.objects.filter(user=user, link=post['link']).first()
           
                if not existing_news:
                    # If it doesn't exist, save the news article
                    ParsedNews.objects.create(
                    user=user,
                    title=post['title'],
                    content=post['content'],
                    date_published=post['date_published'],
                    link=post['link'],
                    source=source,
                    comments=post['comments'],
                    likes=post['total_reactions'],
                    #reposts=post['reposts'],
                    views=post['views'],
                )
                else:
                    existing_news.comments = post['comments']
                    existing_news.likes = post['total_reactions']
                    existing_news.views = views=post['views']
                    existing_news.save()
        except:
            source.selected = False
            source.save()
            continue


        time.sleep(random.uniform(0, 3))
                
# функция фильтрации новосетй по ключевым словам
def filter_news_by_keywords(news_list, keywords1, keywords2):
    filtered_news = []
    for news_item in news_list:
        title_words = news_item['title'].lower()
        content_words = news_item['content'].lower()
        
        # Check if the news item contains at least one word or phrase from keywords1 and keywords2
        contains_keywords1 = any(keyword in title_words or keyword in content_words for keyword in keywords1)
        contains_keywords2 = any(keyword in title_words or keyword in content_words for keyword in keywords2)

        if contains_keywords1 and contains_keywords2:
            filtered_news.append(news_item)
    return filtered_news

# функция шары в телеграм
@login_required(login_url='/compasnews/login/')
def share_telegram(request, news_id):
    news_item = get_object_or_404(ParsedNews, id=news_id)
    news_item.selected = True
    news_item.save()
    telegram_share_url = f"https://t.me/share/url?url={news_item.link}&text={news_item.title}"
    messages.success(request, 'Новость успешно отправлена в Телеграм!')
    return redirect(telegram_share_url)



@login_required(login_url='/compasnews/login/')
def delete_selected_news(request):
    user = request.user
    if request.method == 'POST':

        # Удалить все новости пользователя из базы данных
        ParsedNews.objects.filter(user=user).delete()

    return HttpResponseRedirect(reverse('parsed_news'))