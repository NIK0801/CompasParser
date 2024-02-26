from django.contrib import admin
from .models import NewsSource, ParsedNews, Parsers, SocialData, KeywordBag, EconomMonitoringOperatorRole, PressMonitoringOperatorRole


    
@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "parser", "url", "selected")
    list_filter = ("user", "parser", "selected")
    search_fields = ['name', 'url']# Добавляем поиск по полю "name"
    
    pass

@admin.register(ParsedNews)
class ParsedNewsAdmin(admin.ModelAdmin):
    list_display = ("user", "source", "title")
    list_filter = ("user",)
    pass

@admin.register(Parsers)
class ParsersAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "status")
    
    list_filter = ("user",)
    pass

@admin.register(SocialData)
class SocialDataAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number")
    list_filter = ("user",)
    pass

@admin.register(KeywordBag)
class KeywordBagAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user",)
    pass

@admin.register(EconomMonitoringOperatorRole)
class EconomMonitoringOperatorAdmin(admin.ModelAdmin):
    list_display = ['user']
    
@admin.register(PressMonitoringOperatorRole)
class PressMonitoringOperatorAdmin(admin.ModelAdmin):
    list_display = ['user']
# Register your models here.