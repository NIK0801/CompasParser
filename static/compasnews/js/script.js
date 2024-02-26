// JavaScript file for parsing news data
/*global SelectBox, interpolate*/
// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.
'use strict';

// Функция для всплывающего окошка с контентом новости
document.addEventListener("DOMContentLoaded", function() {
    var contentToggles = document.querySelectorAll('.content-toggle');

    contentToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(event) {
            event.preventDefault();
            var popupContainer = toggle.nextElementSibling;
            popupContainer.style.display = 'block';
        });
    });

    var popupCloseButtons = document.querySelectorAll('.popup-close');

    popupCloseButtons.forEach(function(closeButton) {
        closeButton.addEventListener('click', function(event) {
            event.preventDefault();
            var popupContainer = closeButton.parentElement;
            popupContainer.style.display = 'none';
        });
    });
});



 // Проверяем, открывалось ли модальное окно ранее
var modalOpenCount = localStorage.getItem('modalOpenCount');
var savedMessage = localStorage.getItem('savedMessage');
var currentMessage = "Информация об обновлении приложения...номер обновления №"; // Замените на актуальный текст сообщения

if (!modalOpenCount) {
  modalOpenCount = 0;
}
// Если модальное окно было открыто менее двух раз или текст сообщения изменился, открываем его
if (modalOpenCount < 2 || savedMessage !== currentMessage) {
    openModalOnLoad();
    modalOpenCount++;
    localStorage.setItem('modalOpenCount', modalOpenCount);
    localStorage.setItem('savedMessage', currentMessage);
}
// Определяем функцию, которая будет открывать модальное окно при загрузке страницы
function openModalOnLoad() {
    var modal = document.getElementById("myModal");
    modal.style.display = "block";
}
// Открытие и закрытие модального окна
var modal = document.getElementById("myModal");
var span = document.getElementsByClassName("close")[0];
// Закрытие модального окна при клике на крестик
span.onclick = function() {
  modal.style.display = "none";
}
// Закрытие модального окна при клике вне его области
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}   


// Крутящийся компас
$(document).ready(function() {
    $('#parsing-form').on('submit', function(e) {
        e.preventDefault();

        // Show the loading overlay when parsing starts
        $('#loading-overlay').show();

        $.ajax({
            type: 'POST',
            url: '{% url "parsed_news" %}',
            data: $(this).serialize(),
            success: function(response) {
                // Parsing completed; handle the response

                // Hide the loading overlay when parsing is completed
                $('#loading-overlay').hide();

                // Add a query parameter to the URL to indicate parsing completion
                window.location.href = updateUrlParameter(window.location.href, 'parsingCompleted', 'true');
            }
        });
    });

    // Function to display a notification to the user
    function showNotification(message) {
        var notification = $('<div class="toast" role="alert" aria-live="assertive" aria-atomic="true">' +
            '<div class="toast-header">' +
            '<strong class="mr-auto">Уведомление</strong>' +
            '<button type="button" class="ml-2 mb-1 close" aria-label="Close">' +
            '<span aria-hidden="true">&times;</span>' +
            '</button>' +
            '</div>' +
            '<div class="toast-body">' + message + '</div>' +
            '</div>');

        // Add the notification to the container
        $('#notification-container').append(notification);

        // Show the notification
        notification.toast({ autohide: false }).toast('show');

        // Handle notification close
        notification.find('.close').on('click', function () {
            notification.toast('hide'); // Manually hide the notification
            setTimeout(function() {
                notification.remove(); // Manually remove the notification after it's hidden
                // Remove the 'parsingCompleted' query parameter from the URL
                window.location.href = removeUrlParameter(window.location.href, 'parsingCompleted');
            }, 500); // Adjust the timing as needed
        });
    }

    // Function to add or update a query parameter in the URL
    function updateUrlParameter(url, param, value) {
        var re = new RegExp("([?&])" + param + "=.*?(&|$)", "i");
        var separator = url.indexOf('?') !== -1 ? "&" : "?";
        if (url.match(re)) {
            return url.replace(re, '$1' + param + "=" + value + '$2');
        } else {
            return url + separator + param + "=" + value;
        }
    }

    // Function to remove a query parameter from the URL
    function removeUrlParameter(url, param) {
        var urlParts = url.split('?');
        if (urlParts.length >= 2) {
            var prefix = encodeURIComponent(param) + '=';
            var query = urlParts[1];
            var params = query.split('&');
            for (var i = params.length - 1; i >= 0; i--) {
                if (params[i].lastIndexOf(prefix, 0) !== -1) {
                    params.splice(i, 1);
                }
            }
            return urlParts[0] + (params.length > 0 ? '?' + params.join('&') : '');
        }
        return url;
    }
    // Check for the 'parsingCompleted' query parameter in the URL
    var urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('parsingCompleted')) {
        // Parsing has been completed, display the success notification
        showNotification('Парсинг завершен успешно.');
    }
});


