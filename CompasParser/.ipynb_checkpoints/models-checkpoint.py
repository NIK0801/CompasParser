from django.db import models
from django.contrib.auth.models import User



User.add_to_class('first_login', models.BooleanField(default=True))


class EconomMonitoringOperatorRole(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        permissions = [('can_export_to_word', 'Can export data to Word')]
        verbose_name = 'РОЛЬ_ОПЕРАТОР_ЭКОНОМ'
        verbose_name_plural = 'РОЛЬ_ОПЕРАТОР_ЭКОНОМ'

class PressMonitoringOperatorRole(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        permissions = [('can_export_to_excel', 'Can export data to Excel')]
        verbose_name = 'РОЛЬ_ОПЕРАТОР_СМИ'
        verbose_name_plural = 'РОЛЬ_ОПЕРАТОР_СМИ'
        

class Parsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    name = models.TextField()
    status = models.IntegerField()
    
    class Meta:
        verbose_name = 'Парсеры пользователей'
        verbose_name_plural = 'Парсеры пользователей'
        
    def __str__(self):
        return f"{self.user.username} парсер {self.name}"

class SocialData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    vk_app_token = models.CharField(max_length=150, blank=True, null=True)
    vk_app_id = models.CharField(max_length=150, blank=True, null=True)
    vk_app_secret = models.CharField(max_length=150, blank=True, null=True)
    telegram_api_id = models.CharField(max_length=150, blank=True, null=True)
    telegram_api_hash = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=18, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Данные приложений'
        verbose_name_plural = 'Данные приложений'
    def __str__(self):
        return f"Данные приложений пользователя {self.user.username}"
    
class NewsSource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parser = models.ForeignKey(Parsers, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=200, null=True, blank=True)
    # ссылка на rss-канал для новостных сайтов
    rss_url = models.URLField(null=True, blank=True)
    
    url = models.URLField()
    members_count = models.IntegerField(null=True, blank=True)

    owner = models.CharField(blank=True, null=True)
    selected = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Источники СМИ'
        verbose_name_plural = 'Источники СМИ'
        
    def __str__(self):
        return self.url

class ParsedNews(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_published = models.DateTimeField()
    
    # ссылка на источник
    link = models.URLField()
    likes = models.IntegerField(blank=True, null=True)
    reposts = models.IntegerField(blank=True, null=True)
    likes = models.IntegerField(blank=True, null=True)
    views = models.IntegerField(blank=True, null=True)
    comments = models.IntegerField(blank=True, null=True)
    selected = models.BooleanField(default=False)

    
    class Meta:
        verbose_name = 'Новости'
        verbose_name_plural = 'Весь пулл новостей'
        
    def __str__(self):
        return self.title


# class ParsedNewsIndex(Document):
#     title = Text()
#     content = Text()
#     date_published = Date()

#     class Index:
#         name = 'parsednews_index'
        
        
# class Comments(models.Model):
#     date = models.DateTimeField()
#     count = models.IntegerField()
#     text = models.TextField()
#     news = models.ForeignKey(ParsedNews, on_delete=models.CASCADE)
    
#     def __str__(self):
#         return self.title
    
class KeywordBag(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='keyword_bag')
    bag1 = models.TextField(default="Банк России,ЦБ,Центральный банк,мегарегулятор,министр,министер,финанс,Нацбанк,мошенн,Сбер,льгот,рублей,Отделение-НБ,Волго-Вятское ГУ,Волго-Вятское главное управление,Экономика,бизнес,ОСАГО,эскроу,мошенничество,мошенники,финансы,финансовый рынок,МФО,микрофинансирование,ESG,фальшивка,подделка,деньги,финансы,кредит,заем,вклад,депозит,инфляция,инфляционные ожидания,цены,банкомат,инкассатор,инкассация,банковские карты,банк,платежные карты,платежи,платежей,СБП,система быстрых платежей,реструктуризация,меры поддержки,финансовая грамотность,доклад,Региональная экономика,управляющий,страхование,инвестиции,ценные бумаги,безнал,безналичная оплата,ипотека,ИЖК,фондовый рынок,киберграмотность,выставка Банка России,памятные банкноты,монеты,подлинность,индивидуальные инвестиционные счета,инвестсчета,ломбард,нелегал,нелегальный,участник,финпирамида,финансовая пирамида,онлайн-уроки,дольщики,банкноты,купюры,ДКП,денежно-кредитная политика,НСПК,национальная платежная система,недобросовестные практики,финтех,финансовые,технологии,НДО,наличное денежное обращение,банк,банковский сектор,кредитные истории,кредитная история,страхование,рынок ценных бумаг,противодествие отмыванию,валюта,валютный контроль,заемщик,кредитор,КПК,кредитно-потребительский кооператив,ключевая ставка,НПФ,негосударственный пенсионный фонд,дилер,брокер,форекс-дилер,аутсорсинг,кредитные каникулы,краудфандинг,факторинг,кибермошенник,наличные,застройщик,закредитованность,портфель,заемные средства,ПДН,показатель долговой нагрузки,кредитные организации,ЦБ онлайн,115-ФЗ,БКИ,бюро кредитных историй,мониторинг предприятий,бизнес-климат,кешбэк,инвестор,коллектор,мисселинг,потребительская корзина,ИИС,индивидуальный инвестиционый счет,цифровой рубль,биткойн,рубль,облигации,биржа,европротокол,эквайринг,кэшаут,наличные на кассе,МСП", blank=True)
    bag2 = models.TextField(blank=True)
    bag_arch = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ключевые слова'
        verbose_name_plural = 'Ключевые слова'
        
    def __str__(self):
        return f"Ключевые слова для {self.user.username}"

# default="Банк России,ЦБ,Центральный банк,мегарегулятор,министр,министер,финанс,Нацбанк,мошенн,Сбер,льгот,рублей,Отделение-Национальный банк по Республике Марий Эл,Отдление-НБ Республика Марий Эл,Отдление-НБ,Волго-Вятское ГУ,Волго-Вятское главное управление,Экономика,бизнес,ОСАГО,эскроу,мошенничество,мошенники,финансы,финансовый рынок,МФО,микрофинансирование,ESG,фальшивка,подделка,деньги,финансы,кредит,заем,вклад,депозит,инфляция,инфляционные ожидания,цены,банкомат,инкассатор,инкассация,банковские карты,банк,платежные карты,платежи,платежей,СБП,система быстрых платежей,реструктуризация,меры поддержки,финансовая грамотность,доклад,Региональная экономика,Глава Марий Эл,Александр Волков,управляющий,страхование,инвестиции,ценные бумаги,безнал,безналичная оплата,ипотека,ИЖК,фондовый рынок,киберграмотность,выставка Банка России,памятные банкноты,монеты,подлинность,индивидуальные инвестиционные счета,инвестсчета,ломбард,нелегал,нелегальный,участник,финпирамида,финансовая пирамида,онлайн-уроки,дольщики,банкноты,купюры,ДКП,денежно-кредитная политика,НСПК,национальная платежная система,недобросовестные практики,финтех,финансовые,технологии,НДО,наличное денежное обращение,банк,банковский сектор,кредитные истории,кредитная история,страхование,рынок ценных бумаг,противодествие отмыванию,валюта,валютный контроль,заемщик,кредитор,КПК,кредитно-потребительский кооператив,ключевая ставка,НПФ,негосударственный пенсионный фонд,дилер,брокер,форекс-дилер,аутсорсинг,кредитные каникулы,краудфандинг,факторинг,кибермошенник,наличные,застройщик,закредитованность,портфель,заемные средства,ПДН,показатель долговой нагрузки,кредитные организации,ЦБ онлайн,115-ФЗ,БКИ,бюро кредитных историй,мониторинг предприятий,бизнес-климат,кешбэк,инвестор,коллектор,мисселинг,потребительская корзина,ИИС,индивидуальный инвестиционый счет,цифровой рубль,биткойн,рубль,облигации,биржа,европротокол,эквайринг,кэшаут,наличные на кассе,МСП", 