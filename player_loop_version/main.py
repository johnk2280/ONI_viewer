
import sys
import cv2
import numpy as np
import qimage2ndarray
from openni import openni2
from PyQt5 import QtWidgets, QtCore, QtGui
import gui
import time


class MyLoop(QtCore.QThread):
    def __init__(self, player):
        super().__init__()
        self.player = player

    def run(self) -> None:
        while True:
            self.player.get_next_frame()
            time.sleep(0.01)


class OniPlayer(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, device):
        super().__init__()
        self.setupUi(self)

        self.is_open = False
        self.is_streaming = False
        self.is_play = False

        self.cycle = MyLoop(player=self)

        self.device = device
        self.depth_stream = None
        self.color_stream = None
        self.num_depth_frames = 0
        self.num_color_frames = 0
        self.playback_support = None

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
        self.horizontalSlider.sliderPressed.connect(self.play_video)
        self.horizontalSlider.sliderReleased.connect(self.play_video)

    def open_device(self):
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
            self.horizontalSlider.setRange(2, self.num_depth_frames)

            self.is_open = True

            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.prev_button.setEnabled(True)

    def start_streaming(self):
        self.depth_stream.start()
        self.color_stream.start()
        self.playback_support.seek(self.depth_stream, 2)
        self.playback_support.seek(self.color_stream, 2)
        self.get_depth_frame()
        self.get_color_frame()
        self.is_streaming = True

    def get_depth_frame(self):
        frame = self.depth_stream.read_frame()
        frame_data = frame.get_buffer_as_uint16()
        img = np.frombuffer(frame_data, dtype=np.uint16)
        img = img.reshape(frame.height, frame.width)
        img = cv2.convertScaleAbs(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), alpha=(1200.0 / 65535.0))
        img = qimage2ndarray.array2qimage(img)
        self.left_label.setPixmap(QtGui.QPixmap.fromImage(img))

    def get_color_frame(self):
        frame = self.color_stream.read_frame()
        frame_data = frame.get_buffer_as_uint8()
        img = np.frombuffer(frame_data, dtype=np.uint8)
        img = img.reshape(frame.height, frame.width, 3)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        img = qimage2ndarray.array2qimage(img)
        self.right_label.setPixmap(QtGui.QPixmap.fromImage(img))

    def close_streaming(self):
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)

        self.horizontalSlider.setEnabled(False)
        self.horizontalSlider.setSliderPosition(0)

        self.cycle.terminate()

        self.left_label.clear()
        self.right_label.clear()

        self.depth_stream.close()
        self.color_stream.close()
        self.device.close()

        self.is_open = False
        self.is_streaming = False

    def play_video(self):
        if not self.is_streaming:
            self.start_streaming()
            self.horizontalSlider.setEnabled(True)

        if self.is_play:
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            self.play_button.setText('Play')
            self.next_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            self.is_play = False

            self.cycle.terminate()

        else:
            self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.play_button.setText('Pause')
            self.next_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.is_play = True

            self.cycle.start()

    def stop_video(self):
        self.is_play = False
        self.play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.play_button.setText('Play')
        self.close_streaming()

    def set_position(self, position):
        self.playback_support.seek(self.depth_stream, position)
        self.playback_support.seek(self.color_stream, position)
        self.get_depth_frame()
        self.get_color_frame()

    def get_next_frame(self):
        if self.horizontalSlider.value() == self.num_depth_frames:
            self.horizontalSlider.setValue(0)

        self.horizontalSlider.setValue(self.horizontalSlider.value() + 1)
        self.set_position(self.horizontalSlider.value())

    def get_prev_frame(self):
        if self.horizontalSlider.value() == 2:
            self.horizontalSlider.setValue(self.num_depth_frames)

        self.horizontalSlider.setValue(self.horizontalSlider.value() - 1)
        self.set_position(self.horizontalSlider.value())

    def browse_folder(self):
        p = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'C:\Users', filter='*.oni')
        if p[0]:
            return bytes(''.join([el if el != '/' else '//' for el in list(p[0])]), encoding='utf-8')

    def quit_player(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            'Message',
            'Are you sure to quit?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self.is_streaming:
                self.close_streaming()
            openni2.unload()
            self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.is_streaming:
            self.close_streaming()
        openni2.unload()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    openni2.initialize()
    dev = openni2.Device
    o_player = OniPlayer(dev)
    o_player.show()
    sys.exit(app.exec_())

