from PyQt5 import QtWidgets
from moviepy.editor import *
from threading import Thread
#import vidGen
import server
import autodownloaderUI
import os
import ftplib
from time import sleep
import database
import settings
import scriptwrapper
from pydub import AudioSegment
import random
import settings




class App():
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        app.processEvents()


        autodownloader = autodownloaderUI.PassiveDownloaderWindow()
        autodownloader.show()



        Thread(target=server.VideoGeneratorCommunications).start()
        Thread(target=server.VideoGeneratorRenderStatus).start()



        sys.exit(app.exec_())

def init():
    app = App()



sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


def getFileNames(file_path):
    files = [os.path.splitext(filename)[0] for filename in os.listdir(file_path)]
    return files

if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_directory)
    settings.generateConfigFile()
    if not os.path.exists("UploadedFiles"):
        os.mkdir("UploadedFiles")

    if not os.path.exists(settings.vid_filepath):
        os.mkdir(settings.vid_filepath)

    if not os.path.exists(settings.final_video_path):
        os.mkdir(settings.final_video_path)

    if not os.path.exists(settings.video_data_path):
        os.mkdir(settings.video_data_path)

    if not os.path.exists(settings.backup_path):
        os.mkdir(settings.backup_path)

    if not os.path.exists(settings.asset_file_path):
        os.mkdir(settings.asset_file_path)
        os.mkdir(f"{settings.asset_file_path}/Fonts")
        os.mkdir(f"{settings.asset_file_path}/Intervals")
        os.mkdir(f"{settings.asset_file_path}/Intros")
        os.mkdir(f"{settings.asset_file_path}/Music")



    database.startDatabase()
    server.init()

    App()


