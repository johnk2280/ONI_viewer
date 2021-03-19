import sys
import cv2
import numpy
import qimage2ndarray

from openni import openni2

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimedia import QMediaContent

import gui


class OniPlayer(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, device):
        super().__init__()
        self.setupUi(self)

        self.is_play = False
        self.is_pause = False
        self.is_stop = False
        self.is_open = False
        self.is_streaming = False
        self.is_next = False
        self.is_prev = False

        self.device = device
        self.depth_stream = None
        self.color_stream = None
        self.num_depth_frames = None
        self.num_color_frames = None
        self.playback_support = None

        self.timer = QtCore.QTimer()

        # self.depth_media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)  # возможно StreamPlayback
        # self.color_media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)  # возможно StreamPlayback
        # self.depth_media_player.setVideoOutput(self.video_widget_left)
        # self.color_media_player.setVideoOutput(self.video_widget_right)
        # self.depth_media_player.stateChanged.connect(self.media_state_changed)
        # self.depth_media_player.positionChanged.connect(self.position_changed)
        # self.depth_media_player.durationChanged.connect(self.set_duration)

        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_video)

        self.stop_button.setEnabled(False)
        self.stop_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop_video)

        self.next_button.setEnabled(False)
        self.next_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipForward))
        self.next_button.clicked.connect(self.get_next_frame)

        self.prev_button.setEnabled(False)
        self.prev_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipBackward))
        self.prev_button.clicked.connect(self.get_prev_frame)

        self.open_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
        self.open_button.clicked.connect(self.open_device)

        self.quit_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        self.quit_button.clicked.connect(self.quit_player)

        self.horizontalSlider.sliderMoved.connect(self.set_position)
        self.horizontalSlider.sliderPressed.connect(self.play_video)
        self.horizontalSlider.sliderReleased.connect(self.play_video)

    def open_device(self):

        """ Open .oni file and getting metadata. """

        if self.is_open:
            self.close_streaming()

        path = self.browse_folder()

        if path:
            self.device = self.device.open_file(path)
            self.depth_stream = self.device.create_depth_stream()
            self.color_stream = self.device.create_color_stream()
            self.num_depth_frames = self.depth_stream.get_number_of_frames()
            self.num_color_frames = self.color_stream.get_number_of_frames()
            self.playback_support = openni2.PlaybackSupport(self.device)

            self.is_open = True

            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.prev_button.setEnabled(True)

            print('num_depth_frames', self.num_depth_frames)
            print('Device open')

    def start_streaming(self):
        self.depth_stream.start()
        self.color_stream.start()
        self.horizontalSlider.setRange(0, self.depth_stream.get_number_of_frames())
        self.playback_support.seek(self.depth_stream, 0)
        self.playback_support.seek(self.color_stream, 0)
        self.is_streaming = True

    def stop_streaming(self):
        self.is_play = False
        self.depth_stream.stop()
        self.color_stream.stop()

    def close_streaming(self):
        self.is_streaming = False
        self.is_play = False
        self.is_pause = False
        self.is_open = False
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.is_streaming = False
        self.horizontalSlider.setSliderPosition(0)
        self.depth_stream.close()
        self.color_stream.close()
        self.device.close()
        print('Stream closed')

    def play_video(self):
        if self.is_play:
            self.timer.stop()
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.play_button.setText('Pause')
            self.is_play = False
            self.is_pause = True
        else:
            if not self.is_streaming:
                self.start_streaming()

            #  self.set_frame()
            self.timer.timeout.connect(self.slider_move)
            self.timer.start(40)
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            self.play_button.setText('Play')
            self.is_play = True
            self.is_pause = False

    def stop_video(self):
        if self.is_open:
            self.close_streaming()

    def media_state_changed(self):
        if self.depth_media_player.state() == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.play_button.setText('Pause')
        else:
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            self.play_button.setText('Play')

    def position_changed(self, position):
        print('position_changed', position)
        self.horizontalSlider.setSliderPosition(position)
        # self.horizontalSlider.setValue(position)

    def set_position(self, position):
        print('set_position', position)
        self.depth_media_player.setPosition(position)
        self.color_media_player.setPosition(position)

    def get_next_frame(self, position):
        print(position)
        if self.depth_media_player.state() == QMediaPlayer.PlayingState \
                or self.depth_media_player.state() == QMediaPlayer.PausedState:
            self.depth_media_player.setPosition(position + 1)
            self.color_media_player.setPosition(position + 1)

    def get_prev_frame(self):
        pass

    def browse_folder(self):
        p = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'C:\Users', filter='*.oni')
        if p[0]:
            return bytes(''.join([el if el != '/' else '//' for el in list(p[0])]), encoding='utf-8')

    def quit_player(self):
        reply = QtWidgets.QMessageBox.question(self, 'Message', 'Are you sure to quit?', QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            if self.is_streaming:
                self.close_streaming()
            openni2.unload()
            self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    openni2.initialize()
    dev = openni2.Device
    o_player = OniPlayer(dev)
    o_player.show()
    sys.exit(app.exec_())
