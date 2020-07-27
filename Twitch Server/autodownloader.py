import twitch
import database
from time import sleep
from threading import Thread

class AutoDownloader():
    def __init__(self, window, downloadqueue):
        self.window = window
        self.autoDownloadQueue = downloadqueue
        self.gameIndex = 0
        self.auto = False


    def startAutoMode(self):
        self.auto = True
        self.findClips()

    def startDownloading(self):
        self.downloadClips()


    def startFinding(self):
        self.findClips()


    def stop(self):
        twitch.forceStop = True


    def findClips(self):
        if self.gameIndex == 0:
            self.window.start_clip_search.emit()

        if not self.gameIndex == len(self.autoDownloadQueue):
            Thread(target=twitch.getAllClips, args=(self.autoDownloadQueue[self.gameIndex], self.window)).start()
            self.gameIndex += 1
        else:
            self.gameIndex = 0
            self.window.end_find_search.emit()
            if self.auto:
                self.downloadClips()

    def downloadClips(self):
        if self.gameIndex == 0:
            self.window.start_download_search.emit()
        if not self.gameIndex == len(self.autoDownloadQueue):
            game = self.autoDownloadQueue[self.gameIndex]
            clips = database.getFoundGameClips(game, int(self.window.bulkDownloadAmount.text()))

            Thread(target=twitch.autoDownloadClips, args=(game, clips, self.window)).start()
            self.gameIndex += 1
        else:
            self.gameIndex = 0
            self.window.end_download_search.emit()
            if self.auto:
                self.findClips()
