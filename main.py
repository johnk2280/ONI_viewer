import sys
from openni import openni2
import numpy as np
import cv2
from PyQt5 import QtWidgets
import design


class OniPlayer(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self, dev):
        super().__init__()
        self.setupUi(self)

        self.is_play = False
        self.is_pause = False
        self.is_open = False
        self.is_streaming = False
        self.is_prev = False
        self.is_next = False
        self.is_slider = None

        self.depth_frame_index = None
        self.color_frame_index = None
        self.frame_timestamp = None
        self.color_frame_timestamp = None
        self.num_depth_frames = 0
        self.num_color_frames = 0
        self.device = None
        self.depth_stream = None
        self.color_stream = None
        self.dev = dev
        self.playback_support = None

        self.open_button.clicked.connect(self.open_device)
        self.quit_button.clicked.connect(self.quit_player)
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.next_button.clicked.connect(self.next_frame)
        self.prev_button.clicked.connect(self.prev_frame)
        self.stop_button.clicked.connect(self.stop_video)
        self.horizontalSlider.sliderPressed.connect(self.pause_video)
        self.horizontalSlider.sliderReleased.connect(self.play_video)
        self.horizontalSlider.sliderMoved.connect(self.set_position)

    def open_device(self):
        path = self.browse_folder()
        print(path)
        if path:
            self.device = self.dev.open_file(path)
            self.depth_stream = self.device.create_depth_stream()
            self.color_stream = self.device.create_color_stream()
            self.num_depth_frames = self.depth_stream.get_number_of_frames()
            # self.num_color_frames = self.color_stream.get_number_of_frames()
            self.playback_support = openni2.PlaybackSupport(self.device)
            self.is_open = True
            self.set_duration(self.num_depth_frames)
            print(self.num_depth_frames)
            print('Device open')

    def get_frame(self):
        frame = self.depth_stream.read_frame()
        self.depth_frame_index = frame.frameIndex
        self.frame_timestamp = frame.timestamp

        self.horizontalSlider.setSliderPosition(self.depth_frame_index)

        if self.is_prev:
            if self.depth_frame_index > 5:
                self.depth_frame_index -= 3
            else:
                self.depth_frame_index = self.num_depth_frames - 2
            self.set_frame(self.depth_frame_index)

        frame_data = frame.get_buffer_as_uint16()

        return frame_data

    def set_frame(self, index):
        self.playback_support.seek(stream=self.depth_stream, frame_index=index)
        # self.playback_support.seek(stream=self.color_stream, frame_index=index)

    def get_img(self):
        frame_data = self.get_frame()
        img = np.frombuffer(frame_data, dtype=np.uint16)
        img.shape = (1, 480, 640)
        img = np.concatenate((img, img, img), axis=0)
        img = np.swapaxes(img, 0, 2)
        img = np.swapaxes(img, 0, 1)
        print(self.depth_frame_index)
        return img

    def play_video(self):
        if not self.is_next and not self.is_prev:
            self.is_pause = False

        if not self.is_open:
            self.open_device()
            return

        if not self.is_play:
            self.start_streaming()
            self.is_play = True
            while self.is_play:
                img = self.get_img()
                cv2.imshow('image', img)
                cv2.waitKey(1)
                if self.is_next:
                    self.is_pause = True
                if self.is_pause:
                    self.stop_streaming()
                    break

    def start_streaming(self):
        self.depth_stream.start()
        self.color_stream.start()
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
        self.horizontalSlider.setSliderPosition(0)
        self.is_streaming = False
        cv2.destroyAllWindows()
        self.depth_stream.close()
        self.color_stream.close()
        self.device.close()
        print('Stream closed')

    def pause_video(self):
        self.is_play = False
        self.is_pause = True

    def next_frame(self):
        if self.is_pause:
            self.is_next = True
            self.play_video()
            self.is_next = False

    def prev_frame(self):
        if self.is_pause:
            self.is_prev = True
            self.play_video()
            self.is_prev = False

    def set_position(self):
        pass

    def set_duration(self, duration):
        if self.is_open:
            self.horizontalSlider.setRange(0, duration + 1)

    def stop_video(self):
        if not self.is_open:
            return
        self.close_streaming()

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
    app.exec_()
