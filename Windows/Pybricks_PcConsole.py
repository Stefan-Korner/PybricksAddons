import asyncio, sys
from bleak import BleakScanner, BleakClient
import PySide6.QtAsyncio as QtAsyncio
from PySide6.QtGui import (QColor, QColorConstants, QPalette, QTextCursor)
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
                               QLabel, QLineEdit, QPlainTextEdit, QPushButton)
from PySide6.QtCore import QSize, Slot

PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"
# Name of the hubs when installing the Pybricks firmware.
HUB_NAMES = ["Technic Hub 1"]
#HUB_NAMES = ["Technic Hub 1", "Technic Hub 2"]
# Prompt to inform the PC that a new command can be processed.
PROMPT = b">>> "
PROMPT_LEN = len(PROMPT)

F1_COMMMAND = b"F1_"
F2_COMMMAND = b"F2_"
F3_COMMMAND = b"F3_"
F4_COMMMAND = b"F4_"
F5_COMMMAND = b"F5_"
F6_COMMMAND = b"F6_"
F7_COMMMAND = b"F7_"
F8_COMMMAND = b"F8_"
F9_COMMMAND = b"F9_"
F10_COMMMAND = b"F10"
F11_COMMMAND = b"F11"
F12_COMMMAND = b"F12"
BUTTON_LEFT_PLUS_COMMAND = b"L_U"
BUTTON_LEFT_COMMAND = b"L__"
BUTTON_LEFT_MINUS_COMMAND = b"L_D"
BUTTON_MIDDLE_COMMAND = b"M__"
BUTTON_RIGHT_PLUS_COMMAND = b"R_U"
BUTTON_RIGHT_COMMAND = b"R__"
BUTTON_RIGHT_MINUS_COMMAND = b"R_D"

BUTTON_WIDTH = 60
BUTTON_HEIGTH = 30
INPUT_WIDTH = 60
INPUT_HEIGTH = 30

HUB_DISCONNECTED = 0
HUB_REQUEST_ON = 1
HUB_CONNECTING = 2
HUB_CONNECTED = 3
HUB_RUNNING = 4
HUB_DISCONNECTING = 5

def set_label_color(label, color):
    pal = label.palette()
    pal.setColor(QPalette.Window, color)
    label.setPalette(pal)
    label.update()

def set_button_color(button, color):
    pal = button.palette()
    pal.setColor(QPalette.Button, color)
    button.setPalette(pal)
    button.update()