// ЧЕКБОКСЫ ДЛЯ ВЫБОРА НОВОСТЕЙ_НАЧАЛО СКРИПТА
$(document).ready(function() {
    // Обработчик события изменения чекбокса "Выбрать все новости"
    $('#select-all-news').on('change', function() {
        if ($(this).is(':checked')) {
            // Выбрать все чекбоксы для новостей
            $('#news-table tbody input[type="checkbox"]').prop('checked', true);
            updateSelectedNews();
        } else {
            // Снять выбор со всех чекбоксов для новостей
            $('#news-table tbody input[type="checkbox"]').prop('checked', false);
            clearSelection();
        }
    });
    // Обработчик события изменения чекбокса одной новости
    $('#news-table tbody input[type="checkbox"]').on('change', function() {
        if ($('#news-table tbody input[type="checkbox"]:checked').length === $('#news-table tbody input[type="checkbox"]').length) {
            $('#select-all-news').prop('checked', true);
        } else {
            $('#select-all-news').prop('checked', false);
        }
        updateSelectedNews();
    });

    var selectedNews = []; // Array to store selected news article IDs

    // Function to update selected news in local storage
    function updateLocalStorage() {
        localStorage.setItem('selectedNews', JSON.stringify(selectedNews));
    }

    // Function to clear selection and uncheck checkboxes
    function clearSelection() {
        selectedNews = [];
        updateLocalStorage();
        // Uncheck all checkboxes
        $('#news-table tbody input[type="checkbox"]').prop('checked', false);
    }

    
    // Function to update the selected news array based on checked checkboxes
    function updateSelectedNews() {
        const newSelection = $('#news-table tbody input[type="checkbox"]:checked').map(function() {
            return parseInt($(this).val());
        }).get();
        selectedNews = [...selectedNews, ...newSelection];
        updateLocalStorage();
    }
    // Load selected news from local storage if available
    var storedSelectedNews = localStorage.getItem('selectedNews');
    if (storedSelectedNews) {
        selectedNews = JSON.parse(storedSelectedNews);
        // Set the checkboxes as checked based on the restored selections
        selectedNews.forEach(function(newsId) {
            $('input[type="checkbox"][value="' + newsId + '"]').prop('checked', true);
        });
    }

    $('#word-export-form').on('submit', function(e) {
        // Set the selected news IDs as a comma-separated string in a hidden field
        $('#selected-news-field-word').val(selectedNews.join(','));
        clearSelection();
    });  
        
    // Handle form submission (export selected news)
    $('#export-form').on('submit', function(e) {
        // Set the selected news IDs as a comma-separated string in a hidden field
        $('#selected-news-field').val(selectedNews.join(','));
        clearSelection();
    });
    
    $('#delete-selected-form').on('submit', function(e) {
        // Set the selected news IDs as a comma-separated string in a hidden field
        $('#selected-news-field-delete').val(selectedNews.join(','));
        clearSelection();
    });  
});
// ЧЕКБОКСЫ ДЛЯ ВЫБОРА НОВОСТЕЙ_КОНЕЦ СКРИПТА

// СОРТИРОВКА ТАБЛИЦЫ_НАЧАЛО СКРИПТА
$(document).ready(function() {
    var isAscending = false; // Изначально сортировка по убыванию

    $('#sort-date').on('click', function() {
        isAscending = !isAscending;
        updateSortIcon(isAscending);
        sortTableByDate(isAscending);
    });

    function sortTableByDate(ascending) {
        var rows = $('#news-table tbody').find('tr').get();

        rows.sort(function(a, b) {
            var dateA = parseDate($(a).find('td:eq(2)').text());
            var dateB = parseDate($(b).find('td:eq(2)').text());

            if (ascending) {
                return dateA - dateB;
            } else {
                return dateB - dateA;
            }
        });

        $.each(rows, function(index, row) {
            $('#news-table tbody').append(row);
        });
    }

    function updateSortIcon(ascending) {
        var sortIcon = $('#sort-icon');
        sortIcon.removeClass('bi-caret-up bi-caret-down');
        if (ascending) {
            sortIcon.addClass('bi-caret-up');
        } else {
            sortIcon.addClass('bi-caret-down');
        }
    }

    function parseDate(dateString) {
        var parts = dateString.split(' ');
        var dateParts = parts[0].split('.');
        var timeParts = parts[1].split(':');
        return new Date(dateParts[2], dateParts[1] - 1, dateParts[0], timeParts[0], timeParts[1], timeParts[2]);
    }
    // СОРТИРОВКА ТАБЛИЦЫ_КОНЕЦ СКРИПТА        
        
    // ЧТОБЫ ПРИ ПЕРЕХОДЕ МЕЖДУ СТРАНИЦАМИ НЕ СБИВАЛАСЬ ФИЛЬТРАЦИЯ
    $('.pagination a').on('click', function(e) {
        e.preventDefault();

        var pageUrl = $(this).attr('href'); // Получаем URL страницы

        // Получаем значения параметров фильтрации и поиска
        var filterStartDate = $('#filter_start_date').val();
        var filterEndDate = $('#filter_end_date').val();
        var searchQuery = $('#search').val();

        // Добавляем текущие параметры фильтрации и поиска к URL страницы пагинации
        var updatedUrl = pageUrl + '&filter_start_date=' + filterStartDate +
                     '&filter_end_date=' + filterEndDate + '&q=' + searchQuery;

        // Переходим на новую страницу с обновленным URL
        window.location.href = updatedUrl;
    });


});
