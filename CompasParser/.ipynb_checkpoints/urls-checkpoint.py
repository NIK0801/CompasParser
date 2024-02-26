from django.urls import include, path
from . import views
from . import export
#from django.contrib.auth import views as auth_views

from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

from allauth.utils import import_attribute

login_view = import_attribute("allauth.socialaccount.providers.nextcloud.views.oauth2_login")

urlpatterns = [
    path('login/', views.login_page, name='login_page'),
    path('login_redirect/', login_view),
    path('accounts/', include('allauth.urls')),
    path('change_password/', views.change_password, name='change_password'),
    #path('search_news/', views.search_news, name='search_news'),
    #path('add_news_source/', views.add_news_source, name='add_news_source'),
    path('parsers_status/', views.parsers_status, name='parsers_status'),
    path('social_data_config/', views.social_data_config, name='social_data_config'),
    path('delete_news_source/<int:source_id>/', views.delete_news_source, name='delete_news_source'),
    path('parsed_news/', views.parsed_news, name='parsed_news'),
    path('logout/', views.logout_view, name='logout'),
    #path('parse_news/', views.parse_and_show_news, name='parse_and_show_news'),
    path('manage_keyword_bags/', views.manage_keyword_bags, name='manage_keyword_bags'),
    path('trigger_parse_news/', views.trigger_parse_news, name='trigger_parse_news'),
    path('news_sources/', views.news_sources, name='news_sources'),
    path('manage_news_sources/', views.manage_news_sources, name='manage_news_sources'),
    path('share_telegram/<int:news_id>/', views.share_telegram, name='share_telegram'),
    path('export_to_excel/', export.export_to_excel, name='export_to_excel'),
    path('export_to_word/', export.export_to_word, name='export_to_word'),
    path('delete_selected_news/', views.delete_selected_news, name='delete_selected_news'),
    path('', views.parsed_news),
]
