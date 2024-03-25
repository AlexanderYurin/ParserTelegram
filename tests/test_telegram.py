import pytest

from parser.telegram import get_company_name_and_title, convert_dict_to_text_format, get_vacancies, get_urls, \
	get_location


def test_get_company_name_and_title():
	valid_data = "Java Developer / FedAG"
	invalid_data = "Java Developer"
	response = get_company_name_and_title(valid_data)
	assert response == ("Java Developer", "FedAG")
	response = get_company_name_and_title(invalid_data)
	assert response == ("Java Developer", "Имя компания отсутствует")


def test_convert_dict_to_text_format():
	data = {
		"message": "#java #react #flutter #ios\nВакансии для разработчиков\n\nСтажёр Java Developer / Krainet\nМинск. "
				   "Компания занимается разработкой по заказ клиентов и продажей решений. \nПодробнее | Откликнуться "
				   "\n\nJava Developer / FedAG\nСПб. до 20 000₽. Компания по разработке программного обеспечения. "
				   "\nПодробнее | Откликнутся ",
		"entities": [
			{
				"_": "MessageEntityTextUrl",
				"offset": 165,
				"length": 9,
				"url": "https://docs.google.com/document/d/199xoh3MiT5xjZchmA-BZT63-ABKQpv6PdvDzC6bTQvY/edit"
			},
			{
				"_": "MessageEntityTextUrl",
				"offset": 177,
				"length": 12,
				"url": "https://t.me/powerofmeaou"
			},
		]
	}
	response = convert_dict_to_text_format(data)
	assert isinstance(response, str)
	assert "https://t.me/powerofmeaou" in response


def test_get_vacancies():
	data = '#java #react #flutter #ios\nВакансии для разработчиков\n\nСтажёр Java Developer / Krainet\nМинск. Компания ' \
		   'занимается разработкой по заказ клиентов и продажей решений. \nПодробнее ' \
		   'https://docs.google.com/document/d/199xoh3MiT5xjZchmA-BZT63-ABKQpv6PdvDzC6bTQvY/edit | Откликнуться ' \
		   'https://t.me/powerofmeaou'

	response = get_vacancies(data)
	assert len(response) == 1
	assert len(response[0]) == 3


def test_get_urls():
	data = "Подробнее: https://career.habr.com/vacancies/1000139452 url: https://career.habr.com/vacancies/1000139452"
	response = get_urls(data)
	assert len(response) == 2
	assert "https://career.habr.com/vacancies/1000139452" == response[0]


def test_get_location_remote():
	data = "Удалённо. от 40 000 до 60 000₽. Разработка мобильных приложений.. Подробнее: " \
		   "https://www.vseti.app/vakansii/hfdjfd8479dfjkdfdf"
	response = get_location(data)
	assert response[1] == "Удалённо"
	assert response[0] is True


def test_get_location_not_remote():
	data = "Минск. от 40 000 до 60 000₽. Разработка мобильных приложений.. Подробнее: " \
		   "https://www.vseti.app/vakansii/hfdjfd8479dfjkdfdf"
	response = get_location(data)
	assert response[1] == "Минск"
	assert response[0] is False
