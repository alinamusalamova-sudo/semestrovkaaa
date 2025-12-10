import json
import random
import threading
from collections import defaultdict


class CitiesDatabase:
    def __init__(self):
        self.cities = set()
        self.used_cities = set()
        self.last_letter = None
        self.lock = threading.RLock()
        self.load_cities()

        # Статистика игры
        self.player_scores = defaultdict(int)
        self.current_player = None
        self.game_started = False

    def load_cities(self):
        """Загрузка базы городов"""
        cities_data = [
            "Абакан", "Абу-Даби", "Абуджа", "Авиньон", "Агадир", "Адамстаун", "Аддис-Абеба", "Аден",
            "Акапулько", "Аккра", "Актобе", "Аланья", "Алжир", "Амман", "Амстердам",
            "Анадырь", "Анкара", "Анталья", "Антананариву", "Апиа", "Астана", "Асунсьон",
            "Афины", "Ашхабад", "Багдад", "Бангкок", "Банги", "Банжул", "Барнаул",
            "Бейрут", "Белград", "Берлин", "Берн", "Бисау", "Бишкек", "Богота",
            "Бразилиа", "Братислава", "Брюссель", "Будапешт", "Буэнос-Айрес", "Бужумбура",
            "Вадуц", "Ватикан", "Вашингтон", "Вена", "Венеция", "Вильнюс", "Виндхук",
            "Варшава", "Вроцлав", "Валлетта", "Гавана", "Гамбург", "Гватемала",
            "Гибралтар", "Гонконг", "Грозный", "Гуанчжоу", "Дакар", "Дакка", "Дели",
            "Джакарта", "Джидда", "Джорджтаун", "Джуба", "Дублин", "Душанбе", "Дюссельдорф",
            "Екатеринбург", "Елгава", "Ереван", "Женева", "Житомир", "Загреб", "Занзибар",
            "Иваново", "Иерусалим", "Ижевск", "Иркутск", "Исламабад", "Стамбул",
            "Йоханнесбург", "Йошкар-Ола", "Кабул", "Каир", "Канберра", "Каракас",
            "Касабланка", "Катманду", "Киев", "Кишинёв", "Кингстон", "Киншаса",
            "Копенгаген", "Краков", "Куала-Лумпур", "Лагос", "Лас-Вегас", "Лиссабон",
            "Лима", "Лондон", "Лос-Анджелес", "Луанда", "Любляна", "Люксембург", "Львов",
            "Мадрид", "Мале", "Манагуа", "Манила", "Мапуту", "Марракеш", "Маскат",
            "Мехико", "Милан", "Минск", "Могадишо", "Монако", "Москва", "Мумбаи", "Мюнхен",
            "Найроби", "Накхичевань", "Нанкин", "Нью-Дели", "Нью-Йорк", "Никосия",
            "Ниамей", "Норильск", "Нур-Султан", "Одесса", "Окленд", "Омск", "Орландо",
            "Осло", "Осака", "Ош", "Париж", "Пекин", "Прага", "Пхеньян", "Пномпень",
            "Порто-Ново", "Порту", "Псков", "Пятигорск", "Рейкьявик", "Рига", "Рим",
            "Рио-де-Жанейро", "Ростов-на-Дону", "Сан-Марино", "Сан-Паулу", "Сан-Хосе",
            "Сантьяго", "Самара", "Сеул", "Сингапур", "Сибай", "София", "Стамбул", "Стокгольм",
            "Сукхум", "Сидней", "Таллин", "Ташкент", "Тбилиси", "Тегеран", "Тирана",
            "Токио", "Торонто", "Тула", "Тунис", "Улан-Батор", "Ульяновск", "Уфа",
            "Фамагуста", "Флоренция", "Франкфурт", "Фритаун", "Фукуока", "Хабаровск",
            "Хартум", "Хельсинки", "Хониара", "Хошимин", "Цюрих", "Чебоксары", "Чикаго",
            "Чита", "Шанхай", "Шарм-эш-Шейх", "Штутгарт", "Шэньчжэнь", "Эдинбург",
            "Эль-Кувейт", "Южно-Сахалинск", "Ялта", "Ямусукро", "Янгон", "Ярославль"
        ]
        self.cities = set(cities_data)

    def get_valid_last_letter(self, city):
        invalid_letters = {'ь', 'ъ', 'ы'} # буквы, на которые нет городов
        for letter in reversed(city.lower()):
            if letter not in invalid_letters:
                return letter
        return city[-1].lower()

    def add_city(self, city, player_name):
        with self.lock:
            if not self.game_started:
                return True, "Игра началась! Первый ход за вами!"

            city_lower = city.lower()


            if city_lower not in {c.lower() for c in self.cities}:
                return False, f"Город '{city}' не существует в базе!"


            if city_lower in {c.lower() for c in self.used_cities}:
                return False, f"Город '{city}' уже был использован!"

            if self.last_letter and city[0].lower() != self.last_letter:
                return False, f"Город должен начинаться на букву '{self.last_letter.upper()}'!"


            self.used_cities.add(city)
            self.last_letter = self.get_valid_last_letter(city)
            self.player_scores[player_name] += 1
            self.current_player = player_name

            return True, f"Отлично! Следующий город на букву '{self.last_letter.upper()}'"

    #начинаем игру с первого города
    def start_game(self, first_city, player_name):
        with self.lock:
            city_lower = first_city.lower()

            if city_lower not in {c.lower() for c in self.cities}:
                return False, f"Город '{first_city}' не существует в базе!"

            self.used_cities.add(first_city)
            self.last_letter = self.get_valid_last_letter(first_city)
            self.player_scores[player_name] += 1
            self.current_player = player_name
            self.game_started = True

            return True, f"Игра началась! Следующий город на букву '{self.last_letter.upper()}'"

    def get_game_state(self):
        with self.lock:
            return {
                'used_cities': list(self.used_cities),
                'last_letter': self.last_letter,
                'scores': dict(self.player_scores),
                'current_player': self.current_player,
                'game_started': self.game_started
            }

    def reset_game(self):
        with self.lock:
            self.used_cities.clear()
            self.last_letter = None
            self.player_scores.clear()
            self.current_player = None
            self.game_started = False

    def get_available_cities(self):
        with self.lock:
            if not self.last_letter:
                return []

            available = []
            used_lower = {c.lower() for c in self.used_cities}

            for city in self.cities:
                city_lower = city.lower()
                if (city_lower not in used_lower and
                        city_lower.startswith(self.last_letter)):
                    available.append(city)


            return available
