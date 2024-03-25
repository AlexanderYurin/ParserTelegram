import json
import re
import os
import time
from typing import Tuple, Dict, List

from dotenv import find_dotenv, load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel

if not find_dotenv():
	exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
	load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PASSWORD = os.getenv("PASSWORD")
PHONE_NUMBER = os.getenv("PHONE")
SESSION_NAME = "session_name"


def convert_dict_to_text_format(data_dict: Dict) -> str:
	"""
    Функция конвертирует словарь в нужный текстовый формат.

    :param data_dict: Словарь данных.
    :return: Текстовая строка в нужном формате.
    """
	links_info = []
	start_index = 0

	# Итерация по сущностям в словаре.
	for entity in data_dict.get("entities", []):
		# Если сущность - текстовая ссылка
		if entity["_"] == "MessageEntityTextUrl":
			# Вычисление индексов текста ссылки в сообщении.
			end_index = entity.get("offset", 0) + entity.get("length", 0)
			link_text = data_dict["message"][start_index:end_index]
			start_index = end_index
			link_url = entity.get("url", "")
			links_info.append(f"{link_text} {link_url}")

	# Сборка и объединение информации о ссылках в строку.
	return "".join(links_info)


def get_company_name_and_title(data: str) -> Tuple[str, str]:
	"""
     Функция получает company_name и title из входных данных.

    :param data: Входные данные, которые предварительно валидируются на соответствие.
    :return: Кортеж, содержащий title и company_name.
    """

	# Разбивка входных данных по символу ' / '
	data_list = data.split(' / ')
	if len(data_list) != 2:
		return data, "Имя компания отсутствует"
	title = data_list[0].strip()
	company_name = data_list[1].strip()
	return title, company_name


def get_vacancies(data: str) -> List[List[str]]:
	"""
    Функция для извлечения информации о вакансиях из текста.

    :param data: Входные данные в виде строки, представляющей собой текст с информацией о вакансиях.
    :return: Список списков строк, представляющих информацию о вакансиях.
    """

	# Разделяем входные данные по двойным переносам строки и отбираем только те строки, где есть "подробнее".
	vacancies = [message.split("\n") for message in data.split("\n\n") if "подробнее" in message.lower()]

	return vacancies


def get_location(data: str) -> Tuple[bool, str]:
	"""
    Функция получения информации о местоположении (удалённая работа или указанное место).

    :param data: Входные данные с информацией о вакансии.
    :return: Кортеж (удалённая работа - True/False, местоположение).
    """
	# Значения по умолчанию
	location = "Удалённо"
	remote = True

	# Разбиваем текст на две части: местоположение и остаток текста.
	parsing_text = data.lower().split(".", maxsplit=1)

	# Если в первой части не указано "удалённо", то считаем, что это указанное место.
	if "удалённо" not in parsing_text[0]:
		location = parsing_text[0].strip().title()
		remote = False

	return remote, location


def get_urls(data: str) -> List:
	"""
    Функция для извлечения всех URL-ссылок из текста.

    :param data: Входные данные с текстом.
    :return: Список URL-ссылок.
    """
	urls = re.findall(r'https?://\S+', data)
	return urls


def parse_chat(api_id: str, api_hash: str, session_name: str, phone_number: str, password: str,
			   target_group_id: int) -> Dict:
	"""
	Парсинг чата в Telegram для извлечения вакансий.
	:param api_id: Идентификатор приложения Telegram.
	:param api_hash: Хэш приложения Telegram.
	:param session_name: Название сессии для сохранения состояния авторизации.
	:param phone_number: Номер телефона пользователя.
	:param password: Пароль для авторизации.
	:param target_group_id: Идентификатор целевой группы для парсинга.
	:return: Словарь с информацией о вакансиях.
	"""

	client = TelegramClient(session_name, api_id, api_hash)
	client.start(password=password, phone=phone_number)

	limit = 100
	offset_id = 0
	all_vacancies = {}

	while True:
		history = client(GetHistoryRequest(
			peer=PeerChannel(target_group_id),
			offset_id=offset_id,
			offset_date=None,
			add_offset=0,
			limit=limit,
			max_id=0,
			min_id=0,
			hash=0
		))

		messages = history.messages
		if not messages:
			break  # Если сообщений больше нет, завершаем парсинг

		data_dict = (message.to_dict() for message in messages)
		for data in data_dict:
			text = convert_dict_to_text_format(data)
			vacancies = get_vacancies(text)
			date = data["date"]

			for i in range(len(vacancies)):
				try:
					title, company_name = get_company_name_and_title(vacancies[i][0])
					remote, location = get_location(vacancies[i][1])
					url = ""
					urls = get_urls(vacancies[i][2])
					description = f"{vacancies[i][1].strip()}. Подробнее: {urls[0]}"
					if len(urls) == 2:
						url = urls[1]
					else:
						url = urls[0]
					all_vacancies[vacancies[i][0]] = {
						"date": str(date),
						"external_id": f"{data['id']}.{i}",
						"title": title,
						"company_name": company_name,
						"description": description,
						"url": url,
						"remote": remote,
						"location": location,
						"salary": "Не указана",
					}
				except IndexError:
					print(f"Была ошибка: {data}")

		offset_id = messages[-1].id

	return all_vacancies


if __name__ == "__main__":
	group_id = -1001626257345
	start = time.time()
	data = parse_chat(API_ID, API_HASH, SESSION_NAME, PHONE_NUMBER, PASSWORD, group_id)
	with open("data.json", "w+", encoding="UTF-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)
	end = time.time()
	print(f"Время: {round((end - start) / 60)} мин.")
