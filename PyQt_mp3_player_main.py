import glob
import os
import sys

from PyQt5.QtCore import QStringListModel, QFileInfo, QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic

form_class = uic.loadUiType('./qt_mp3_player.ui')[0]

class ExampleApp(QWidget, form_class):
    def __init__(self):
        super().__init__()
        self.file_path = ('', '')
        self.setupUi(self)

        self.playlist = []          # 절대경로 리스트
        self.current_index = -1     # 현재 곡 인덱스
        self.model = QStringListModel()
        self.listView.setModel(self.model)
        self.player = QMediaPlayer()
        self.player.setVolume(50)   # 초기 볼륨

        # File 메뉴 기능 연결
        self.actionOpen_File.triggered.connect(self.open_file_slot)
        self.actionOpen_Folder.triggered.connect(self.open_folder_slot)
        self.btn_open.clicked.connect(self.open_folder_slot)
        # self.actionAdd_Music.triggered.connect(self.open_file_slot)

        # 재생 기능 연결
        self.actionPlay.triggered.connect(self.playing_music_slot)
        self.actionPause.triggered.connect(self.pause_music_slot)
        self.actionPrevious_Track.triggered.connect(self.previous_track_slot)
        self.actionNext_Track.triggered.connect(self.next_track_slot)

        self.btn_pnp.toggled.connect(self.play_or_pause_slot)
        self.player.stateChanged.connect(self.sync_play_button)
        self.btn_previous.clicked.connect(self.previous_track_slot)
        self.btn_next.clicked.connect(self.next_track_slot)

        # 볼륨 조절 기능 연결
        # 슬라이더 혹은 다이얼 값 변경
        self.volume_slider.valueChanged.connect(self.volume_dial.setValue)
        self.volume_dial.valueChanged.connect(self.volume_slider.setValue)
        self.lbl_music_name.setText("Volume: " + str(self.player.volume))  # 곡 제목을 표시

        # 슬라이더 혹은 다이얼을 조정 시 실제로 볼륨이 조절되도록
        self.volume_slider.valueChanged.connect(self.player.setVolume)
        self.volume_dial.valueChanged.connect(self.player.setVolume)


        # 진행 표시 기능 연결
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.play_bar.sliderMoved.connect(self.seek)

        # 플레이리스트 관리 기능 연결
        self.actionOpen.triggered.connect(self.open_folder_slot)
        self.listView.itemDoubleClicked.connect(self.play_selected)

    # File =============================
    # 파일 1개 열기
    def open_file_slot(self):
        self.file_path = QFileDialog.getOpenFileName(self, 'Open Audio File', '',
                                            ''
                                            'Audio Files (*.mp3 *.wav *.wma *.aac);;All Files(*.*)')
        if not self.file_path[0]: # 파일을 불러오지 않았다면 그냥 return해서 아무 것도 하지 않기
            return # 메시지 박스를 띄우는 게 좋을까?
        self.playlist = [self.file_path[0]] # 플레이리스트에 해당 파일 경로만 추가
        self.current_index = 0

        filename=  os.path.basename(self.file_path[0])
        self.model.setStringList([filename]) # 모델에는 파일명만 추가
        self.load_track(0) # 첫 곡 로드 & 재생

    # 폴더 열기
    def open_folder_slot(self):
        folder = QFileDialog.getExistingDirectory(self,
                                                  'Select Folder',
                                                  '')
        if not folder:
            return

        # 지원 확장자
        extensions = ('*.mp3', '*.wav', '*.wma', '*.flac', '*.aac', '*.ogg')
        audio_files = []
        for i in extensions:
            audio_files += glob.glob(os.path.join(folder, i))

        if not audio_files: # 추가된 음악이 없을 경우
            return # 메시지 박스를 띄우는 게 좋을까?

        self.playlist = audio_files
        self.current_index = 0

        names = []
        for p in audio_files:
            names.append(QFileInfo(p).fileName()) # 파일 이름만을 추가
        self.model.setStringList(names)

        self.load_track(0) # 선택한 즉시 재생을 시켜야 할까?

    # Play =============================

    def load_track(self, idx):
        url = QUrl.fromLocalFile(self.playlist[idx]) # 파일 경로 받기
        self.player.setMedia(QMediaContent(url))
        self.lbl_music_name.setText(QFileInfo(self.playlist[idx]).baseName()) # 곡 제목을 표시

        self.player.play() # 자동으로 재생시키지는 않을 거임

    # 재생/일시정지 버튼 상태 변경
    def sync_play_button(self, state):
        is_playing = (state == QMediaPlayer.State.PlayingState)
        # Checked 상태 바꾸기
        self.btn_pnp.blockSignals(True) # 루프 방지
        self.btn_pnp.setChecked(is_playing)
        self.btn_pnp.blockSignals(False)

    # play or pause
    def play_or_pause_slot(self, checked: bool):
        if checked:
            self.player.play()
        else:
            self.player.pause()

    # 재생
    def playing_music_slot(self):
        self.player.play()

    # 일시정지
    def pause_music_slot(self):
        self.player.pause()

    # 이전 트랙 재생 | 되돌아가기
    def previous_track_slot(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.load_track(self.current_index)

    def next_track_slot(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.load_track(self.current_index)

    # 현재 재생 지점 표시
    def update_position(self, pos):
        self.play_bar.setValue(pos)
        secs = pos // 1000
        m, s = divmod(secs, 60)
        self.lblCurrentTime.setText(f'{m:02d}:{s:02d}')

    # 전체 길이 표시
    def update_duration(self, dur):
        self.play_bar.setRange(0, dur)
        secs = dur // 1000
        m, s = divmod(secs, 60)
        self.lblTotalTime.setText(f'/ {m:02d}:{s:02d}')

    def seek(self, pos):
        self.player.setPosition(pos)

    def play_selected(self, item):
        self.current_index = self.listWidget.row(item)
        self.load_track(self.current_index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ExampleApp()
    main_window.show()
    sys.exit(app.exec())