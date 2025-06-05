import sys
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic

form_class = uic.loadUiType('./qt_mp3_player.ui')[0]

class ExampleApp(QWidget, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.playing_flag = False
        self.player = QMediaPlayer()
        self.playlist = []
        self.current_index = -1

        # 재생 기능 연결
        self.actionPlay.triggered.connect(self.playing_music_slot)
        self.actionPause.triggered.connect(self.pause_music_slot)
        self.actionPrevious_Track.triggered.connect(self.previous_track_slot)
        self.actionNext_Track.triggered.connect(self.next_track_slot)

        self.btn_pnp.toggle.connect(self.play_or_pause_slot)
        self.btn_previous.clicked.connect(self.previous_track_slot)
        self.btn_next.clicked.connect(self.next_track_slot)

        # 볼륨 조절 기능 연결

        # 진행 표시 기능 연결

        # 플레이리스트 관리 기능 연결

        # 음악 정보 표시 기능 연결

    # Play =============================
    # 재생/일시정지 버튼 토글
    def play_or_pause_slot(self):
        if self.btn_pnp.isChecked():
            return self.pause_music_slot()
        else:
            return self.playing_music_slot()

    # 재생
    def playing_music_slot(self):
        pass

    # 일시정지
    def pause_music_slot(self):
        pass

    # 이전 트랙 재생 | 되돌아가기
    def previous_track_slot(self):
        pass

    def next_track_slot(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ExampleApp()
    main_window.show()
    sys.exit(app.exec())