# Encapsulates the ble client to remote control a hub.
class HubClient:

    def __init__(self, ble_client, event_char_uuid, logger=None):
        self.ble_client = ble_client
        self.ready_event = asyncio.Event()
        self.event_char_uuid = event_char_uuid
        self.logger = logger
        self.send_is_ready = False

    # Logs text to a logger if a logger is used.
    def log_text(self, text, end="\n"):
        if self.logger:
            self.logger.log_text(text, end)

    # Callback for receiving data.
    def handle_rx(self, _, data: bytearray):
        # "write stdout" event (0x01)
        if data[0] == 0x01:
            payload = data[1:]
            self.log_text(payload.decode("utf-8"), end="")
            if len(payload) >= PROMPT_LEN:
                if payload[-PROMPT_LEN:] == PROMPT:
                    self.log_text("")
                    self.ready_event.set()

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
    def __init__(self, hub_name):
        super().__init__()
        # view - top frame
        self.top_frame = QFrame()
        self.label_hub_name = QLabel(hub_name)
        self.label_connect = QLabel("disconnected")
        self.label_connect.setAutoFillBackground(True)
        set_label_color(self.label_connect, QColorConstants.Gray)
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
        # view - left buttons frame
        self.left_buttons_frame = QFrame()
        self.button_f1 = QPushButton("F1")
        self.button_f1.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f1.setAutoDefault(False)
        self.button_f1.clicked.connect(self.button_f1_clicked)
        self.input_f1 = QLineEdit()
        self.input_f1.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f2 = QPushButton("F2")
        self.button_f2.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f2.setAutoDefault(False)
        self.button_f2.clicked.connect(self.button_f2_clicked)
        self.input_f2 = QLineEdit()
        self.input_f2.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f3 = QPushButton("F3")
        self.button_f3.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f3.setAutoDefault(False)
        self.button_f3.clicked.connect(self.button_f3_clicked)
        self.input_f3 = QLineEdit()
        self.input_f3.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f4 = QPushButton("F4")
        self.button_f4.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f4.setAutoDefault(False)
        self.button_f4.clicked.connect(self.button_f4_clicked)
        self.input_f4 = QLineEdit()
        self.input_f4.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f5 = QPushButton("F5")
        self.button_f5.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f5.setAutoDefault(False)
        self.button_f5.clicked.connect(self.button_f5_clicked)
        self.input_f5 = QLineEdit()
        self.input_f5.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f6 = QPushButton("F6")
        self.button_f6.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f6.setAutoDefault(False)
        self.button_f6.clicked.connect(self.button_f6_clicked)
        self.input_f6 = QLineEdit()
        self.input_f6.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f7 = QPushButton("F7")
        self.button_f7.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f7.setAutoDefault(False)
        self.button_f7.clicked.connect(self.button_f7_clicked)
        self.input_f7 = QLineEdit()
        self.input_f7.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f8 = QPushButton("F8")
        self.button_f8.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f8.setAutoDefault(False)
        self.button_f8.clicked.connect(self.button_f8_clicked)
        self.input_f8 = QLineEdit()
        self.input_f8.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f9 = QPushButton("F9")
        self.button_f9.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f9.setAutoDefault(False)
        self.button_f9.clicked.connect(self.button_f9_clicked)
        self.input_f9 = QLineEdit()
        self.input_f9.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f10 = QPushButton("F10")
        self.button_f10.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f10.setAutoDefault(False)
        self.button_f10.clicked.connect(self.button_f10_clicked)
        self.input_f10 = QLineEdit()
        self.input_f10.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f11 = QPushButton("F11")
        self.button_f11.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f11.setAutoDefault(False)
        self.button_f11.clicked.connect(self.button_f11_clicked)
        self.input_f11 = QLineEdit()
        self.input_f11.setFixedSize(QSize(INPUT_WIDTH, INPUT_HEIGTH))
        self.button_f12 = QPushButton("F12")
        self.button_f12.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_f12.setAutoDefault(False)
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
        set_button_color(self.button_left, QColorConstants.Red)
        self.button_left.clicked.connect(self.button_left_clicked)
        self.button_left_minus = QPushButton("-")
        self.button_left_minus.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_left_minus.setAutoDefault(False)
        self.button_left_minus.clicked.connect(self.button_left_minus_clicked)
        self.button_middle = QPushButton("M")
        self.button_middle.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_middle.setAutoDefault(False)
        set_button_color(self.button_middle, QColorConstants.Green)
        self.button_middle.clicked.connect(self.button_middle_clicked)
        self.button_right_plus = QPushButton("+")
        self.button_right_plus.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_right_plus.setAutoDefault(False)
        self.button_right_plus.clicked.connect(self.button_right_plus_clicked)
        self.button_right = QPushButton("R")
        self.button_right.setFixedSize(QSize(BUTTON_WIDTH, BUTTON_HEIGTH))
        self.button_right.setAutoDefault(False)
        set_button_color(self.button_right, QColorConstants.Red)
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
        self.line_input = QLineEdit()
        self.line_input.returnPressed.connect(self.line_input_return_pressed)
        self.text_log = QPlainTextEdit()
        self.bottom_frame.setFrameShadow(QFrame.Sunken)
        self.bottom_frame.setFrameShape(QFrame.Panel)
        self.bottom_layout = QGridLayout()
        self.bottom_layout.addWidget(self.line_input, 4, 0, 1, 2)
        self.bottom_layout.addWidget(self.text_log, 5, 0, 1, 2)
        self.bottom_frame.setLayout(self.bottom_layout)
        # view - toplevel
        self.layout = QGridLayout()
        self.layout.addWidget(self.top_frame, 0, 0, 1, 2)
        self.layout.addWidget(self.left_buttons_frame, 1, 0, 1, 1)
        self.layout.addWidget(self.right_buttons_frame, 1, 1, 1, 1)
        self.layout.addWidget(self.bottom_frame, 2, 0, 1, 2)
        self.setLayout(self.layout)
        # model
        self.hub_name = hub_name
        self.hub_connect_state = HUB_DISCONNECTED
        self.device = None
        self.client = None
        self.hub_client = None

    # Logs text to the logger.
    def log_text(self, text, end="\n"):
        self.text_log.moveCursor(QTextCursor.End)
        self.text_log.insertPlainText(text + end)

    async def start_hub(self):
        self.button_connect.setText("Click when hub is started")
        self.label_connect.setText("Start hub with hub button")
        set_label_color(self.label_connect, QColorConstants.Cyan)
        self.hub_connect_state = HUB_REQUEST_ON

    async def connect_hub(self):
        self.hub_connect_state = HUB_CONNECTING
        self.log_text("pc> Hub is started")
        self.button_connect.setText("")
        self.label_connect.setText("Scan to find the hub")
        set_label_color(self.label_connect, QColorConstants.Magenta)

        # Do a Bluetooth scan to find the hub.
        device = await BleakScanner.find_device_by_name(self.hub_name)
        if device is None:
            self.hub_connect_state = HUB_DISCONNECTED
            self.log_text(f"pc> Could not find hub with name: {self.hub_name}")
            self.button_connect.setText("connect to hub")
            self.label_connect.setText("disconnected")
            set_label_color(self.label_connect, QColorConstants.Gray)
            return
        # Hub found.
        self.log_text(f"pc> Hub found with name: {self.hub_name}")

        # Connect to the hub.
        self.client = BleakClient(device)
        await self.client.connect()
        self.log_text("pc> Hub is connected")
        self.device = device

        # Initialize the sender channel to the hub.
        self.hub_client = HubClient(self.client, PYBRICKS_COMMAND_EVENT_CHAR_UUID, self)

        # Subscribe to notifications from the hub.
        await self.hub_client.start_notify()
        self.hub_connect_state = HUB_CONNECTED
        self.log_text("pc> Hub notifications started")
        # Tell user to start program on the hub.
        self.label_connect.setText("Start program with hub button")
        set_label_color(self.label_connect, QColorConstants.Yellow)

        # Waits until a ready response has been sent from the hub.
        await self.hub_client.wait_send_ready()
        self.hub_connect_state = HUB_RUNNING
        self.log_text("pc> Hub running.")
        self.button_connect.setText("disconnect from hub")
        self.label_connect.setText("running")
        set_label_color(self.label_connect, QColorConstants.Green)

    async def disconnect_hub(self):
        self.hub_connect_state = HUB_DISCONNECTING
        set_label_color(self.label_connect, QColorConstants.Yellow)
        self.button_connect.setText("")
        for i in range(3):
            self.label_connect.setText("disconnecting" + ("." * i))
            await asyncio.sleep(1)
        self.hub_connect_state = HUB_DISCONNECTED
        self.label_connect.setText("disconnected")
        set_label_color(self.label_connect, QColorConstants.Gray)
        self.button_connect.setText("connect to hub")

    def hub_is_running(self):
        if self.hub_connect_state == HUB_RUNNING:
            return True
        self.log_text("pc> error: not connected to hub")
        return False

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
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F1_COMMMAND))

    @Slot()
    def button_f2_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F2_COMMMAND))

    @Slot()
    def button_f3_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F3_COMMMAND))

    @Slot()
    def button_f4_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F4_COMMMAND))

    @Slot()
    def button_f5_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F5_COMMMAND))

    @Slot()
    def button_f6_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F6_COMMMAND))

    @Slot()
    def button_f7_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F7_COMMMAND))

    @Slot()
    def button_f8_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F8_COMMMAND))

    @Slot()
    def button_f9_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F9_COMMMAND))

    @Slot()
    def button_f10_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F10_COMMMAND))

    @Slot()
    def button_f11_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F11_COMMMAND))

    @Slot()
    def button_f12_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(F12_COMMMAND))

    @Slot()
    def button_left_plus_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(BUTTON_LEFT_PLUS_COMMAND))

    @Slot()
    def button_left_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(BUTTON_LEFT_COMMAND))

    @Slot()
    def button_left_minus_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(BUTTON_LEFT_MINUS_COMMAND))

    @Slot()
    def button_middle_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(BUTTON_MIDDLE_COMMAND))

    @Slot()
    def button_right_plus_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(BUTTON_RIGHT_PLUS_COMMAND))

    @Slot()
    def button_right_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(BUTTON_RIGHT_COMMAND))

    @Slot()
    def button_right_minus_clicked(self):
        if self.hub_is_running():
            asyncio.create_task(self.hub_client.send(BUTTON_RIGHT_MINUS_COMMAND))

    @Slot()
    def line_input_return_pressed(self):
        text = self.line_input.text()
        self.log_text(text)
        self.line_input.setText("")

# Run the main async program.
if __name__ == "__main__":
    # Start the RemoteConsole
    app = QApplication(sys.argv)
    # remote consoles must be saved in the global list,
    # otherwiese garbage collector
    remote_consoles = []
    for hub_name in HUB_NAMES:
        remote_console = RemoteConsole(hub_name)
        remote_console.show()
        remote_consoles.append(remote_console)
    QtAsyncio.run(handle_sigint=True)