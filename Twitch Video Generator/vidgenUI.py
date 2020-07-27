from PyQt5.QtCore import QDir, Qt, QUrl, pyqtSignal, QPoint, QRect, QObject
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
import vidGen
import sys
import server
from PyQt5.QtGui import QIcon

class renderingScreen(QDialog):
    script_queue_update = pyqtSignal()
    render_progress = pyqtSignal()

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi(f"UI/videoRendering.ui", self)

        try:
            self.setWindowIcon(QIcon('Logo/twitchlogo.png'))
        except Exception as e:
            pass

        self.script_queue_update.connect(self.updateScriptScreen)
        self.render_progress.connect(self.updateRenderProgress)
        self.testServerFTP()
        self.testServerConnection.clicked.connect(self.testServerFTP)

    def closeEvent(self, evnt):
        sys.exit()


    def testServerFTP(self):
        success = server.testFTPConnection()
        if success:
            self.connectionStatus.setText("Server connection fine!")
        else:
            self.connectionStatus.setText("Could not connect to server! Ensure it is online and FTP username/password are correct in config.ini.")


    def updateScriptScreen(self):
        self.scriptQueue.clear()
        for i, script in enumerate(vidGen.saved_videos):
            amount_clips = len(script.clips)
            self.scriptQueue.append(f'({i + 1}/{len(vidGen.saved_videos)}) clips: {amount_clips}')

    def updateRenderProgress(self):
        self.renderStatus.setText(vidGen.render_message)
        self.progressBar.setMaximum(vidGen.render_max_progress)
        self.progressBar.setValue(vidGen.render_current_progress)