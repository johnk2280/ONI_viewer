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

        self.play = None
        self.stop = None

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
            self.device = dev.open_file(path)
            self.depth_stream = self.device.create_depth_stream()
            self.color_stream = self.device.create_color_stream()
            print('Device open')

    def get_img(self):
        frame = self.depth_stream.read_frame()
        frame_data = frame.get_buffer_as_triplet()
        img = np.frombuffer(frame_data, dtype=np.uint16)
        img.shape = (1, 480, 640)
        img = np.concatenate((img, img, img), axis=0)
        img = np.swapaxes(img, 0, 2)
        img = np.swapaxes(img, 0, 1)
        print('Image received')
        return img

    def start_streaming(self):
        pass

    def load_video(self):
        pass

    def play_video(self):
        if not self.play:
            self.play = True
            print('enter play')
            self.depth_stream.start()
            print('start depth')
            self.color_stream.start()
            print('Start streaming')

            while True:
                img = self.get_img()
                img = cv2.imshow('image', img)
                self.label.setPixmap(QtGui.QPixmap.fromImage(img))
                if cv2.waitKey(34) & 0xFF == ord('q'):
                    self.play = False
                    self.stop = False
                    # cv2.destroyAllWindows()
                    break


    def pause_video(self):
        print('Pause')

    def next_frame(self):
        print('Next')

    def prev_frame(self):
        print('Previous')

    def stop_video(self):
        return ord('q')

    def browse_folder(self):
        p = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'C:\Users', filter='*.oni')
        print(p[0])
        if p:
            return bytes(''.join([el if el != '/' else '//' for el in list(p[0])]), encoding='utf-8')

    def quit_player(self):
        reply = QtWidgets.QMessageBox.question(self, 'Message', 'Are you sure to quit?', QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            # self.depth_stream.stop()
            # self.color_stream.stop()
            # openni2.unload()
            self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    openni2.initialize()
    dev = openni2.Device
    o_player = OniPlayer(dev)
    o_player.show()
    app.exec_()

