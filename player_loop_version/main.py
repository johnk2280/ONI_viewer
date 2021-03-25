from openni import openni2
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import cv2
import numpy as np


class OniPlayer(QtWidgets.QWidget):

    def __init__(self, dev, width=640, height=480, fps=30):
        super().__init__()

        self.video = None
        self.play = None
        self.pause = None
        self.next = None
        self.prev = None
        self.stop = None
        self.by_step = None
        self.wait_k = 34

        # инициализация OpenNI2
        self.dev = dev.open_file(self.browse_folder())

        self.depth_stream = self.dev.create_depth_stream()
        # self.color_stream = self.dev.create_color_stream()
        self.v_mode = self.depth_stream.get_video_mode()
        self.play_sup = openni2.PlaybackSupport(self.dev)

        self.width = self.v_mode.resolutionX
        self.height = self.v_mode.resolutionY
        self.fps = self.v_mode.fps

        # self.start_streaming()

        self.video_capture = cv2.VideoCapture()
        self.video_size = QtCore.QSize(self.width, self.height)
        self.frame_timer = QtCore.QTimer()

        # self.display_video()

        """Инициализация виджетов"""

        self.frame_label = QtWidgets.QLabel()
        self.quit_button = QtWidgets.QPushButton('Quit')
        self.play_pause_button = QtWidgets.QPushButton('Play')
        self.stop_button = QtWidgets.QPushButton('Stop')
        self.next_button = QtWidgets.QPushButton('Next', self.frame_label)
        self.prev_button = QtWidgets.QPushButton('Previous')
        self.browse_button = QtWidgets.QPushButton('Open')
        self.horizontal_slider = QtWidgets.QSlider(self.frame_label)
        self.lcd = QtWidgets.QLCDNumber(self.frame_label)
        self.main_layout = QtWidgets.QGridLayout()

        self.setup_ui()

    def setup_ui(self):
        """Устанавливаем название и ярлык в главном окне"""
        self.setWindowTitle('ONI Player')
        self.setWindowIcon(QtGui.QIcon('media/player-play_114441.png'))

        """Устанавливаем размер поля вывода под размер видео"""

        self.frame_label.setFixedSize(self.video_size)

        """Коннектим кнопки с функциями класса"""

        self.quit_button.clicked.connect(self.close_window)
        self.play_pause_button.clicked.connect(self.play_pause_video)
        self.stop_button.clicked.connect(self.stop_video)
        self.next_button.clicked.connect(self.get_next_frame)
        self.prev_button.clicked.connect(self.get_prev_frame)
        self.browse_button.clicked.connect(self.browse_folder)
        self.horizontal_slider.valueChanged.connect(self.scroll_video)

        """Устанавливаем слайдер по горизонтали"""
        self.horizontal_slider.setOrientation(QtCore.Qt.Horizontal)

        """Рисуем поля для кнопок и поля вывода изображения"""
        self.main_layout.addWidget(self.frame_label, 0, 0, 0, 0)
        self.main_layout.addWidget(self.quit_button, 7, 0, 1, 4)
        self.main_layout.addWidget(self.stop_button, 5, 0, 1, 1)
        self.main_layout.addWidget(self.prev_button, 5, 1, 1, 1)
        self.main_layout.addWidget(self.play_pause_button, 5, 2, 1, 1)
        self.main_layout.addWidget(self.next_button, 5, 3, 1, 1)
        self.main_layout.addWidget(self.browse_button, 6, 0, 1, 4)
        self.main_layout.addWidget(self.horizontal_slider, 4, 0, 2, 4)
        self.main_layout.addWidget(self.lcd, 0, 0, 1, 1)

        self.setLayout(self.main_layout)

    def setup_video(self):
        pass

    def get_data(self):
        frame = self.depth_stream.read_frame()
        frame_data = frame.get_buffer_as_uint16()
        img = np.frombuffer(frame_data, dtype=np.uint16)
        img.shape = (1, self.height, self.width)
        img = np.concatenate((img, img, img), axis=0)
        img = np.swapaxes(img, 0, 2)
        img = np.swapaxes(img, 0, 1)
        return img

    def start_streaming(self):
        self.depth_stream.start()
        # self.color_stream.start()
        while True:
            img = self.get_data()
            cv2.imshow('image', img)
            cv2.waitKey(self.wait_k)

    def display_video(self):
        self.start_streaming()

    def play_pause_video(self):
        if not self.pause:
            self.play_pause_button.setText('Play')
            self.wait_k = 0
            # self.play_sup.set_speed(0.0)
        else:
            self.play_pause_button.setText('Pause')
            self.wait_k = 34
            # self.play_sup.set_speed(1.0)
        self.pause = not self.pause
        self.display_video()

        print(self.pause)

    def stop_video(self):
        self.depth_stream.stop()
        # self.color_stream.stop()
        openni2.unload()

    def get_next_frame(self):
        pass

    def get_prev_frame(self):
        pass

    def scroll_video(self):
        # self.horizontal_slider.valueChanged.connect(self.lcd.display)
        pass

    def browse_folder(self):
        p = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'C:\Users', filter='*.oni')
        return bytes(''.join([el if el != '/' else '//' for el in list(p[0])]), encoding='utf-8')

    def close_window(self):
        reply = QtWidgets.QMessageBox.question(self, 'Message', 'Are you sure to quit?', QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.depth_stream.stop()
            # self.color_stream.stop()
            openni2.unload()
            self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    openni2.initialize()
    dev = openni2.Device
    player = OniPlayer(dev)
    player.show()
    sys.exit(app.exec())
