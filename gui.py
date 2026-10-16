from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QListWidget
)
from PySide6.QtCore import Qt

from runner import run
from player import Player

from pathlib import Path

folder="score_set/midi"

class MidiWindow(QWidget):

    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        self.resize(
            300,
            400
        )

        self.player = Player(
            dry_run=False
        )
        
        self.files = list(Path(folder).glob("*.mid")) + list(Path(folder).glob("*.midi"))

        self.play_button = QPushButton("播放")
        self.stop_button = QPushButton("取消")
        self.file_list = QListWidget()
        for file in self.files:
            self.file_list.addItem(file.name)

        layout = QVBoxLayout()

        layout.addWidget(self.file_list)

        layout.addWidget(
            self.play_button
        )

        layout.addWidget(
            self.stop_button
        )

        self.setLayout(layout)


        self.play_button.clicked.connect(
            self.play
        )

        self.stop_button.clicked.connect(
            self.stop
        )

        self.setWindowOpacity(0.8)

    def play(self):
        row = self.file_list.currentRow()

        if row == -1:
            return

        path = self.files[row]

        info = run(
            str(path),
            speed=0.5,
            optimization=True
        )
        '''暂停3s'''
        import time
        time.sleep(3)

        self.player.start(
            info["events"]
        )

    def stop(self):
        self.player.stop()



app = QApplication([])

window = MidiWindow()

window.show()

app.exec()
