import socket
import threading
import json
import time


class GameProtocol:
    @staticmethod
    def create_message(message_type, **kwargs):
        message = {'type': message_type}
        message.update(kwargs)
        return json.dumps(message) + '\n'

    @staticmethod
    def parse_message(data):
        try:
            return json.loads(data.strip())
        except json.JSONDecodeError:
            return None


class GameRoom:
    def __init__(self, room_name):
        self.name = room_name
        self.players = []
        self.used_cities = []
        self.last_letter = None
        self.game_started = False
        self.current_player_index = 0
        self.lock = threading.Lock()
        self.player_scores = {}

        self.cities = ["Абакан", "Абу-Даби", "Абуджа", "Авиньон", "Агадир", "Адамстаун", "Аддис-Абеба", "Аден",
            "Акапулько", "Аккра", "Актобе", "Аланья", "Алжир", "Амман", "Амстердам",
            "Анадырь", "Анкара", "Анталья", "Антананариву", "Апиа", "Астана", "Асунсьон",
            "Афины", "Ашхабад", "Баймак", "Багдад", "Бангкок", "Банги", "Банжул", "Барнаул",
            "Бейрут", "Белград", "Берлин", "Берн", "Бисау", "Бишкек", "Богота",
            "Бразилиа", "Братислава", "Брюссель", "Будапешт", "Буэнос-Айрес", "Бужумбура",
            "Вадуц", "Ватикан", "Вашингтон", "Вена", "Венеция", "Вильнюс", "Виндхук",
            "Варшава", "Вроцлав", "Волгоград", "Вологда", "Воронеж", "Валлетта", "Гавана", "Гамбург", "Гватемала",
            "Гибралтар", "Гонконг", "Грозный", "Гуанчжоу", "Дакар", "Дакка", "Дели",
            "Джакарта", "Джидда", "Джорджтаун", "Джуба", "Дублин", "Душанбе", "Дюссельдорф",
            "Екатеринбург", "Елгава", "Ереван", "Женева", "Житомир", "Загреб", "Занзибар",
            "Иваново", "Иерусалим", "Ижевск", "Иркутск", "Исламабад", "Стамбул",
            "Йоханнесбург", "Йошкар-Ола", "Кабул", "Казань", "Каир", "Канберра", "Каракас",
            "Касабланка", "Катманду", "Киев", "Кишинёв", "Кингстон", "Киншаса",
            "Копенгаген", "Краков", "Куала-Лумпур", "Лагос", "Лас-Вегас", "Лиссабон",
            "Лима", "Лондон", "Лос-Анджелес", "Луанда", "Любляна", "Люксембург", "Львов",
            "Мадрид", "Мале", "Манагуа", "Манила", "Мапуту", "Марракеш", "Маскат",
            "Мехико", "Милан", "Минск", "Могадишо", "Монако", "Москва", "Мумбаи", "Мюнхен",
            "Найроби", "Накхичевань", "Нанкин", "Нижний Новогород","Нью-Дели", "Нью-Йорк", "Никосия",
            "Ниамей", "Норильск", "Нур-Султан", "Одесса", "Окленд", "Омск", "Орландо",
            "Осло", "Осака", "Ош", "Париж", "Пекин", "Прага", "Пхеньян", "Пномпень",
            "Порто-Ново", "Порту", "Псков", "Пятигорск", "Рейкьявик", "Рига", "Рим",
            "Рио-де-Жанейро", "Ростов-на-Дону", "Сан-Марино", "Сан-Паулу", "Сан-Хосе",
            "Сантьяго", "Самара", "Сеул", "Сингапур", "София", "Стамбул", "Стокгольм",
            "Сукхум", "Сидней", "Таллин", "Ташкент", "Тбилиси", "Тегеран", "Тирана",
            "Токио", "Торонто", "Тула", "Тунис", "Улан-Батор", "Ульяновск", "Уфа",
            "Фамагуста", "Флоренция", "Франкфурт", "Фритаун", "Фукуока", "Хабаровск",
            "Хартум", "Хельсинки", "Хониара", "Хошимин", "Цюрих", "Чебоксары", "Чикаго",
            "Чита", "Шанхай", "Шарм-эш-Шейх", "Штутгарт", "Шэньчжэнь", "Эдинбург",
            "Эль-Кувейт", "Южно-Сахалинск", "Ялта", "Ямусукро", "Янгон", "Ярославль"
        ]


    def get_valid_last_letter(self, city):
        invalid_letters = {'ь', 'ъ', 'ы'}
        for letter in reversed(city.lower()):
            if letter not in invalid_letters:
                return letter
        return city[-1].lower()

    def add_player(self, player_name):
        with self.lock:
            if player_name not in self.players:
                self.players.append(player_name)
                return True
            return False

    def remove_player(self, player_name):
        with self.lock:
            if player_name in self.players:
                if self.game_started and self.players.index(player_name) == self.current_player_index:
                    self.next_player()
                self.players.remove(player_name)
                if not self.players:
                    self.reset_game()
                return True
            return False

    def start_game(self, player_name, city):
        with self.lock:
            if self.game_started:
                return False, "Игра уже начата"

            city_lower = city.lower()
            if city_lower not in {c.lower() for c in self.cities}:
                return False, "Город не найден в базе"

            if city_lower in {c.lower() for c in self.used_cities}:
                return False, "Город уже использован"

            self.used_cities.append(city)
            self.last_letter = self.get_valid_last_letter(city)
            self.game_started = True
            self.current_player_index = (self.players.index(player_name) + 1) % len(self.players)
            self.player_scores[player_name] = self.player_scores.get(player_name, 0) + 1

            return True, f"Игра началась! Следующий ход: {self.get_current_player()}. Буква: '{self.last_letter.upper()}'"

    def add_city(self, player_name, city):
        with self.lock:
            if not self.game_started:
                return False, "Игра еще не началась"

            current_player = self.get_current_player()
            if player_name != current_player:
                return False, f"Сейчас ход игрока {current_player}"

            city_lower = city.lower()
            if city_lower not in {c.lower() for c in self.cities}:
                return False, "Город не найден в базе"

            if city_lower in {c.lower() for c in self.used_cities}:
                return False, "Город уже использован"

            if city[0].lower() != self.last_letter:
                return False, f"Город должен начинаться на букву '{self.last_letter.upper()}'"

            self.used_cities.append(city)
            self.last_letter = self.get_valid_last_letter(city)
            self.next_player()
            self.player_scores[player_name] = self.player_scores.get(player_name, 0) + 1

            next_player = self.get_current_player()
            return True, f"Принято! Следующий ход: {next_player}. Буква: '{self.last_letter.upper()}'"

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def get_current_player(self):
        if not self.players:
            return None
        return self.players[self.current_player_index]

    def get_game_state(self):
        with self.lock:
            return {
                'room_name': self.name,
                'players': self.players.copy(),
                'used_cities': self.used_cities.copy(),
                'last_letter': self.last_letter,
                'game_started': self.game_started,
                'current_player': self.get_current_player(),
                'used_count': len(self.used_cities),
                'scores': self.player_scores.copy()
            }

    def reset_game(self):
        with self.lock:
            self.used_cities = []
            self.last_letter = None
            self.game_started = False
            self.current_player_index = 0
            self.player_scores = {}


class CitiesGameServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.rooms = {}
        self.player_rooms = {}
        self.clients = {}
        self.lock = threading.RLock()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.create_room("Основная")

    def create_room(self, room_name):
        with self.lock:
            if room_name not in self.rooms:
                self.rooms[room_name] = GameRoom(room_name)
                print(f"🏠 Создана комната: {room_name}")
                return True
            return False

    def join_room(self, player_name, room_name):
        with self.lock:
            if room_name not in self.rooms:
                self.create_room(room_name)

            if player_name in self.player_rooms:
                old_room = self.player_rooms[player_name]
                self.rooms[old_room].remove_player(player_name)
                self.broadcast_room_state(old_room)

            success = self.rooms[room_name].add_player(player_name)
            if success:
                self.player_rooms[player_name] = room_name
                self.broadcast_room_state(room_name)
                return True, f"Присоединились к комнате '{room_name}'"
            return False, "Не удалось присоединиться к комнате"

    def broadcast_room_state(self, room_name):
        if room_name not in self.rooms:
            return

        room_state = self.rooms[room_name].get_game_state()
        message = GameProtocol.create_message('room_state', **room_state)

        with self.lock:
            for player in self.rooms[room_name].players:
                if player in self.clients:
                    try:
                        self.clients[player][0].send(message.encode('utf-8'))
                    except:
                        pass

    def handle_client(self, client_socket, address):
        player_name = None

        try:
            buffer = ""
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    response = self.process_message(line, client_socket)
                    if response:
                        client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"Ошибка с клиентом {address}: {e}")
        finally:
            if player_name:
                self.leave_room(player_name)
                with self.lock:
                    if player_name in self.clients:
                        del self.clients[player_name]

            client_socket.close()
            print(f"Отключен: {address}")

    def process_message(self, message_str, client_socket):
        try:
            message = GameProtocol.parse_message(message_str)
            if not message:
                return GameProtocol.create_message('error', message='Неверный формат сообщения')

            command = message.get('command')
            player_name = message.get('player_name')
            room_name = message.get('room_name')
            city = message.get('city')

            if command == 'join':
                return self.handle_join(player_name, client_socket)
            elif command == 'join_room':
                return self.handle_join_room(player_name, room_name)
            elif command == 'create_room':
                return self.handle_create_room(player_name, room_name)
            elif command == 'list_rooms':
                return self.handle_list_rooms()
            elif command == 'start':
                return self.handle_start(player_name, city)
            elif command == 'add_city':
                return self.handle_add_city(player_name, city)
            elif command == 'reset':
                return self.handle_reset(player_name)
            elif command == 'leave':
                return self.handle_leave(player_name)
            elif command == 'chat':
                return self.handle_chat(player_name, message.get('message', ''))
            else:
                return GameProtocol.create_message('error', message='Неизвестная команда')

        except Exception as e:
            return GameProtocol.create_message('error', message=f'Ошибка обработки: {str(e)}')

    def handle_join(self, player_name, client_socket):
        with self.lock:
            if player_name in self.clients:
                return GameProtocol.create_message('error', message='Игрок с таким именем уже существует')

            self.clients[player_name] = (client_socket, 'unknown')
            success, msg = self.join_room(player_name, "Основная")

            return GameProtocol.create_message('success',
                                               message=f"Игрок {player_name} присоединился. {msg}",
                                               room_name="Основная"
                                               )

    def handle_chat(self, player_name, message_text):
        if player_name not in self.player_rooms:
            return GameProtocol.create_message('error', message='Вы не в комнате')

        room_name = self.player_rooms[player_name]

        chat_msg = GameProtocol.create_message('chat_message',
                                               sender=player_name,
                                               message=message_text,
                                               timestamp=time.strftime("%H:%M:%S"))

        with self.lock:
            for player in self.rooms[room_name].players:
                if player in self.clients:
                    try:
                        self.clients[player][0].send(chat_msg.encode('utf-8'))
                    except:
                        pass

        return GameProtocol.create_message('success', message='Сообщение отправлено')

    def handle_join_room(self, player_name, room_name):
        if not room_name:
            return GameProtocol.create_message('error', message='Укажите название комнаты')

        success, msg = self.join_room(player_name, room_name)
        if success:
            return GameProtocol.create_message('success', message=msg, room_name=room_name)
        else:
            return GameProtocol.create_message('error', message=msg)

    def handle_create_room(self, player_name, room_name):
        if not room_name:
            return GameProtocol.create_message('error', message='Укажите название комнаты')

        success = self.create_room(room_name)
        if success:
            join_success, join_msg = self.join_room(player_name, room_name)
            if join_success:
                return GameProtocol.create_message('success',
                                                   message=f"Комната '{room_name}' создана. {join_msg}",
                                                   room_name=room_name
                                                   )
        return GameProtocol.create_message('error', message='Комната уже существует')

    def handle_list_rooms(self):
        with self.lock:
            rooms_info = []
            for name, room in self.rooms.items():
                rooms_info.append({
                    'name': name,
                    'players': len(room.players),
                    'game_started': room.game_started
                })

            return GameProtocol.create_message('rooms_list', rooms=rooms_info)

    def handle_start(self, player_name, city):
        if player_name not in self.player_rooms:
            return GameProtocol.create_message('error', message='Вы не в комнате')

        room_name = self.player_rooms[player_name]
        success, message = self.rooms[room_name].start_game(player_name, city)

        if success:
            self.broadcast_room_state(room_name)
            return GameProtocol.create_message('success', message=message)
        else:
            return GameProtocol.create_message('error', message=message)

    def handle_add_city(self, player_name, city):
        if player_name not in self.player_rooms:
            return GameProtocol.create_message('error', message='Вы не в комнате')

        room_name = self.player_rooms[player_name]
        success, message = self.rooms[room_name].add_city(player_name, city)

        if success:
            self.broadcast_room_state(room_name)
            return GameProtocol.create_message('success', message=message)
        else:
            return GameProtocol.create_message('error', message=message)

    def handle_reset(self, player_name):
        if player_name not in self.player_rooms:
            return GameProtocol.create_message('error', message='Вы не в комнате')

        room_name = self.player_rooms[player_name]
        self.rooms[room_name].reset_game()
        self.broadcast_room_state(room_name)

        return GameProtocol.create_message('success', message='Игра сброшена')

    def leave_room(self, player_name):
        with self.lock:
            if player_name in self.player_rooms:
                room_name = self.player_rooms[player_name]
                self.rooms[room_name].remove_player(player_name)
                del self.player_rooms[player_name]
                self.broadcast_room_state(room_name)
                return True
            return False

    def handle_leave(self, player_name):
        success = self.leave_room(player_name)
        if success:
            with self.lock:
                if player_name in self.clients:
                    del self.clients[player_name]
            return GameProtocol.create_message('success', message='Игрок покинул игру')
        else:
            return GameProtocol.create_message('error', message='Игрок не найден')

    def accept_connections(self):
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"🔗 Новое подключение: {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()

            except Exception as e:
                print(f"Ошибка при приеме подключения: {e}")
                break

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"🚀 Сервер игры в города запущен на {self.host}:{self.port}")
            print("🏠 Создана комната 'Основная'")
            print("⏳ Ожидаем подключений...")

            self.accept_connections()

        except KeyboardInterrupt:
            print("\n🛑 Сервер остановлен")
        except Exception as e:
            print(f"❌ Ошибка сервера: {e}")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    server = CitiesGameServer()
    server.start()