import glob
import os
import sys
import random

from PyQt5.QtCore import QStringListModel, QFileInfo, QUrl, QModelIndex, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5 import uic

from Qt_style import create_default_shadow

form_class = uic.loadUiType('./qt_mp3_player.ui')[0]

class ExampleApp(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.file_path = ('', '')
        self.setupUi(self)

        self.playlist = []          # 절대경로 리스트
        self.current_index = -1     # 현재 곡 인덱스
        self.is_shuffle = False
        self.is_loop = False
        self.btn_shuffle.setCheckable(True)
        self.btn_loop.setCheckable(True)
        self.history = []
        self.model = QStringListModel()
        self.listView.setModel(self.model)
        self.player = QMediaPlayer()
        self.player.setVolume(50)   # 초기 볼륨
        self.setWindowTitle("MP3 Player")

        # File 메뉴 기능 연결 ---------------------------------
        self.actionOpen_File.triggered.connect(self.open_file_slot)
        self.actionOpen_Folder.triggered.connect(self.open_folder_slot)
        self.actionAdd_File.triggered.connect(self.add_files_slot)
        self.actionRemove.triggered.connect(self.remove_current_track_slot)
        self.actionRemove_All.triggered.connect(self.remove_all_slot)

        # 재생 기능 연결 ----------------------------------------
        self.actionPlay.triggered.connect(self.play_or_pause_slot)
        self.actionPause.triggered.connect(self.play_or_pause_slot)
        self.actionPrevious_Track.triggered.connect(self.previous_track_slot)
        self.actionNext_Track.triggered.connect(self.next_track_slot)
        self.actionShuffle_On_Off.setCheckable(True)
        self.actionShuffle_On_Off.toggled.connect(self.toggle_shuffle_slot)
        self.actionLoop_On_Off.setCheckable(True)
        self.actionLoop_On_Off.toggled.connect(self.toggle_loop_slot)

        self.btn_pnp.clicked.connect(self.play_or_pause_slot)

        self.player.stateChanged.connect(self.sync_play_button)

        self.btn_previous.clicked.connect(self.previous_track_slot)
        self.btn_next.clicked.connect(self.next_track_slot)

        self.btn_shuffle.toggled.connect(self.toggle_shuffle_slot)
        self.btn_loop.toggled.connect(self.toggle_loop_slot)

        # 트랙이 끝났을 때 자동으로 다음 곡 재생
        self.player.mediaStatusChanged.connect(self.handle_media_status)

        # 볼륨
        volume = self.player.volume()
        # 슬라이더 조정 시 실제로 볼륨이 조절되도록
        self.volume_slider.valueChanged.connect(self.volume_changed)

        # 진행 표시 기능 연결
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.play_bar.sliderMoved.connect(self.seek)

        # 플레이리스트 관리 기능 연결 ----------------------------
        self.btn_open.clicked.connect(self.open_folder_slot)
        self.listView.doubleClicked.connect(self.play_selected)
        self.btn_add.clicked.connect(self.add_files_slot)
        self.btn_remove.clicked.connect(self.remove_item_slot)
        self.btn_remove_all.clicked.connect(self.remove_all_slot)


        # 프로그램 정보
        self.actionAbout.triggered.connect(self.about_slot)

        # 라벨 내용, 스타일 설정 ----------------------------------
        #라벨 설정
        self.lbl_music_name.setText("Choose your music")
        self.lbl_volume.setText(f"Volume: {volume}%")  # 볼륨을 표시

        # 마우스를 올리면 뿌옇게 빛나요~
        for btn in [self.btn_shuffle, self.btn_loop]:
            btn.installEventFilter(self)
            btn.toggled.connect(lambda _, b=btn: self.update_button_shadow(b))


    # File =============================
    # 파일 선택해서 열기
    def open_file_slot(self):
        self.file_path = QFileDialog.getOpenFileName(self, 'Open Music File', '',
                                            ''
                                            'Audio Files (*.mp3 *.wav *.wma *.aac);;All Files(*.*)')
        path = self.file_path[0]
        if not path: # 파일을 불러오지 않았다면
            return # 아무 것도 하지 않는다

        # 2) 기존 플레이리스트에 곡이 있을 때 → 추가할지 물어보기
        if self.playlist:
            reply = QMessageBox.question(
                self,
                'Add or Replace',
                '플레이리스트에 이미 곡이 있습니다.\n'
                '선택한 곡을 추가하시겠습니까?\n'
                '"No"를 선택할 경우, 플레이리스트가 선택한 곡으로 대체됩니다.',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 2-a) Yes → 뒤에 추가하고, 그 곡을 바로 재생
                self.playlist.append(path)
                # 모델에도 새로운 파일명만 append
                names = self.model.stringList()
                names.append(QFileInfo(path).fileName())
                self.model.setStringList(names)

                # 추가된 곡을 current_index로 설정 후 재생
                self.current_index = len(self.playlist) - 1
                self.load_track(self.current_index)
                return

        self.playlist = [path] # 플레이리스트에 해당 파일 경로만 추가
        self.current_index = 0

        print(path)
        self.model.setStringList([QFileInfo(path).fileName()]) # 모델에는 파일명만 추가

        self.history.clear() # 이전 재생 기록 클리어
        self.load_track(0) # 첫 곡 로드 & 재생

    # 폴더 열기
    def open_folder_slot(self):
        # 옵션 객체 생성
        options = QFileDialog.Options()
        # 네이티브 대화상자가 아닌 Qt 자체 다이얼로그 사용
        options |= QFileDialog.DontUseNativeDialog
        # ShowDirsOnly 옵션은 주지 않으면 기본값 False → 파일도 함께 표시
        folder = QFileDialog.getExistingDirectory(
            self,
            'Select Folder',
            '',
            options
        )

        print(folder)
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

        self.history.clear() # 이전 재생 기록 클리어
        self.load_track(0) # 선택한 즉시 재생을 시켜야 할까?

    # Play =============================

    def load_track(self, idx):
        if idx < 0 or not self.playlist:
            self.lbl_music_name.setText("Choose your music")
            return
        url = QUrl.fromLocalFile(self.playlist[idx]) # 파일 경로 받기
        self.player.setMedia(QMediaContent(url))
        self.lbl_music_name.setText(QFileInfo(self.playlist[idx]).baseName()) # 곡 제목을 표시
        self.setWindowTitle(QFileInfo(self.playlist[idx]).baseName() + "- MP3 Player")

        self.player.play()

    # 재생/일시정지 버튼 상태 변경
    def sync_play_button(self, state):
        is_playing = (state == QMediaPlayer.State.PlayingState)
        # Checked 상태 바꾸기
        self.btn_pnp.blockSignals(True) # 루프 방지
        self.btn_pnp.setChecked(is_playing)
        self.btn_pnp.blockSignals(False)

    # play or pause
    def play_or_pause_slot(self):
        if not self.playlist: # 플레이리스트가 비어 있다면
            QMessageBox.warning(self, 'No Tracks', '플레이리스트에 재생할 곡이 없습니다!')
            self.sync_play_button(self.player.state()) # 버튼 되돌리기
            return

        if self.player.state() == QMediaPlayer.State.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    # 이전 트랙 재생 | 되돌아가기
    def previous_track_slot(self):
        if not self.playlist: # 첫 재생 상태일 경우
            return

        if self.history: # 재생 기록이 있으면 가장 마지막에 재생했던 곡으로 돌아간다
            idx = self.history.pop()
            self.current_index = idx
            self.load_track(idx)
            return

        # 트랙이 로드조차 안 된 상태일 때 아무 것도 안 함
        if self.current_index < 0:
            return

        # 셔플 모드이면 랜덤, 아니면 순차/반복 로직
        if self.is_shuffle:
            nxt = random.randrange(len(self.playlist))
            # 같은 곡이 선택될 수 있으니, 리스트가 2개 이상일 때만 재시도
            while len(self.playlist) > 1 and nxt == self.current_index:
                nxt = random.randrange(len(self.playlist))
            self.current_index = nxt
        else:
            # 순차 모드: 이전 인덱스로 이동 or 반복 모드라면 맨 끝으로
            if self.current_index > 0:
                self.current_index -= 1
            elif self.is_loop:
                self.current_index = len(self.playlist) - 1
            else:
                self.player.setPosition(0) # 첫 트랙에서 바로 이전을 누르면 재시작
                return

        self.load_track(self.current_index)

    def next_track_slot(self):
        if not self.playlist:
            return

        if self.current_index >= 0:
            self.history.append(self.current_index) # 재생 기록 추가

        # history에 모든 노래가 들어오면 history 초기화
        if len(self.history) >= len(self.playlist):
            self.history.clear()

        # Shuffle 모드인 경우
        if self.is_shuffle:
            # 남은 후보들: 전체 인덱스 중 아직 history에 없는 것
            candidates = [i for i in range(len(self.playlist)) if i not in self.history]
            nxt = random.choice(candidates)
            self.current_index = nxt
            self.load_track(nxt)
            return

        # 순차 모드일 때
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
        elif self.is_loop:
            self.current_index = 0
        else:
            return  # 모드 off & 끝에 도달하면 중지

        self.load_track(self.current_index)

    # 트랙이 완전히 끝나면 자동으로 next_track_slot()
    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_track_slot()

    # 현재 재생 지점 표시
    def update_position(self, pos):
        self.play_bar.setValue(pos)
        secs = pos // 1000
        m, s = divmod(secs, 60)
        self.lbl_current.setText(f'{m:02d}:{s:02d}')

    # 전체 길이 표시
    def update_duration(self, dur):
        self.play_bar.setRange(0, dur)
        secs = dur // 1000
        m, s = divmod(secs, 60)
        self.lbl_total.setText(f'{m:02d}:{s:02d}')

    def seek(self, pos):
        self.player.setPosition(pos)

    # 셔플 모드 토글
    def toggle_shuffle_slot(self, checked: bool):
        self.is_shuffle = checked

    # 반복 모드 토글
    def toggle_loop_slot(self, checked: bool):
        self.is_loop = checked

    # 볼륨 조절
    def volume_changed(self, value: int):
        # 실제 볼륨 반영
        self.player.setVolume(value)
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(value)
        self.volume_slider.blockSignals(False)
        # 레이블에 퍼센트로 표시
        self.lbl_volume.setText(f"Volume: {value}%")

    # 현재 재생 중인 음악 제거
    def remove_current_track_slot(self):
        idx = self.current_index
        print(idx)
        # 재생 중인 트랙이 없으면 아무 것도 하지 않음
        if idx < 0 or idx >= len(self.playlist):
            return

        name = QFileInfo(self.playlist[idx]).fileName()
        reply = QMessageBox.question(
            self,
            'Remove Current Track',
            f'"{name}"을(를) 플레이리스트에서 제거하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 리스트에서 제거
        self.playlist.pop(idx)
        # 모델 갱신
        self._update_playlist_model()

        # 제거 후 재생할 트랙 결정
        if self.playlist:
            # 지금 idx 위치에 다음 트랙(혹은 순환)을 재생
            self.current_index = idx % len(self.playlist)
            self.load_track(self.current_index)
        else:
            # 남은 트랙이 없으면 stop
            self.current_index = -1
            self.player.stop()
            self.lbl_music_name.setText("Choose your music")

    # Playlist 섹션 기능 구현

    # 플레이리스트에서 음악 선택하기
    def play_selected(self, index: QModelIndex):
        if self.current_index >= 0:
            self.history.append(self.current_index)

        self.current_index = index.row()
        self.load_track(self.current_index)

    # 플레이리스트에서 파일 추가하기
    def add_files_slot(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Add Audio Files',
            '',
            'Audio Files (*.mp3 *.wav *.flac *.aac *.ogg)'
        )
        if not files:
            return

        # playlist에 새 경로들 추가
        self.playlist.extend(files)
        self._update_playlist_model()

    # 플레이리스트에서 음악 1개 제거하기
    def remove_item_slot(self):
        idx = self.listView.currentIndex().row()
        if idx < 0 or idx >= len(self.playlist):
            return

        name = QFileInfo(self.playlist[idx]).fileName()
        reply = QMessageBox.question(
            self,
            'Remove Track',
            f'"{name}" 을(를) 플레이리스트에서 제거하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.playlist.pop(idx)
            self._update_playlist_model()

    # 플레이리스트의 음악 모두 제거하기
    def remove_all_slot(self):
        if not self.playlist:
            return

        reply = QMessageBox.question(
            self,
            'Remove All',
            '플레이리스트의 모든 트랙을 제거하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.playlist.clear()
            self._update_playlist_model()

    # 모델 업데이트 및 UI 초기화
    def _update_playlist_model(self):
        # 파일명만 뽑아서 모델에
        names = [QFileInfo(p).fileName() for p in self.playlist]
        self.model.setStringList(names)

        # 인덱스 유효 범위 조정
        if not self.playlist:
            self.current_index = -1
            self.player.stop()

            # 기본 UI 상태로 복원
            self.setWindowTitle("MP3 Player")
            self.lbl_music_name.setText("Choose your music")
            return
        # 플레이리스트에 아이템이 남아 있을 때 (인덱스 보정 및 자동 재생)
        self.current_index = min(self.current_index, len(self.playlist) - 1)
        self.load_track(self.current_index)

        # 현재 트랙 이름을 타이틀에도 반영
        title = QFileInfo(self.playlist[self.current_index]).baseName()
        self.setWindowTitle(f"{title} - MP3 Player")

    # Help 메뉴 기능 구현 ---------------------
    def about_slot(self):
        QMessageBox.about(self, 'MP3 Player made with PyQt',
                              '만든이: 이은서\n\r버전 정보: 1.0.0')

    # 스타일 ---------------------------------
    def eventFilter(self, obj, event):
        color = QColor(252, 252, 252)

        if event.type() == QEvent.HoverEnter:
            if obj.isChecked():
                color = QColor(20, 255, 236)
            obj.setGraphicsEffect(create_default_shadow((0, 0), 20, color))
        elif event.type() == QEvent.HoverLeave:
            obj.setGraphicsEffect(None)
        return super().eventFilter(obj, event)

    def update_button_shadow(self, btn):
        if btn.underMouse():
            color = QColor(20, 255, 236) if btn.isChecked() else QColor(252, 252, 252)
            btn.setGraphicsEffect(create_default_shadow((0, 0), 20, color))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ExampleApp()
    main_window.show()
    sys.exit(app.exec())