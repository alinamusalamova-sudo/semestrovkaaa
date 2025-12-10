import threading
import sys
import socket

import json
from datetime import datetime
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                             QListWidget, QLabel, QMessageBox, QGroupBox,
                             QProgressBar)



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


class NetworkClient(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    message_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.socket = None
        self.connected_flag = False
        self.receive_thread = None

    def connect_to_server(self, host='localhost', port=8888):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(0.5)
            self.socket.connect((host, port))
            self.connected_flag = True

            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()

            self.connected.emit()
            return True

        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def send_message(self, message):
        if self.connected_flag and self.socket:
            try:
                self.socket.send(message.encode('utf-8'))
                return True
            except Exception as e:
                print(f"Ошибка отправки: {e}")
                self.connected_flag = False
                self.disconnected.emit()
        return False

    def receive_messages(self):
        buffer = ""
        while self.connected_flag and self.socket:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    print("Сервер закрыл соединение")
                    break

                buffer += data

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        message = GameProtocol.parse_message(line)
                        if message:
                            self.message_received.emit(message)

            except socket.timeout:
                continue
            except Exception as e:
                print(f"Ошибка приема сообщений: {e}")
                break

        self.connected_flag = False
        self.disconnected.emit()

    def disconnect(self):
        self.connected_flag = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None


class CitiesClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player_name = ""
        self.current_room = ""
        self.joined = False
        self.network_client = NetworkClient()

        # таймер
        self.game_timer = QTimer()
        self.game_time_left = 120
        self.game_active = False

        # очки игроков
        self.player_scores = {}

        self.setup_ui()
        self.connect_signals()

        # запускаем подключение с задержкой
        QTimer.singleShot(100, self.connect_to_server)

    def setup_ui(self):
        self.setWindowTitle("Города")
        self.setGeometry(100, 100, 1200, 800)

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8B5FBF, stop:1 #6A1B9A);
            }
            QGroupBox {
                background: rgba(255, 255, 255, 220);
                border: 2px solid #7B1FA2;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #4A148C;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 6px 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7B1FA2, stop:1 #4A148C);
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #BA68C8;
                border-radius: 10px;
                background: white;
                color: #4A148C;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #AB47BC, stop:1 #8E24AA);
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8E24AA, stop:1 #6A1B9A);
            }
            QPushButton:disabled {
                background: #9E9E9E;
                color: #757575;
            }
            QListWidget {
                background: rgba(255, 255, 255, 220);
                border: 2px solid #BA68C8;
                border-radius: 8px;
                color: #4A148C;
                font-weight: bold;
                font-size: 11px;
            }
            QTextEdit {
                background: rgba(255, 255, 255, 220);
                border: 2px solid #BA68C8;
                border-radius: 8px;
                color: #4A148C;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar {
                border: 2px solid #7B1FA2;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
                background: white;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #AB47BC, stop:1 #8E24AA);
                border-radius: 6px;
            }
            QLabel {
                color: #4A148C;
                font-weight: bold;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # левая панель
        left_panel = QVBoxLayout()


        # заголовок
        title_label = QLabel("💜 ИГРА В ГОРОДА 💜")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 26px; 
            font-weight: bold; 
            color: white; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #AB47BC, stop:1 #7B1FA2);
            padding: 18px;
            border-radius: 18px;
            border: 3px solid #4A148C;
        """)
        left_panel.addWidget(title_label)

        # таймеры
        timers_group = QGroupBox("⏰ Таймер игры")
        timers_layout = QVBoxLayout()

        game_timer_layout = QHBoxLayout()
        game_timer_layout.addWidget(QLabel("🕐 Время игры:"))
        self.game_timer_label = QLabel("02:00")
        self.game_timer_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #7B1FA2;")
        game_timer_layout.addWidget(self.game_timer_label)
        game_timer_layout.addStretch()

        self.game_progress = QProgressBar()
        self.game_progress.setRange(0, 120)
        self.game_progress.setValue(120)
        self.game_progress.setFormat("Осталось: %v сек")

        timers_layout.addLayout(game_timer_layout)
        timers_layout.addWidget(self.game_progress)
        timers_group.setLayout(timers_layout)
        left_panel.addWidget(timers_group)

        # результаты
        results_group = QGroupBox("🏆 Текущие очки")
        results_layout = QVBoxLayout()

        self.results_label = QLabel("Ожидание начала игры...")
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_label.setStyleSheet("""
            background: rgba(255, 255, 255, 200);
            padding: 12px;
            border-radius: 10px;
            font-size: 12px;
            color: #4A148C;
            border: 2px solid #BA68C8;
        """)
        results_layout.addWidget(self.results_label)
        results_group.setLayout(results_layout)
        left_panel.addWidget(results_group)

        # состояние игры
        state_group = QGroupBox("🎮 Игровое поле")
        state_layout = QVBoxLayout()

        self.game_state_label = QLabel("Добро пожаловать! Введите имя и присоединяйтесь к игре.")
        self.game_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.game_state_label.setStyleSheet("""
            background: rgba(255, 255, 255, 200);
            padding: 18px;
            border-radius: 12px;
            font-size: 13px;
            color: #4A148C;
            border: 2px solid #BA68C8;
        """)
        self.game_state_label.setMinimumHeight(120)

        self.letter_indicator = QLabel("🎯")
        self.letter_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.letter_indicator.setStyleSheet("""
            font-size: 52px;
            font-weight: bold;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #AB47BC, stop:1 #7B1FA2);
            border-radius: 60px;
            padding: 25px;
            border: 4px solid #4A148C;
            color: white;
        """)
        self.letter_indicator.setFixedSize(120, 120)

        letter_layout = QHBoxLayout()
        letter_layout.addStretch()
        letter_layout.addWidget(self.letter_indicator)
        letter_layout.addStretch()

        state_layout.addWidget(self.game_state_label)
        state_layout.addLayout(letter_layout)
        state_group.setLayout(state_layout)
        left_panel.addWidget(state_group)

        # управление
        control_group = QGroupBox("🎯 Управление игрой")
        control_layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("💜 Введите город...")
        self.submit_btn = QPushButton("🎯 Сделать ход")
        self.start_btn = QPushButton("🚀 Начать игру")
        self.reset_btn = QPushButton("🔄 Новая игра")

        input_layout.addWidget(self.city_input)
        input_layout.addWidget(self.submit_btn)
        input_layout.addWidget(self.start_btn)
        input_layout.addWidget(self.reset_btn)

        control_layout.addLayout(input_layout)
        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # использованные города
        cities_group = QGroupBox("🏰 Использованные города")
        cities_layout = QVBoxLayout()

        self.cities_list = QListWidget()
        cities_layout.addWidget(self.cities_list)
        cities_group.setLayout(cities_layout)
        left_panel.addWidget(cities_group)

        left_panel.addStretch()

        # правая панель
        right_panel = QVBoxLayout()

        # подключение
        conn_group = QGroupBox("🔐 Подключение к игре")
        conn_layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("💜 Ваше имя...")
        self.join_btn = QPushButton("🎮 Присоединиться")

        name_layout.addWidget(QLabel("Имя:"))
        name_layout.addWidget(self.name_input)
        name_layout.addWidget(self.join_btn)

        conn_layout.addLayout(name_layout)

        btn_layout = QHBoxLayout()
        self.reconnect_btn = QPushButton("🔁 Переподключиться")
        self.leave_btn = QPushButton("🚪 Покинуть игру")

        btn_layout.addWidget(self.reconnect_btn)
        btn_layout.addWidget(self.leave_btn)

        conn_layout.addLayout(btn_layout)
        conn_group.setLayout(conn_layout)
        right_panel.addWidget(conn_group)

        # комнаты
        rooms_group = QGroupBox("🏯 Игровые комнаты")
        rooms_layout = QVBoxLayout()

        room_input_layout = QHBoxLayout()
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("💜 Название комнаты...")
        self.create_room_btn = QPushButton("➕ Создать")
        self.join_room_btn = QPushButton("🚪 Войти")
        self.refresh_rooms_btn = QPushButton("🔄 Обновить")

        room_input_layout.addWidget(self.room_input)
        room_input_layout.addWidget(self.create_room_btn)
        room_input_layout.addWidget(self.join_room_btn)
        room_input_layout.addWidget(self.refresh_rooms_btn)

        rooms_layout.addLayout(room_input_layout)

        self.rooms_list = QListWidget()
        rooms_layout.addWidget(self.rooms_list)

        self.current_room_label = QLabel("Текущая комната: не выбрана")
        self.current_room_label.setStyleSheet("color: #7B1FA2; font-weight: bold; font-size: 12px;")
        rooms_layout.addWidget(self.current_room_label)

        rooms_group.setLayout(rooms_layout)
        right_panel.addWidget(rooms_group)

        # игроки
        players_group = QGroupBox("👥 Игроки в комнате")
        players_layout = QVBoxLayout()

        self.players_list = QListWidget()
        players_layout.addWidget(self.players_list)
        players_group.setLayout(players_layout)
        right_panel.addWidget(players_group)

        # чат
        chat_group = QGroupBox("💬 Игровой чат")
        chat_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)


        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("💬 Введите сообщение...")
        self.chat_send_btn = QPushButton("📤")
        self.chat_send_btn.setFixedWidth(50)
        chat_input_layout.addWidget(self.chat_input)
        chat_input_layout.addWidget(self.chat_send_btn)
        chat_layout.addLayout(chat_input_layout)

        chat_group.setLayout(chat_layout)
        right_panel.addWidget(chat_group)

        # статус
        status_layout = QHBoxLayout()
        self.status_label = QLabel("❌ Не подключено")
        self.status_label.setStyleSheet("color: #D32F2F; font-weight: bold;")
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet("color: #7B1FA2; font-weight: bold;")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.time_label)
        right_panel.addLayout(status_layout)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 1)

    def connect_signals(self):
        # подключение всех сигналов к слотам
        self.network_client.connected.connect(self.on_connected)
        self.network_client.disconnected.connect(self.on_disconnected)
        self.network_client.message_received.connect(self.on_message_received)

        self.join_btn.clicked.connect(self.join_game)
        self.reconnect_btn.clicked.connect(self.reconnect)
        self.leave_btn.clicked.connect(self.leave_game)
        self.create_room_btn.clicked.connect(self.create_room)
        self.join_room_btn.clicked.connect(self.join_room)
        self.refresh_rooms_btn.clicked.connect(self.refresh_rooms)
        self.submit_btn.clicked.connect(self.submit_city)
        self.start_btn.clicked.connect(self.start_game)
        self.reset_btn.clicked.connect(self.reset_game)

        self.chat_send_btn.clicked.connect(self.send_chat_message)
        self.chat_input.returnPressed.connect(self.send_chat_message)

        self.city_input.returnPressed.connect(self.submit_city)
        self.name_input.returnPressed.connect(self.join_game)

        self.game_timer.timeout.connect(self.update_game_timer)

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)


    def start_timers(self):
        if not self.game_active:
            self.game_time_left = 120
            self.game_active = True
            self.game_timer.start(1000)
            self.update_timer_displays()

    def stop_timers(self):
        self.game_timer.stop()
        self.game_active = False

    def update_game_timer(self):
        if self.game_time_left > 0:
            self.game_time_left -= 1
            self.game_progress.setValue(self.game_time_left)

            minutes = self.game_time_left // 60
            seconds = self.game_time_left % 60
            self.game_timer_label.setText(f"{minutes:02d}:{seconds:02d}")

            if self.game_time_left <= 30:
                self.game_timer_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #D32F2F;")
        else:
            self.end_game()

    def update_timer_displays(self):
        minutes = self.game_time_left // 60
        seconds = self.game_time_left % 60
        self.game_timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def connect_to_server(self):
        self.add_chat_message("💜 СИСТЕМА", "Подключаемся к серверу...")
        if not self.network_client.connect_to_server():
            self.add_chat_message("❌ ОШИБКА", "Не удалось подключиться к серверу!")
            self.status_label.setText("❌ Не подключено")

    def on_connected(self):
        self.add_chat_message("💜 СИСТЕМА", "Успешно подключено к серверу!")
        self.status_label.setText("✅ Подключено")
        self.status_label.setStyleSheet("color: #388E3C; font-weight: bold;")
        self.refresh_rooms()

    def on_disconnected(self):
        self.add_chat_message("❌ ОШИБКА", "Отключено от сервера!")
        self.status_label.setText("❌ Отключено")
        self.status_label.setStyleSheet("color: #D32F2F; font-weight: bold;")
        self.set_controls_enabled(False)
        self.joined = False
        self.stop_timers()

    def on_message_received(self, message):
        msg_type = message.get('type')

        if msg_type == 'success':
            msg = message.get('message', '')
            self.add_chat_message("✅ УСПЕХ", msg)

            if not self.joined:
                self.joined = True
                self.name_input.setEnabled(False)
                self.join_btn.setEnabled(False)
                self.set_controls_enabled(True)

            if 'room_name' in message:
                self.current_room = message['room_name']
                self.current_room_label.setText(f"Текущая комната: {self.current_room}")

        elif msg_type == 'error':
            msg = message.get('message', '')
            self.add_chat_message("❌ ОШИБКА", msg)

        elif msg_type == 'room_state':
            self.update_room_state(message)

        elif msg_type == 'rooms_list':
            self.update_rooms_list(message.get('rooms', []))

        elif msg_type == 'chat_message':
            sender = message.get('sender', 'Неизвестно')
            msg_text = message.get('message', '')
            timestamp = message.get('timestamp', '')

            if timestamp:
                self.chat_display.append(f"[{timestamp}] {sender}: {msg_text}")
            else:
                self.chat_display.append(f"{sender}: {msg_text}")

            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def join_game(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "❌ Ошибка", "Введите имя!")
            return

        self.player_name = name
        message = GameProtocol.create_message('command',
                                              command='join',
                                              player_name=name)
        self.network_client.send_message(message)

    def leave_game(self):
        if not self.joined:
            return

        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы уверены, что хотите покинуть игру?")
        if reply == QMessageBox.StandardButton.Yes:
            message = GameProtocol.create_message('command',
                                                  command='leave',
                                                  player_name=self.player_name)
            self.network_client.send_message(message)
            self.joined = False
            self.set_controls_enabled(False)
            self.name_input.setEnabled(True)
            self.join_btn.setEnabled(True)
            self.stop_timers()

    def create_room(self):
        if not self.joined:
            QMessageBox.warning(self, "❌ Ошибка", "Сначала присоединитесь к игре!")
            return

        room_name = self.room_input.text().strip()
        if not room_name:
            QMessageBox.warning(self, "❌ Ошибка", "Введите название комнаты!")
            return

        message = GameProtocol.create_message('command',
                                              command='create_room',
                                              player_name=self.player_name,
                                              room_name=room_name)
        self.network_client.send_message(message)
        self.room_input.clear()

    def join_room(self):
        if not self.joined:
            QMessageBox.warning(self, "❌ Ошибка", "Сначала присоединитесь к игре!")
            return

        room_name = self.room_input.text().strip()
        if not room_name:
            QMessageBox.warning(self, "❌ Ошибка", "Введите название комнаты!")
            return

        message = GameProtocol.create_message('command',
                                              command='join_room',
                                              player_name=self.player_name,
                                              room_name=room_name)
        self.network_client.send_message(message)
        self.room_input.clear()

    def refresh_rooms(self):
        if not self.joined:
            return

        message = GameProtocol.create_message('command',
                                              command='list_rooms',
                                              player_name=self.player_name)
        self.network_client.send_message(message)

    def start_game(self):
        if not self.joined:
            QMessageBox.warning(self, "❌ Ошибка", "Сначала присоединитесь к игре!")
            return

        city = self.city_input.text().strip()
        if not city:
            QMessageBox.warning(self, "❌ Ошибка", "Введите город для начала игры!")
            return

        message = GameProtocol.create_message('command',
                                              command='start',
                                              player_name=self.player_name,
                                              city=city)
        self.network_client.send_message(message)
        self.city_input.clear()

        self.start_timers()

    def submit_city(self):
        if not self.joined:
            QMessageBox.warning(self, "❌ Ошибка", "Сначала присоединитесь к игре!")
            return

        city = self.city_input.text().strip()
        if not city:
            return

        message = GameProtocol.create_message('command',
                                              command='add_city',
                                              player_name=self.player_name,
                                              city=city)
        self.network_client.send_message(message)
        self.city_input.clear()

    def reset_game(self):
        if not self.joined:
            QMessageBox.warning(self, "❌ Ошибка", "Сначала присоединитесь к игре!")
            return

        message = GameProtocol.create_message('command',
                                              command='reset',
                                              player_name=self.player_name)
        self.network_client.send_message(message)

        self.stop_timers()
        self.game_time_left = 120
        self.update_timer_displays()
        self.game_progress.setValue(120)
        self.game_active = False
        self.player_scores.clear()
        self.results_label.setText("Ожидание начала игры...")

    def reconnect(self):
        self.network_client.disconnect()
        QTimer.singleShot(100, self.connect_to_server)

    def send_chat_message(self):
        # Отправляем сообщением в чат
        if not self.joined:
            QMessageBox.warning(self, "❌ Ошибка", "Сначала присоединитесь к игре!")
            return

        text = self.chat_input.text().strip()
        if not text:
            return

        message = GameProtocol.create_message('command',
                                              command='chat',
                                              player_name=self.player_name,
                                              message=text)
        self.network_client.send_message(message)
        self.chat_input.clear()

    def update_room_state(self, state):
        # Обновляем очки игроков
        scores = state.get('scores', {})
        if scores:
            self.player_scores = scores.copy()

        self.players_list.clear()
        players = state.get('players', [])
        current_player = state.get('current_player')

        # Обновление игроков с очками
        for player in players:
            score = self.player_scores.get(player, 0)
            item_text = f"🎮 {player} - {score} очков"
            if player == current_player:
                item_text += " 🎯 (ходит)"
            if player == self.player_name:
                item_text += " 👑 (вы)"
            self.players_list.addItem(item_text)

        self.cities_list.clear()
        for city in state.get('used_cities', []):
            self.cities_list.addItem(f"🏙️ {city}")

        last_letter = state.get('last_letter')
        game_started = state.get('game_started', False)

        # Обновление очков
        if self.player_scores:
            results_text = "🏆 ТЕКУЩИЕ ОЧКИ:\n\n"
            sorted_scores = sorted(self.player_scores.items(), key=lambda x: x[1], reverse=True)
            for player, score in sorted_scores:
                medal = "🥇" if sorted_scores.index((player, score)) == 0 else "🥈" if sorted_scores.index(
                    (player, score)) == 1 else "🥉" if sorted_scores.index((player, score)) == 2 else "🎯"
                results_text += f"{medal} {player}: {score} очков\n"
            self.results_label.setText(results_text)
        else:
            self.results_label.setText("Ожидание начала игры...")

        if game_started and not self.game_active:
            self.start_timers()

        if game_started and last_letter:
            self.letter_indicator.setText(f"{last_letter.upper()}")

            state_text = f"🎯 Текущая буква: {last_letter.upper()}\n"
            state_text += f"🎮 Ходит: {current_player}\n"

            if current_player == self.player_name:
                state_text += "✅ Ваш ход! Введите город."
                self.game_state_label.setStyleSheet("""
                    background: #E8F5E8;
                    padding: 18px;
                    border-radius: 12px;
                    font-size: 13px;
                    color: #2E7D32;
                    border: 2px solid #4CAF50;
                """)
            else:
                state_text += f"⏳ Ожидаем ход {current_player}"
                self.game_state_label.setStyleSheet("""
                    background: #FFF8E1;
                    padding: 18px;
                    border-radius: 12px;
                    font-size: 13px;
                    color: #FF8F00;
                    border: 2px solid #FFB300;
                """)
        else:
            state_text = "Добро пожаловать! Начните игру, введя город."
            self.game_state_label.setStyleSheet("""
                background: rgba(255, 255, 255, 200);
                padding: 18px;
                border-radius: 12px;
                font-size: 13px;
                color: #4A148C;
                border: 2px solid #BA68C8;
            """)
            self.letter_indicator.setText("🎯")

        self.game_state_label.setText(state_text)

    def update_rooms_list(self, rooms):
        self.rooms_list.clear()
        for room in rooms:
            room_text = f"🏠 {room['name']} ({room['players']} игроков)"
            if room['game_started']:
                room_text += " 🎮"
            self.rooms_list.addItem(room_text)

    def add_chat_message(self, sender, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.append(f"[{timestamp}] {sender}: {message}")

        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_time(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)

    def set_controls_enabled(self, enabled):
        self.room_input.setEnabled(enabled)
        self.create_room_btn.setEnabled(enabled)
        self.join_room_btn.setEnabled(enabled)
        self.refresh_rooms_btn.setEnabled(enabled)
        self.city_input.setEnabled(enabled)
        self.submit_btn.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        self.leave_btn.setEnabled(enabled)

    def end_game(self):
        self.stop_timers()
        self.game_active = False

        # определение победителя
        if self.player_scores:
            sorted_scores = sorted(self.player_scores.items(), key=lambda x: x[1], reverse=True)
            winner = sorted_scores[0][0]
            winner_score = sorted_scores[0][1]

            #результаты
            results_text = "🏆 ИГРА ЗАВЕРШЕНА! 🏆\n\n"
            for i, (player, score) in enumerate(sorted_scores, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🎯"
                results_text += f"{medal} {player}: {score} очков\n"

            self.results_label.setText(results_text)

            # gj,tlbhntkm ehf
            if winner == self.player_name:
                congrats = f"🎉 ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ! 🎉\nСчет: {winner_score} очков"
                self.game_state_label.setText(congrats)
                self.game_state_label.setStyleSheet("""
                    background: #E8F5E8;
                    padding: 18px;
                    border-radius: 12px;
                    font-size: 14px;
                    color: #2E7D32;
                    border: 3px solid #4CAF50;
                    font-weight: bold;
                """)
            else:
                congrats = f"🏆 Победитель: {winner}\nСчет: {winner_score} очков"
                self.game_state_label.setText(congrats)
                self.game_state_label.setStyleSheet("""
                    background: #FFF8E1;
                    padding: 18px;
                    border-radius: 12px;
                    font-size: 14px;
                    color: #FF8F00;
                    border: 3px solid #FFB300;
                    font-weight: bold;
                """)

            self.add_chat_message("🏆 СИСТЕМА", f"Игра завершена! Победитель: {winner} с {winner_score} очками!")

            # показываем окно с результатами
            QMessageBox.information(self, "🏆 Игра завершена!",
                                    f"ПОБЕДИТЕЛЬ: {winner}\n\n{results_text}")
        else:
            self.game_state_label.setText("⏰ Время вышло! Игра завершена.")
            self.add_chat_message("🏆 СИСТЕМА", "Игра завершена! Нет результатов.")

    def closeEvent(self, event):
        if self.joined:
            message = GameProtocol.create_message('command',
                                                  command='leave',
                                                  player_name=self.player_name)
            self.network_client.send_message(message)
        self.network_client.disconnect()
        self.stop_timers()
        event.accept()


def main():
    app = QApplication(sys.argv)

    font = QFont("Arial", 10)
    app.setFont(font)

    client = CitiesClient()
    client.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()