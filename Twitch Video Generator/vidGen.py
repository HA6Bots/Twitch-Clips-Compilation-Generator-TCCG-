from moviepy.editor import *
import random
import os
import time
import shutil
import subprocess
import re
from time import sleep
import string
import datetime
#import clientUI
from pysubs2 import SSAFile, SSAEvent, SSAStyle, make_time
import pickle
import settings
from pydub import AudioSegment
from distutils.dir_util import copy_tree

#File Paths



#Creating file paths that are needed


saved_videos = None
render_current_progress = None
render_max_progress = None
render_message = None


#------------------------------------------C O M P I L A T I O N   G E N E R A T O R------------------------------------------

#Getting Filename without extension and storing it into a list
def getFileNames(file_path):
    files = [os.path.splitext(filename)[0] for filename in os.listdir(file_path)]
    return files

def deleteSkippedClips(clips):
    for clip in clips:
        print(clip)
        os.remove(f'{clip}')

def deleteAllFilesInPath(path):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def renderThread(renderingScreen):
    global saved_videos
    while True:
        time.sleep(5)
        savedFiles = getFileNames(f'{settings.temp_path}')
        saved_videos = []
        save_names = []
        for file in savedFiles:
            try:
                with open(f'{settings.temp_path}/{file}/vid.data', 'rb') as pickle_file:
                    script = pickle.load(pickle_file)
                    saved_videos.append(script)
                save_names.append(f'{settings.temp_path}/{file}')
            except FileNotFoundError:
                pass
                #print("No vid.data file in %s" % file)
        renderingScreen.script_queue_update.emit()

        for i, video in enumerate(saved_videos):
            print(f'Rendering script {i + 1}/{len(saved_videos)}')

            t0 = datetime.datetime.now()
            renderVideo(video, renderingScreen)
            t1 = datetime.datetime.now()

            total = t1-t0
            print("Rendering Time %s" % total)

            if settings.backupVids:
                backupName = save_names[i].replace(settings.temp_path, settings.backup_path)
                if os.path.exists(backupName):
                    print("Backup for video %s already exists" % backupName)
                else:
                    print("Making backup of video to %s" % backupName)
                    copy_tree(save_names[i], backupName)


            print(f"Deleting video folder {save_names[i]}")
            shutil.rmtree(save_names[i])

                # delete all the temp videos
            try:
                deleteAllFilesInPath(settings.vid_finishedvids)
            except Exception as e:
                print(e)
                print("Couldn't delete clips")


#bgr format with &h at start and & at end
def getColour(colourstring):
    if colourstring == "Blue":
        return "&hff0000&"
    elif colourstring == "Red":
        return "&h0000ff&"
    elif colourstring == "Green":
        return "&h00ff7f&"
    elif colourstring == "Orange":
        return "&h007fff&"
    elif colourstring == "Black":
        return "&h000000&"
    elif colourstring == "Purple":
        return "&hbf00bf&"
    elif colourstring == "Pink":
        return "&hff00ff&"
    elif colourstring == "White":
        return "&hffffff&"
    elif colourstring == "Yellow":
        return "&h00ffff&"

