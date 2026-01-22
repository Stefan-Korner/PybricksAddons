import asyncio, json, sys
from bleak import BleakScanner, BleakClient
import PySide6.QtAsyncio as QtAsyncio
from PySide6.QtGui import (QColor, QColorConstants, QFont, QPalette, QTextCursor)
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
                               QHeaderView, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import QSize, Slot

CONFIG_FILE_NAME = "Pybricks_PcConsole.json"
PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"
# Name of the hubs when installing the Pybricks firmware.
HUB_NAMES = ["Technic Hub 1"]
#HUB_NAMES = ["Technic Hub 1", "Technic Hub 2"]
# Prompt to inform the PC that a new command can be processed.
PROMPT = ">>> "
PROMPT_LEN = len(PROMPT)

HUB_DISCONNECTED = 0
HUB_REQUEST_ON = 1
HUB_CONNECTING = 2
HUB_CONNECTED = 3
HUB_RUNNING = 4
HUB_DISCONNECTING = 5

BUTTON_WIDTH = 60
BUTTON_HEIGTH = 30
INPUT_WIDTH = 60
INPUT_HEIGTH = 30
TELEMETRY_ROWS = 5
TELEMETRY_COLUMNS = 8

def set_label_color(label, color_name):
    color = getattr(QColorConstants, color_name)
    pal = label.palette()
    pal.setColor(QPalette.Window, color)
    label.setPalette(pal)
    label.update()

def set_button_color(button, color_name):
    color = getattr(QColorConstants, color_name)
    pal = button.palette()
    pal.setColor(QPalette.Button, color)
    button.setPalette(pal)
    button.update()

def set_button_text_color(button, color_name):
    color = getattr(QColorConstants, color_name)
    # color.name() returns the RGB value
    button.setStyleSheet("QPushButton {color: " + color.name() + ";}")

# Encapsulates the ble client to remote control a hub.
class HubClient:

    def __init__(self, ble_client, event_char_uuid, hub_logger):
        self.ble_client = ble_client
        self.ready_event = asyncio.Event()
        self.event_char_uuid = event_char_uuid
        self.hub_logger = hub_logger
        self.send_is_ready = False
        self.response_buffer = ""

    # Checks if a prompt is in the response buffer and set the ready event
    def check_prompt(self):
        if len(self.response_buffer) >= PROMPT_LEN:
            if PROMPT in self.response_buffer:
                self.ready_event.set()

    # Callback for receiving data.
    def handle_rx(self, _, data: bytearray):
        # "write stdout" event (0x01)
        if data[0] == 0x01:
            payload = data[1:].decode("utf-8")
            self.handle_next_payload(payload)

    # Callback for receiving next payload characters.
    def handle_next_payload(self, payload):
        for next_char in payload:
            if next_char == "\r":
                # ignore the return before the newline
                pass
            elif next_char == "\n":
                # Complete line received: check if prompt
                self.check_prompt()
                self.handle_response_line(self.response_buffer)
                self.hub_logger.log_hub("")
                self.response_buffer = ""
            else:
                self.hub_logger.log_hub(next_char, end="")
                self.response_buffer += next_char
        # Characters are received and added to response buffer: check if prompt
        self.check_prompt()

    # Callback for receiving a complete response line.
    def handle_response_line(self, response_line):
        pass

    # Subscribe to notifications from the hub.
    async def start_notify(self):
        await self.ble_client.start_notify(self.event_char_uuid, self.handle_rx)

    # Waits until a ready response has been sent from the hub.
    async def wait_send_ready(self):
        if not self.send_is_ready:
            # Wait for hub to say that it is ready to receive data
            await self.ready_event.wait()
            # Prepare for the next ready event.
            self.ready_event.clear()
            self.send_is_ready = True

    # Sends data to the hub.
    async def send(self, data):
        await self.wait_send_ready()
        # Send the data to the hub.
        await self.ble_client.write_gatt_char(
            self.event_char_uuid,
            b"\x06" + data + b"\r",  # prepend "write stdin" command (0x06) and add "\r"
            response=True
        )
        self.send_is_ready = False

