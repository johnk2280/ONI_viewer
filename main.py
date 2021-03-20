import sys
import cv2
import numpy as np
import qimage2ndarray
from openni import openni2
from PyQt5 import QtCore, QtWidgets, QtGui
import gui


class OniPlayer(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, device):
        super().__init__()
        self.setupUi(self)

        self.is_open = False
        self.is_streaming = False

        self.device = device
        self.depth_stream = None
        self.color_stream = None
        self.num_depth_frames = None
        self.num_color_frames = None
        self.playback_support = None

        self.timer = QtCore.QTimer()

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

        self.horizontalSlider.setEnabled(False)
        self.horizontalSlider.sliderMoved.connect(self.set_position)

    def open_device(self):

        """ Open .oni file and getting metadata. """

        if self.is_open:
            self.stop_video()

        path = self.browse_folder()

        if path:
            self.device = self.device.open_file(path)
            self.depth_stream = self.device.create_depth_stream()
            self.color_stream = self.device.create_color_stream()
            self.num_depth_frames = self.depth_stream.get_number_of_frames()
            self.num_color_frames = self.color_stream.get_number_of_frames()
            self.playback_support = openni2.PlaybackSupport(self.device)
            self.horizontalSlider.setRange(0, self.num_depth_frames)

            self.is_open = True

            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            self.horizontalSlider.setEnabled(True)

    def start_streaming(self):
        self.depth_stream.start()
        self.color_stream.start()
        self.playback_support.seek(self.depth_stream, 0)
        self.playback_support.seek(self.color_stream, 0)
        self.get_depth_frame()
        self.get_color_frame()
        self.timer.timeout.connect(self.position_changed)
        self.is_streaming = True

    def get_depth_frame(self):
        frame = self.depth_stream.read_frame()
        frame_data = frame.get_buffer_as_uint16()
        img = np.frombuffer(frame_data, dtype=np.uint16)
        img = img.reshape(frame.height, frame.width)
        img = cv2.convertScaleAbs(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), alpha=(1000.0 / 65535.0))
        img = qimage2ndarray.array2qimage(img)
        self.label_left.setPixmap(QtGui.QPixmap.fromImage(img))

    def get_color_frame(self):
        frame = self.color_stream.read_frame()
        frame_data = frame.get_buffer_as_uint8()
        img = np.frombuffer(frame_data, dtype=np.uint8)
        img = img.reshape(frame.height, frame.width, 3)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        img = qimage2ndarray.array2qimage(img)
        self.label_right.setPixmap(QtGui.QPixmap.fromImage(img))

    def close_streaming(self):
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.horizontalSlider.setEnabled(False)
        self.timer.stop()
        self.label_right.clear()
        self.label_left.clear()
        self.horizontalSlider.setSliderPosition(0)
        self.depth_stream.close()
        self.color_stream.close()
        self.device.close()
        self.is_open = False
        self.is_streaming = False

    def play_video(self):
        if not self.is_streaming:
            self.start_streaming()

        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            self.play_button.setText('Play')
        else:
            self.timer.start()
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.play_button.setText('Pause')

    def stop_video(self):
        self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.play_button.setText('Play')
        self.close_streaming()

    def position_changed(self):
        if self.horizontalSlider.value() == self.num_depth_frames:
            self.horizontalSlider.setValue(0)

        self.horizontalSlider.setValue(self.horizontalSlider.value() + 1)
        self.set_position(self.horizontalSlider.value())

    def set_position(self, position):
        self.playback_support.seek(self.depth_stream, position)
        self.playback_support.seek(self.color_stream, position)
        self.get_depth_frame()
        self.get_color_frame()

    def get_next_frame(self):
        if not self.timer.isActive() and self.is_streaming:
            self.horizontalSlider.setValue(self.horizontalSlider.value() + 1)
            self.set_position(self.horizontalSlider.value())

    def get_prev_frame(self):
        if not self.timer.isActive() and self.is_streaming:
            self.horizontalSlider.setValue(self.horizontalSlider.value() - 1)
            self.set_position(self.horizontalSlider.value())

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