#Adding Streamer's name to the video clip
def renderVideo(video, rendering_screen):
    global render_current_progress, render_max_progress, render_message
    t0 = datetime.datetime.now()

    clips = video.clips
    colour1 = getColour(video.colour1)
    colour2 = getColour(video.colour2)
    music_type = video.audio_cat

    subprocess._cleanup = lambda: None
    credits = []
    streamers_in_cred = []

    render_current_progress = 0
    # see where render_current_progress += 1

    amount = 0
    for clip in clips:
        if clip.isUsed:
            amount += 1

    render_max_progress = amount * 3 + 1 + 1
    render_message = "Beginning Rendering"
    rendering_screen.render_progress.emit()

    current_date = datetime.datetime.today().strftime("%m-%d-%Y__%H-%M-%S")
    fClips = []
    start_duration = 0
    end_duration = 0


    # render progress 1
    for i, clip in enumerate(clips):
        if clip.isUsed:
            name = clip.streamer_name
            mp4 = clip.mp4
            subs = SSAFile()

            if name is not None and name not in streamers_in_cred and not clip.isUpload:
                credits.append(f"Streamer: {clip.streamer_name} Channel: {clip.channel_url}")
                streamers_in_cred.append(clip.streamer_name)

            if clip.start_cut is None:
                clip.start_cut = 0

            if clip.end_cut is None:
                clip.end_cut = 0

            start_trim = round(clip.start_cut / 1000, 1)
            end_trim = round(clip.end_cut / 1000, 1)

            final_duration = round(clip.vid_duration - end_trim - start_trim, 1)
            audio = clip.audio

            if name is None:
                name = ""


            render_message = f"Adding text ({i + 1}/{len(clips)})"
            rendering_screen.render_progress.emit()
            subs.styles['vidText'] = SSAStyle(alignment=7, fontname='Gilroy-ExtraBold', fontsize=25, marginl=4, marginv=-2.5, marginr=0, outline=2, outlinecolor=colour2, primarycolor=colour1, shadow=0)
            if settings.includeStreamerName:
                subs.append(SSAEvent(start=make_time(s=0), end=make_time(s=60),style='vidText' ,text=f"{name}"))
            subs.save(f'subtitleFile.ass')
            render_current_progress += 1
            render_message = f"Done Adding text ({i + 1}/{len(clips)})"
            rendering_screen.render_progress.emit()

            print(f"Adding text ({i + 1}/{len(clips)}) to video: {mp4}.mp4")

            render_message = f"Adding text to video ({i + 1}/{len(clips)})"
            rendering_screen.render_progress.emit()
            print(f"Rendering video ({i + 1}/{len(clips)}) to \"{settings.vid_finishedvids}\"/{mp4}_finished.mp4")


            mp4name = mp4
            mp4path = f"{mp4}.mp4"

            if len(mp4.split("/")) > 2:
                name = len(mp4.split("/"))
                mp4name = mp4.split("/")[name-1].replace(".mp4", "")
                mp4path = mp4[1:]

            if not clip.isInterval and not clip.isIntro:
                print("%s duration %s" % (mp4name, final_duration))
                if end_trim == 0 and start_trim == 0:
                    print("%s no trim" % mp4name)
                    os.system(f"ffmpeg -y -fflags genpts -i \"{mp4path}\" -vf \"ass=subtitleFile.ass, scale=1920:1080\" \"{settings.vid_finishedvids}/{mp4name}_finished.mp4\"")
                elif end_trim > 0 and start_trim > 0:
                    print("%s start trim %s and end trim %s" % (mp4name, start_trim, end_trim))
                    os.system(f"ffmpeg -y -fflags genpts -i \"{mp4path}\" -ss {start_trim} -t {final_duration} -vf \"ass=subtitleFile.ass, scale=1920:1080\" \"{settings.vid_finishedvids}/{mp4name}_finished.mp4\"")
                elif end_trim > 0 and start_trim == 0:
                    print("%s end trim %s" % (mp4name,  end_trim))

                    os.system(f"ffmpeg -y -fflags genpts -i \"{mp4path}\" -t {clip.vid_duration - end_trim} -vf \"ass=subtitleFile.ass, scale=1920:1080\" \"{settings.vid_finishedvids}/{mp4name}_finished.mp4\"")
                elif end_trim == 0 and start_trim > 0:
                    print("%s start trim %s" % (mp4name,  start_trim))
                    os.system(f"ffmpeg -y -fflags genpts -i \"{mp4path}\" -ss {start_trim} -vf \"ass=subtitleFile.ass, scale=1920:1080\" \"{settings.vid_finishedvids}/{mp4name}_finished.mp4\"")

            render_current_progress += 1
            render_message = f"Done Adding text to video ({i + 1}/{len(clips)})"
            rendering_screen.render_progress.emit()


            render_message = f"Adding clip to list ({i + 1}/{len(clips)})"
            rendering_screen.render_progress.emit()

            if not clip.isInterval and not clip.isIntro:
                finish = VideoFileClip(f'{settings.vid_finishedvids}/{mp4name}_finished.mp4').fx(afx.volumex, audio)
            else:
                finish = VideoFileClip(f'{mp4path}').fx(afx.volumex, audio)

            end_duration += finish.duration
            fClips.append(finish)

            render_current_progress += 1
            render_message = f"Done Adding clip to list ({i + 1}/{len(clips)})"
            rendering_screen.render_progress.emit()
            if i <= 2:
                start_duration += finish.duration

    musicFiles = getFileNames(f'{settings.asset_file_path}/Music')
    random.shuffle(musicFiles)

    print("done working out durations")
    final_concat = concatenate_videoclips(fClips)
    print("done combining clips")
    print(musicFiles)

    # render progress 2
    render_message = "Creating audio loop"
    rendering_screen.render_progress.emit()
    #audio = AudioFileClip(f'{settings.asset_file_path}/Music/{musicFiles[0]}.mp3').fx(afx.volumex, float(video.background_volume))

    print("Using music type %s" % music_type)
    musicFolders = (getFileNames("Assets/Music"))

    if not musicFolders:
        music_type = "None"
        print("No music folders, defaulting to no audio")

    if not music_type == "None":

        try:
            to_combine = []
            music_combined_duration = 0

            while music_combined_duration < end_duration:
                random_file=random.choice(os.listdir(f'{settings.asset_file_path}/Music/{music_type}'))
                sound1 = AudioSegment.from_wav(f"Assets/Music/{music_type}/{random_file}")
                music_combined_duration += sound1.duration_seconds
                to_combine.append(sound1)

            combined_sounds = sum(to_combine)
            combined_sounds.export(f"{settings.temp_path}/music-loop-uncut.wav", format="wav")
            audio_loop_without_pause = AudioSegment.from_wav("%s/music-loop-uncut.wav" % settings.temp_path)
            new_audio = AudioSegment.silent(duration=(start_duration * 1000)) + audio_loop_without_pause
            new_audio.export(f"{settings.temp_path}/music-loop-uncut_with_pause.mp3", format="mp3")

            music_loop = afx.audio_loop(AudioFileClip(f"{settings.temp_path}/music-loop-uncut_with_pause.mp3"), duration=end_duration).fx(afx.volumex, float(video.background_volume))
            #music_loop = afx.audio_loop(audio, duration=end_duration)
            music_loop.write_audiofile(f'{settings.temp_path}/music-loop.mp3')
        except Exception as e:
            print(e)
            music_type = "None"




    render_current_progress += 1
    render_message = "Done Creating audio loop"
    rendering_screen.render_progress.emit()
    # render progress 3
    render_message = "Writing final video"
    rendering_screen.render_progress.emit()

    if not music_type == "None":
        final_vid_with_music = final_concat.set_audio(CompositeAudioClip([final_concat.audio, AudioFileClip(f'{settings.temp_path}/music-loop.mp3')]))
    else:
        final_vid_with_music = final_concat.set_audio(final_concat.audio)

    sleep(5)
    if settings.ffmpeg_audio:
        print("Rendering with audio fix")
        final_vid_with_music.write_videofile(f'{settings.final_video_path}/TwitchMoments_{current_date}.mp4', fps=settings.fps,
                                             threads=16, temp_audiofile=f'{settings.final_video_path}/TwitchMoments_{current_date}audio.mp3', remove_temp = False)
        sleep(5)
        os.system(f"ffmpeg -y -i \"{settings.final_video_path}/TwitchMoments_{current_date}.mp4\" -i \"{settings.final_video_path}/TwitchMoments_{current_date}audio.mp3\" -c:v copy -c:a aac \"{settings.final_video_path}/TwitchMoments_{current_date}fixaudio.mp4\"")
        sleep(5)
        os.remove(f'{settings.final_video_path}/TwitchMoments_{current_date}.mp4')
        os.remove(f'{settings.final_video_path}/TwitchMoments_{current_date}audio.mp3')
    else:
        final_vid_with_music.write_videofile(f'{settings.final_video_path}/TwitchMoments_{current_date}.mp4', fps=settings.fps,
                                             threads=16)
        sleep(5)


    render_current_progress += 1
    t1 = datetime.datetime.now()
    total = t1-t0
    render_message = "Done writing final video (%s)" % total
    rendering_screen.render_progress.emit()
    f = None
    if settings.ffmpeg_audio:
        f = open(f"{settings.final_video_path}/TwitchMoments_{current_date}fixaudio.txt", "w+")
    else:
        f = open(f"{settings.final_video_path}/TwitchMoments_{current_date}.txt", "w+")
    f.write("A special thanks to the following: \n\n")
    for cred in credits:
        f.write(cred + "\n")
    f.close()
    sleep(10)

