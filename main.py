import sys
from openni import openni2
import numpy as np
import cv2
from PyQt5 import QtWidgets
import design
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtMultimedia
from PyQt5 import QtMultimediaWidgets


class OniPlayer(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self, dev):
        super().__init__()
        self.setupUi(self)

        self.is_play = None
        self.is_stop = None
        self.is_pause = None

        self.dev = dev

        self.open_button.clicked.connect(self.open_device)
        self.quit_button.clicked.connect(self.quit_player)
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.next_button.clicked.connect(self.next_frame)
        self.prev_button.clicked.connect(self.prev_frame)
        self.stop_button.clicked.connect(self.stop_video)

    def open_device(self):
        path = self.browse_folder()
        print(path)
        if path:
            self.device = self.dev.open_file(path)
            self.depth_stream = self.device.create_depth_stream()
            self.color_stream = self.device.create_color_stream()
            self.is_play = True
            print('Device open')

    def get_img(self):
        frame = self.depth_stream.read_frame()
        frame_data = frame.get_buffer_as_triplet()
        img = np.frombuffer(frame_data, dtype=np.uint16)
        img.shape = (1, 480, 640)
        img = np.concatenate((img, img, img), axis=0)
        img = np.swapaxes(img, 0, 2)
        img = np.swapaxes(img, 0, 1)
        # print('Image received')
        return img

    def start_streaming(self):
        pass

    def load_video(self):
        pass

    def play_video(self):
        print(self.is_play)
        if not self.is_play:
            self.open_device()

        elif self.is_play:
            self.depth_stream.start()
            self.color_stream.start()

            while True:
                img = self.get_img()
                cv2.imshow('image', img)
                cv2.waitKey(1)
                if self.is_stop:
                    break

            self.is_stop = False
            self.is_play = False
            cv2.destroyAllWindows()
            self.depth_stream.close()
            self.color_stream.close()
            self.device.close()
            print('Stream closed')

    def pause_video(self):
        print('Pause')

    def next_frame(self):
        print('Next')

    def prev_frame(self):
        print('Previous')

    def stop_video(self):
        self.is_stop = True

    def browse_folder(self):
        p = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'C:\Users', filter='*.oni')
        print(p[0])
        if p:
            return bytes(''.join([el if el != '/' else '//' for el in list(p[0])]), encoding='utf-8')

    def quit_player(self):
        reply = QtWidgets.QMessageBox.question(self, 'Message', 'Are you sure to quit?', QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            # Добавить условие проверки запущенных потоков
            # self.depth_stream.stop()
            # self.color_stream.stop()
            openni2.unload()
            self.close()
            print('Вышли нах')



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    openni2.initialize()
    dev = openni2.Device
    o_player = OniPlayer(dev)
    o_player.show()
    app.exec_()

