from django.shortcuts import render, redirect
from random import choice
from .funny_texts import funnyTexts


class Funny502ErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if response.status_code == 404 and request.path != 'parsed_news':
            random_funny_text = choice(funnyTexts)
            return render(request, 'error_page.html', {'error_message': random_funny_text}, status=404)

        return response

    
    
#         if response.status_code == 500:
#             random_funny_text = choice(funnyTexts)
#             return render(request, 'error_page.html', {'error_message': random_funny_text}, status=500)

#         # Если ошибка отсутствует, перенаправляем пользователя на "штатную" страницу
#         return redirect('parsed_news')