
import string
import requests
import urllib.request
import database
import scriptwrapper
import shutil
import subprocess
import settings
from time import sleep
from pymediainfo import MediaInfo


forceStop = False

def getGameID(input_game_name):
    #Search for and add game categories
    game = requests.get(f"https://api.twitch.tv/helix/games?name={input_game_name}", headers={"Client-ID": settings.client_id, "Authorization": f"Bearer {settings.bearer}"}).json()
    print(game)
    if "error" in game.keys():
        return "ERROR"
    elif len(game["data"]) == 0:
        return "ERROR"
    else:
        return game["data"][0]["id"]


def getAllClips(game_name, window):
    global all_clips_found, forceStop
    # format the saved_ids by taking it out of tuple form
    bad_ids = []

    for id in database.getAllSavedGameIDs():
        bad_ids.append(id[0])

    clips = []
    print(f"Looking for all clips for game {game_name}")
    used_cursors = []
    attempt = 0
    next_page_cursor = None
    period = "day"
    oldPeriodAmount = 0
    while True:
        try:
            if next_page_cursor is None:
                response = requests.get(f"https://api.twitch.tv/kraken/clips/top?game={game_name}&period={period}&language={settings.language}&limit={100}", headers={"Client-ID": settings.client_id, "Accept": "application/vnd.twitchtv.v5+json"}).json()

            else:
                response = requests.get(f"https://api.twitch.tv/kraken/clips/top?game={game_name}&period={period}&language={settings.language}&limit={100}&cursor={next_page_cursor}", headers={"Client-ID": settings.client_id, "Accept": "application/vnd.twitchtv.v5+json"}).json()

            raw_clips = response["clips"]


            next_page_cursor = response["_cursor"]
            if next_page_cursor in used_cursors:
                window.update_log_found_clips.emit(game_name, oldPeriodAmount, period)
                oldPeriodAmount = 0
                used_cursors.clear()
                old_period = period
                if period == "day":
                    period = "week"
                elif period == "week":
                    period = "month"
                elif period == "month":
                    period = "all"
                elif period == "all":
                    print("MAX AMOUNT OF AVAILABLE CLIPS FOUND. CANNOT LOOK FOR MORE")
                    break

                print(f"Max clips found for {game_name} in time frame {old_period} increasing time frame to {period}")
                continue
            used_cursors.append(next_page_cursor)
            print(f"Found {len(raw_clips)} for time frame {period}")

            for clip in raw_clips:
                id = int(clip['tracking_id'])
                streamer_name = clip['broadcaster']['display_name']
                url = clip['thumbnails']['tiny'].replace('-preview-86x45.jpg', '.mp4')
                title = clip['title']
                channel_url = clip['broadcaster']['channel_url']

                # bad_ids is a list of ids that we have already checked to see if the id is in the database and it is
                if id in bad_ids:
                    continue

                # clip id already recorded in clips
                if id in [newclip.id for newclip in clips]:
                    continue

                twitch_clip = scriptwrapper.TwitchClipWrapper(id, url, streamer_name, title, channel_url)
                clips.append(twitch_clip)
                oldPeriodAmount += 1
            #     if len(clips) > 5:
            #         break
            # if len(clips) > 5:
            #     break
            attempt += 1
            print(f"{len(clips)} unique {game_name} clips found")
            if forceStop:
                print("Forced Stop Finding Process")
                forceStop = False
                break
        except Exception as e:
            print(e)
            print("exception occured downloading. waiting and retrying")
            sleep(5)

    print(f"Found {len(clips)} unique clips")
    window.update_log_found_total_clips.emit(game_name, len(clips))

    for clip in clips:
        database.addFoundClip(clip, game_name)

    return clips

def autoDownloadClips(game, clips, window):
    global forceStop
    #Downloading the clips with custom naming scheme
    window.update_log_start_downloading_game.emit(game, len(clips))
    print('Downloading...')
    for i, clip in enumerate(clips):
        print("Downloading Clip %s/%s" % (i + 1, len(clips)))
        try:
            urllib.request.urlretrieve(clip.url, f"{settings.vid_filepath}/{clip.streamer_name}-{clip.id}.mp4")
            clip.mp4 = f"{clip.streamer_name}-{clip.id}"

            media_info = MediaInfo.parse(f"{settings.vid_filepath}/{clip.streamer_name}-{clip.id}.mp4")
            duration = media_info.tracks[0].duration
            clip.vid_duration = float(duration) / 1000
            database.updateStatusWithClip(clip.id, "DOWNLOADED", clip)
        except Exception as e:
            print(e)
            print("Error downloading clip")
            database.updateStatusWithClip(clip.id, "BAD", clip)

        window.update_log_downloaded_clip.emit(i + 1)
        if forceStop:
            print("Forced Stop Downloading Process")
            forceStop = False
            break
    window.update_done_downloading_game.emit(game, len(clips))




