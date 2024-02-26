from django import forms

from .models import Parsers, SocialData

class AddVKTelegramSourceForm(forms.Form):
    parser = forms.ModelChoiceField(
        queryset=Parsers.objects.all(),
        empty_label="Выберите парсер",  # Set an appropriate label
        required=True
    )
    url = forms.URLField(
        label="Вставьте ссылку на источник VK/Telegram:",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
# class AddVKTelegramSourceForm(forms.Form):
#     parser = forms.ModelChoiceField(
#         label='Выберите парсер:',
#         queryset=Parsers.objects.all(),
#         empty_label=None  # If you want to force the user to select a parser
#     )
#     url = forms.URLField(label="Enter the webpage URL", max_length=200)
    
class AddNewsSourceForm(forms.Form):
    parser = forms.ModelChoiceField(
        queryset=Parsers.objects.all(),
        empty_label="Выберите парсер",  # Set an appropriate label
        required=True
    )
    url = forms.URLField(label="Вставьте ссылку на новостной сайт:", required=False)
    rss_url = forms.URLField(label="Или вставьте ссылку на RSS:", required=False)
    
class SocialDataForm(forms.ModelForm):
    class Meta:
        model = SocialData
        fields = ['vk_app_token', 'vk_app_id', 'vk_app_secret', 'telegram_api_id', 'telegram_api_hash', 'phone_number']


    def __init__(self, *args, **kwargs):
        super(SocialDataForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = False