class RemoteConsole(QDialog):
    def __init__(self, console_config_dict):
        super().__init__()
        # model
        ObjFromDict = type("ObjFromDict", (object,), console_config_dict)
        self.console_config = ObjFromDict()
        self.hub_connect_state = HUB_DISCONNECTED
        self.device = None
        self.client = None
        self.hub_client = None
        # view - top frame
        self.top_frame = QFrame()
        self.label_hub_name = QLabel(self.console_config.hubName)
        self.label_connect = QLabel("disconnected")
        self.label_connect.setAutoFillBackground(True)
        set_label_color(self.label_connect, "Gray")
        self.button_connect = QPushButton("connect to hub")
        self.button_connect.setAutoDefault(False)
        self.button_connect.clicked.connect(self.button_connect_clicked)
        self.top_frame.setFrameShadow(QFrame.Sunken)
        self.top_frame.setFrameShape(QFrame.Panel)
        self.top_layout = QGridLayout()
        self.top_layout.addWidget(self.label_hub_name, 0, 0, 1, 1)
        self.top_layout.addWidget(self.label_connect, 1, 0, 1, 1)
        self.top_layout.addWidget(self.button_connect, 2, 0, 1, 1)
        self.top_frame.setLayout(self.top_layout)
        # view - telemetry frame
        self.telemetry_frame = QFrame()
        self.telemetry_label = QLabel("Telemetry")
        self.telemetry_table = QTableWidget(TELEMETRY_ROWS, TELEMETRY_COLUMNS)
        self.telemetry_table.setHorizontalHeaderLabels(
            ["Name              ", "Value                "] * int(TELEMETRY_COLUMNS / 2))
        header = self.telemetry_table.horizontalHeader()
        for column in range(TELEMETRY_COLUMNS):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        parameter1col1 = self.console_config.telemetry["parameter1col1"]
        parameter2col1 = self.console_config.telemetry["parameter2col1"]
        parameter3col1 = self.console_config.telemetry["parameter3col1"]
        parameter4col1 = self.console_config.telemetry["parameter4col1"]
        parameter5col1 = self.console_config.telemetry["parameter5col1"]
        parameter1col2 = self.console_config.telemetry["parameter1col2"]
        parameter2col2 = self.console_config.telemetry["parameter2col2"]
        parameter3col2 = self.console_config.telemetry["parameter3col2"]
        parameter4col2 = self.console_config.telemetry["parameter4col2"]
        parameter5col2 = self.console_config.telemetry["parameter5col2"]
        parameter1col3 = self.console_config.telemetry["parameter1col3"]
        parameter2col3 = self.console_config.telemetry["parameter2col3"]
        parameter3col3 = self.console_config.telemetry["parameter3col3"]
        parameter4col3 = self.console_config.telemetry["parameter4col3"]
        parameter5col3 = self.console_config.telemetry["parameter5col3"]
        parameter1col4 = self.console_config.telemetry["parameter1col4"]
        parameter2col4 = self.console_config.telemetry["parameter2col4"]
        parameter3col4 = self.console_config.telemetry["parameter3col4"]
        parameter4col4 = self.console_config.telemetry["parameter4col4"]
        parameter5col4 = self.console_config.telemetry["parameter5col4"]
        self.telemetry_items = {
            parameter1col1: QTableWidgetItem(),
            parameter2col1: QTableWidgetItem(),
            parameter3col1: QTableWidgetItem(),
            parameter4col1: QTableWidgetItem(),
            parameter5col1: QTableWidgetItem(),
            parameter1col2: QTableWidgetItem(),
            parameter2col2: QTableWidgetItem(),
            parameter3col2: QTableWidgetItem(),
            parameter4col2: QTableWidgetItem(),
            parameter5col2: QTableWidgetItem(),
            parameter1col3: QTableWidgetItem(),
            parameter2col3: QTableWidgetItem(),
            parameter3col3: QTableWidgetItem(),
            parameter4col3: QTableWidgetItem(),
            parameter5col3: QTableWidgetItem(),
            parameter1col4: QTableWidgetItem(),
            parameter2col4: QTableWidgetItem(),
            parameter3col4: QTableWidgetItem(),
            parameter4col4: QTableWidgetItem(),
            parameter5col4: QTableWidgetItem()
        }
        self.telemetry_table.setItem(0, 0, QTableWidgetItem(parameter1col1))
        self.telemetry_table.setItem(1, 0, QTableWidgetItem(parameter2col1))
        self.telemetry_table.setItem(2, 0, QTableWidgetItem(parameter3col1))
        self.telemetry_table.setItem(3, 0, QTableWidgetItem(parameter4col1))
        self.telemetry_table.setItem(4, 0, QTableWidgetItem(parameter5col1))
        self.telemetry_table.setItem(0, 1, self.telemetry_items[parameter1col1])
        self.telemetry_table.setItem(1, 1, self.telemetry_items[parameter2col1])
        self.telemetry_table.setItem(2, 1, self.telemetry_items[parameter3col1])
        self.telemetry_table.setItem(3, 1, self.telemetry_items[parameter4col1])
        self.telemetry_table.setItem(4, 1, self.telemetry_items[parameter5col1])
        self.telemetry_table.setItem(0, 2, QTableWidgetItem(parameter1col2))
        self.telemetry_table.setItem(1, 2, QTableWidgetItem(parameter2col2))
        self.telemetry_table.setItem(2, 2, QTableWidgetItem(parameter3col2))
        self.telemetry_table.setItem(3, 2, QTableWidgetItem(parameter4col2))
        self.telemetry_table.setItem(4, 2, QTableWidgetItem(parameter5col2))
        self.telemetry_table.setItem(0, 3, self.telemetry_items[parameter1col2])
        self.telemetry_table.setItem(1, 3, self.telemetry_items[parameter2col2])
        self.telemetry_table.setItem(2, 3, self.telemetry_items[parameter3col2])
        self.telemetry_table.setItem(3, 3, self.telemetry_items[parameter4col2])
        self.telemetry_table.setItem(4, 3, self.telemetry_items[parameter5col2])
        self.telemetry_table.setItem(0, 4, QTableWidgetItem(parameter1col3))
        self.telemetry_table.setItem(1, 4, QTableWidgetItem(parameter2col3))
        self.telemetry_table.setItem(2, 4, QTableWidgetItem(parameter3col3))
        self.telemetry_table.setItem(3, 4, QTableWidgetItem(parameter4col3))
        self.telemetry_table.setItem(4, 4, QTableWidgetItem(parameter5col3))
        self.telemetry_table.setItem(0, 5, self.telemetry_items[parameter1col3])
        self.telemetry_table.setItem(1, 5, self.telemetry_items[parameter2col3])
        self.telemetry_table.setItem(2, 5, self.telemetry_items[parameter3col3])
        self.telemetry_table.setItem(3, 5, self.telemetry_items[parameter4col3])
        self.telemetry_table.setItem(4, 5, self.telemetry_items[parameter5col3])
        self.telemetry_table.setItem(0, 6, QTableWidgetItem(parameter1col4))
        self.telemetry_table.setItem(1, 6, QTableWidgetItem(parameter2col4))
        self.telemetry_table.setItem(2, 6, QTableWidgetItem(parameter3col4))
        self.telemetry_table.setItem(3, 6, QTableWidgetItem(parameter4col4))
        self.telemetry_table.setItem(4, 6, QTableWidgetItem(parameter5col4))
        self.telemetry_table.setItem(0, 7, self.telemetry_items[parameter1col4])
        self.telemetry_table.setItem(1, 7, self.telemetry_items[parameter2col4])
        self.telemetry_table.setItem(2, 7, self.telemetry_items[parameter3col4])
        self.telemetry_table.setItem(3, 7, self.telemetry_items[parameter4col4])
        self.telemetry_table.setItem(4, 7, self.telemetry_items[parameter5col4])
        self.telemetry_frame.setFrameShadow(QFrame.Sunken)
        self.telemetry_frame.setFrameShape(QFrame.Panel)
        self.telemetry_layout = QGridLayout()
        self.telemetry_layout.addWidget(self.telemetry_label, 0, 0)
        self.telemetry_layout.addWidget(self.telemetry_table, 1, 0)
        self.telemetry_frame.setLayout(self.telemetry_layout)
        # view - left buttons frame
        self.left_buttons_frame = QFrame()
        self.button_f1 = QPushButton(self.console_config.f1["label"])
        self.button_f1.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f1.setAutoDefault(False)
        set_button_color(self.button_f1, self.console_config.f1["color"])
        set_button_text_color(self.button_f1, self.console_config.f1["textColor"])
        self.button_f1.clicked.connect(self.button_f1_clicked)
        self.input_f1 = QLineEdit()
        self.input_f1.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f2 = QPushButton(self.console_config.f2["label"])
        self.button_f2.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f2.setAutoDefault(False)
        set_button_color(self.button_f2, self.console_config.f2["color"])
        set_button_text_color(self.button_f2, self.console_config.f2["textColor"])
        self.button_f2.clicked.connect(self.button_f2_clicked)
        self.input_f2 = QLineEdit()
        self.input_f2.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f3 = QPushButton(self.console_config.f3["label"])
        self.button_f3.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f3.setAutoDefault(False)
        set_button_color(self.button_f3, self.console_config.f3["color"])
        set_button_text_color(self.button_f3, self.console_config.f3["textColor"])
        self.button_f3.clicked.connect(self.button_f3_clicked)
        self.input_f3 = QLineEdit()
        self.input_f3.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f4 = QPushButton(self.console_config.f4["label"])
        self.button_f4.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f4.setAutoDefault(False)
        set_button_color(self.button_f4, self.console_config.f4["color"])
        set_button_text_color(self.button_f4, self.console_config.f4["textColor"])
        self.button_f4.clicked.connect(self.button_f4_clicked)
        self.input_f4 = QLineEdit()
        self.input_f4.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f5 = QPushButton(self.console_config.f5["label"])
        self.button_f5.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f5.setAutoDefault(False)
        set_button_color(self.button_f5, self.console_config.f5["color"])
        set_button_text_color(self.button_f5, self.console_config.f5["textColor"])
        self.button_f5.clicked.connect(self.button_f5_clicked)
        self.input_f5 = QLineEdit()
        self.input_f5.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f6 = QPushButton(self.console_config.f6["label"])
        self.button_f6.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f6.setAutoDefault(False)
        set_button_color(self.button_f6, self.console_config.f6["color"])
        set_button_text_color(self.button_f6, self.console_config.f6["textColor"])
        self.button_f6.clicked.connect(self.button_f6_clicked)
        self.input_f6 = QLineEdit()
        self.input_f6.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f7 = QPushButton(self.console_config.f7["label"])
        self.button_f7.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f7.setAutoDefault(False)
        set_button_color(self.button_f7, self.console_config.f7["color"])
        set_button_text_color(self.button_f7, self.console_config.f7["textColor"])
        self.button_f7.clicked.connect(self.button_f7_clicked)
        self.input_f7 = QLineEdit()
        self.input_f7.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f8 = QPushButton(self.console_config.f8["label"])
        self.button_f8.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f8.setAutoDefault(False)
        set_button_color(self.button_f8, self.console_config.f8["color"])
        set_button_text_color(self.button_f8, self.console_config.f8["textColor"])
        self.button_f8.clicked.connect(self.button_f8_clicked)
        self.input_f8 = QLineEdit()
        self.input_f8.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f9 = QPushButton(self.console_config.f9["label"])
        self.button_f9.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f9.setAutoDefault(False)
        set_button_color(self.button_f9, self.console_config.f9["color"])
        set_button_text_color(self.button_f9, self.console_config.f9["textColor"])
        self.button_f9.clicked.connect(self.button_f9_clicked)
        self.input_f9 = QLineEdit()
        self.input_f9.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f10 = QPushButton(self.console_config.f10["label"])
        self.button_f10.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f10.setAutoDefault(False)
        set_button_color(self.button_f10, self.console_config.f10["color"])
        set_button_text_color(self.button_f10, self.console_config.f10["textColor"])
        self.button_f10.clicked.connect(self.button_f10_clicked)
        self.input_f10 = QLineEdit()
        self.input_f10.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f11 = QPushButton(self.console_config.f11["label"])
        self.button_f11.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f11.setAutoDefault(False)
        set_button_color(self.button_f11, self.console_config.f11["color"])
        set_button_text_color(self.button_f11, self.console_config.f11["textColor"])
        self.button_f11.clicked.connect(self.button_f11_clicked)
        self.input_f11 = QLineEdit()
        self.input_f11.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f12 = QPushButton(self.console_config.f12["label"])
        self.button_f12.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f12.setAutoDefault(False)
        set_button_color(self.button_f12, self.console_config.f12["color"])
        set_button_text_color(self.button_f12, self.console_config.f12["textColor"])
        self.button_f12.clicked.connect(self.button_f12_clicked)
        self.input_f12 = QLineEdit()
        self.input_f12.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.left_buttons_frame.setFrameShadow(QFrame.Sunken)
        self.left_buttons_frame.setFrameShape(QFrame.Panel)
        self.left_buttons_layout = QGridLayout()
        self.left_buttons_layout.addWidget(self.button_f1, 0, 0)
        self.left_buttons_layout.addWidget(self.input_f1, 0, 1)
        self.left_buttons_layout.addWidget(self.button_f2, 0, 2)
        self.left_buttons_layout.addWidget(self.input_f2, 0, 3)
        self.left_buttons_layout.addWidget(self.button_f3, 0, 4)
        self.left_buttons_layout.addWidget(self.input_f3, 0, 5)
        self.left_buttons_layout.addWidget(self.button_f4, 0, 6)
        self.left_buttons_layout.addWidget(self.input_f4, 0, 7)
        self.left_buttons_layout.addWidget(self.button_f5, 1, 0)
        self.left_buttons_layout.addWidget(self.input_f5, 1, 1)
        self.left_buttons_layout.addWidget(self.button_f6, 1, 2)
        self.left_buttons_layout.addWidget(self.input_f6, 1, 3)
        self.left_buttons_layout.addWidget(self.button_f7, 1, 4)
        self.left_buttons_layout.addWidget(self.input_f7, 1, 5)
        self.left_buttons_layout.addWidget(self.button_f8, 1, 6)
        self.left_buttons_layout.addWidget(self.input_f8, 1, 7)
        self.left_buttons_layout.addWidget(self.button_f9, 2, 0)
        self.left_buttons_layout.addWidget(self.input_f9, 2, 1)
        self.left_buttons_layout.addWidget(self.button_f10, 2, 2)
        self.left_buttons_layout.addWidget(self.input_f10, 2, 3)
        self.left_buttons_layout.addWidget(self.button_f11, 2, 4)
        self.left_buttons_layout.addWidget(self.input_f11, 2, 5)
        self.left_buttons_layout.addWidget(self.button_f12, 2, 6)
        self.left_buttons_layout.addWidget(self.input_f12, 2, 7)
        self.left_buttons_frame.setLayout(self.left_buttons_layout)
        # view - right buttons frame
        self.right_buttons_frame = QFrame()
        self.button_left_plus = QPushButton("+")
        self.button_left_plus.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_left_plus.setAutoDefault(False)
        self.button_left_plus.clicked.connect(self.button_left_plus_clicked)
        self.button_left = QPushButton("L")
        self.button_left.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_left.setAutoDefault(False)
        set_button_color(self.button_left, "Red")
        self.button_left.clicked.connect(self.button_left_clicked)
        self.button_left_minus = QPushButton("-")
        self.button_left_minus.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_left_minus.setAutoDefault(False)
        self.button_left_minus.clicked.connect(self.button_left_minus_clicked)
        self.button_middle = QPushButton("M")
        self.button_middle.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_middle.setAutoDefault(False)
        set_button_color(self.button_middle, "Green")
        self.button_middle.clicked.connect(self.button_middle_clicked)
        self.button_right_plus = QPushButton("+")
        self.button_right_plus.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_right_plus.setAutoDefault(False)
        self.button_right_plus.clicked.connect(self.button_right_plus_clicked)
        self.button_right = QPushButton("R")
        self.button_right.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_right.setAutoDefault(False)
        set_button_color(self.button_right, "Red")
        self.button_right.clicked.connect(self.button_right_clicked)
        self.button_right_minus = QPushButton("-")
        self.button_right_minus.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_right_minus.setAutoDefault(False)
        self.button_right_minus.clicked.connect(self.button_right_minus_clicked)
        self.right_buttons_frame.setFrameShadow(QFrame.Sunken)
        self.right_buttons_frame.setFrameShape(QFrame.Panel)
        self.right_buttons_layout = QGridLayout()
        self.right_buttons_layout.addWidget(self.button_left_plus, 0, 0)
        self.right_buttons_layout.addWidget(self.button_left, 1, 0)
        self.right_buttons_layout.addWidget(self.button_left_minus, 2, 0)
        self.right_buttons_layout.addWidget(self.button_middle, 1, 1)
        self.right_buttons_layout.addWidget(self.button_right_plus, 0, 2)
        self.right_buttons_layout.addWidget(self.button_right, 1, 2)
        self.right_buttons_layout.addWidget(self.button_right_minus, 2, 2)
        self.right_buttons_frame.setLayout(self.right_buttons_layout)
        # view - bottom frame
        self.bottom_frame = QFrame()
        self.label_local = QLabel("local")
        self.local_log = QPlainTextEdit()
        self.label_hub = QLabel("hub")
        self.hub_log = QPlainTextEdit()
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self.command_input_return_pressed)
        courier_font = QFont("Courier")
        self.hub_log.setFont(courier_font)
        self.bottom_frame.setFrameShadow(QFrame.Sunken)
        self.bottom_frame.setFrameShape(QFrame.Panel)
        self.bottom_layout = QGridLayout()
        self.bottom_layout.addWidget(self.label_local, 0, 0, 1, 2)
        self.bottom_layout.addWidget(self.local_log, 1, 0, 2, 2)
        self.bottom_layout.addWidget(self.label_hub, 0, 2, 1, 1)
        self.bottom_layout.addWidget(self.hub_log, 1, 2, 1, 1)
        self.bottom_layout.addWidget(self.command_input, 2, 2, 1, 1)
        self.bottom_frame.setLayout(self.bottom_layout)
        # view - toplevel
        self.layout = QGridLayout()
        self.layout.addWidget(self.top_frame, 0, 0, 1, 2)
        self.layout.addWidget(self.telemetry_frame, 1, 0, 1, 2)
        self.layout.addWidget(self.left_buttons_frame, 2, 0, 1, 1)
        self.layout.addWidget(self.right_buttons_frame, 2, 1, 1, 1)
        self.layout.addWidget(self.bottom_frame, 3, 0, 1, 2)
        self.setLayout(self.layout)

    # Logs text to the local logger.
    def log_local(self, text, end="\n"):
        self.local_log.moveCursor(QTextCursor.End)
        self.local_log.insertPlainText(text + end)

    # Logs text to the hub logger.
    def log_hub(self, text, end="\n"):
        self.hub_log.moveCursor(QTextCursor.End)
        self.hub_log.insertPlainText(text + end)

    async def start_hub(self):
        self.button_connect.setText("Click when hub is started")
        self.label_connect.setText("Start hub with hub button")
        set_label_color(self.label_connect, "Cyan")
        self.hub_connect_state = HUB_REQUEST_ON

    async def connect_hub(self):
        self.hub_connect_state = HUB_CONNECTING
        self.log_local("Hub is started")
        self.button_connect.setText("")
        self.label_connect.setText("Scan to find the hub")
        set_label_color(self.label_connect, "Magenta")

        # Do a Bluetooth scan to find the hub.
        hub_name = self.console_config.hubName
        device = await BleakScanner.find_device_by_name(hub_name)
        if device is None:
            self.hub_connect_state = HUB_DISCONNECTED
            self.log_local(f"Could not find hub with name: {hub_name}")
            self.button_connect.setText("connect to hub")
            self.label_connect.setText("disconnected")
            set_label_color(self.label_connect, "Gray")
            return
        # Hub found.
        self.log_local(f"Hub found with name: {hub_name}")

        # Connect to the hub.
        self.client = BleakClient(device)
        await self.client.connect()
        self.log_local("Hub is connected")
        self.device = device

        # Initialize the sender channel to the hub.
        self.hub_client = HubClient(self.client, PYBRICKS_COMMAND_EVENT_CHAR_UUID, self)

        # Subscribe to notifications from the hub.
        await self.hub_client.start_notify()
        self.hub_connect_state = HUB_CONNECTED
        self.log_local("Hub notifications started")
        # Tell user to start program on the hub.
        self.label_connect.setText("Start program with hub button")
        set_label_color(self.label_connect, "Yellow")

        # Waits until a ready response has been sent from the hub.
        await self.hub_client.wait_send_ready()
        self.hub_connect_state = HUB_RUNNING
        self.log_local("Hub running.")
        self.button_connect.setText("disconnect from hub")
        self.label_connect.setText("running")
        set_label_color(self.label_connect, "Green")

    async def disconnect_hub(self):
        self.hub_connect_state = HUB_DISCONNECTING
        set_label_color(self.label_connect, "Yellow")
        self.button_connect.setText("")
        for i in range(3):
            self.label_connect.setText("disconnecting" + ("." * i))
            await asyncio.sleep(1)
        self.hub_connect_state = HUB_DISCONNECTED
        self.label_connect.setText("disconnected")
        set_label_color(self.label_connect, "Gray")
        self.button_connect.setText("connect to hub")

    def create_send_task(self, command, arg=""):
        if self.hub_connect_state != HUB_RUNNING:
            self.log_local("error: not connected to hub")
            return
        if len(arg) > 0:
            command += " " + arg
        binary_command = command.encode("ascii")
        asyncio.create_task(self.hub_client.send(binary_command))

    @Slot()
    def button_connect_clicked(self):
        if self.hub_connect_state == HUB_DISCONNECTED:
            asyncio.create_task(self.start_hub())
        elif self.hub_connect_state == HUB_REQUEST_ON:
            asyncio.create_task(self.connect_hub())
        elif self.hub_connect_state == HUB_RUNNING:
            asyncio.create_task(self.disconnect_hub())

    @Slot()
    def button_f1_clicked(self):
        text = self.input_f1.text()
        self.create_send_task(self.console_config.f1["command"], text)

    @Slot()
    def button_f2_clicked(self):
        text = self.input_f2.text()
        self.create_send_task(self.console_config.f2["command"], text)

    @Slot()
    def button_f3_clicked(self):
        text = self.input_f3.text()
        self.create_send_task(self.console_config.f3["command"], text)

    @Slot()
    def button_f4_clicked(self):
        text = self.input_f4.text()
        self.create_send_task(self.console_config.f4["command"], text)

    @Slot()
    def button_f5_clicked(self):
        text = self.input_f5.text()
        self.create_send_task(self.console_config.f5["command"], text)

    @Slot()
    def button_f6_clicked(self):
        text = self.input_f6.text()
        self.create_send_task(self.console_config.f6["command"], text)

    @Slot()
    def button_f7_clicked(self):
        text = self.input_f7.text()
        self.create_send_task(self.console_config.f7["command"], text)

    @Slot()
    def button_f8_clicked(self):
        text = self.input_f8.text()
        self.create_send_task(self.console_config.f8["command"], text)

    @Slot()
    def button_f9_clicked(self):
        text = self.input_f9.text()
        self.create_send_task(self.console_config.f9["command"], text)

    @Slot()
    def button_f10_clicked(self):
        text = self.input_f10.text()
        self.create_send_task(self.console_config.f10["command"], text)

    @Slot()
    def button_f11_clicked(self):
        text = self.input_f11.text()
        self.create_send_task(self.console_config.f11["command"], text)

    @Slot()
    def button_f12_clicked(self):
        text = self.input_f12.text()
        self.create_send_task(self.console_config.f12["command"], text)

    @Slot()
    def button_left_plus_clicked(self):
        self.create_send_task(self.console_config.leftPlus["command"])

    @Slot()
    def button_left_clicked(self):
        self.create_send_task(self.console_config.left["command"])

    @Slot()
    def button_left_minus_clicked(self):
        self.create_send_task(self.console_config.leftMinus["command"])

    @Slot()
    def button_middle_clicked(self):
        self.create_send_task(self.console_config.middle["command"])

    @Slot()
    def button_right_plus_clicked(self):
        self.create_send_task(self.console_config.rightPlus["command"])

    @Slot()
    def button_right_clicked(self):
        self.create_send_task(self.console_config.right["command"])

    @Slot()
    def button_right_minus_clicked(self):
        self.create_send_task(self.console_config.rightMinus["command"])

    @Slot()
    def command_input_return_pressed(self):
        hub_command = self.command_input.text()
        self.command_input.setText("")
        self.create_send_task(hub_command)

# Run the main async program.
if __name__ == "__main__":
    # Read the configuration JSON file
    try:
        with open(CONFIG_FILE_NAME, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Cannot read configuration file: {e}")
    else:
        # Start the RemoteConsole
        app = QApplication(sys.argv)
        # Remote consoles must be saved in the global list,
        # otherwiese the garbage collector deletes it
        remote_consoles = []
        for console_config_dict in config:
            remote_console = RemoteConsole(console_config_dict)
            remote_console.show()
            remote_consoles.append(remote_console)
        QtAsyncio.run(handle_sigint=True)