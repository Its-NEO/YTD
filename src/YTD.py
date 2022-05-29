import os.path
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from math import floor
import time

import pytube.exceptions
from pytube import Playlist
from pytube import YouTube
from pytube.cli import on_progress

config_path = os.getcwd() + r'\config.ini'
config = ConfigParser()


def check_config():
    config.read(config_path)
    if not os.path.exists(config.get('Client Info', 'Download Path')):
        print('Download Path might have been modified or changed')
        create_config()


def create_config():
    if os.path.exists(config_path):
        os.remove(config_path)
    print('Set Download Path:')
    download_path = input()
    if os.path.isdir(download_path):
        add_to_config(download_path)
    else:
        print('Not a Valid Path!\nClosing')
        print('<----------==========End==========---------->', end='\n\n')
        return


def add_to_config(download_path):
    config['Client Info'] = {
        'Download Path': download_path
    }
    with open(config_path, 'w') as file:
        config.write(file)
        file.flush()
        file.close()
        print('Download path updated successfully')


def on_download_complete(self, file_path):
    print('Downloaded successfully and saved to:', file_path)


def download_vid(video):
    video.get('object'). \
        download(output_path=video.get('output_path'),
                 filename=video.get('filename'),
                 filename_prefix=video.get('filename_prefix'))


def download_playlist(parallel_download=False):
    link = input('Enter the Playlist URL: ')
    try:
        youtube_list = Playlist(link)
    except pytube.exceptions.RegexMatchError:
        print('Not a Valid URL!\nClosing')
        print('<----------==========End==========---------->', end='\n\n')
        return

    video_count = len(youtube_list.video_urls)
    print('<----------==========PLAYLIST FOUND==========---------->')
    print(f'{youtube_list.title}\n'
          f'Number of Videos: {video_count}')
    print('<-------------=========================------------->')

    print('Is this the playlist you are looking for? (y/n)')
    video_choice = input('Your Choice: ').lower()

    if not (video_choice == 'y' or video_choice == 'yes'):
        print('Closing')
        print('<----------==========End==========---------->', end='\n\n')
        return

    streaming_qualities = {1: '720p', 2: '360p'}
    print('Choose a Video Quality:')
    print('1. 720p\n2. 360p\n3. Exit')
    quality_choice = int(input('Your Choice: '))

    if quality_choice == 3:
        print('Closing')
        print('<----------==========End==========---------->', end='\n\n')
        return

    config.read(config_path)
    dir_name = os.path.join(config.get('Client Info', 'Download Path'),
                            youtube_list.title.replace('|', '').replace('?', ''))

    videos = []
    print('Fetching Downloads...')
    for i, youtube in enumerate(youtube_list.videos):
        if not parallel_download:
            youtube.register_on_progress_callback(on_progress)
        youtube.register_on_complete_callback(on_download_complete)
        video = youtube.streams.get_by_resolution(streaming_qualities.get(quality_choice))

        if video is None:
            video = youtube.streams.get_by_resolution(streaming_qualities.get(quality_choice + 1))
            print(print(f'Downloading: {video.title} at a lower {video.resolution} resolution'))

        print('<----------==========VIDEO FOUND==========---------->')
        print(f'{i+1}/{video_count}')
        print(f'{youtube.title}\n'
              f'Channel: {youtube.author} | '
              f'Publish Date: {youtube.publish_date} | '
              f'Length: {floor(youtube.length / 60)}:{youtube.length - floor(youtube.length / 60) * 60}')
        print(f'<-------------=========={i+1}/{video_count}==========------------->')

        if video.exists_at_path(dir_name):
            print(f'Output: Video already exists at {dir_name}\nSkipping...')
            continue

        videos.append({'object': video,
                       'output_path': dir_name,
                       'filename': video.default_filename,
                       'filename_prefix': str(i) + '. '})

    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)

    if parallel_download:
        t = time.perf_counter()
        with ThreadPoolExecutor() as executor:
            executor.map(download_vid, videos)
        print('Finished in', time.perf_counter() - t, 'seconds')
    else:
        t = time.perf_counter()
        for video in videos:
            video.get('object').\
                download(output_path=video.get('output_path'),
                         filename=video.get('filename'),
                         filename_prefix=video.get('filename_prefix'))
        print('Finished in', time.perf_counter() - t, 'seconds')


def download():
    link = input('Enter the Video URL: ')
    try:
        youtube = YouTube(link, on_progress_callback=on_progress, on_complete_callback=on_download_complete)
    except pytube.exceptions.RegexMatchError:
        print('Not a Valid URL!\nClosing')
        print('<----------==========End==========---------->', end='\n\n')
        return

    print('<----------==========VIDEO FOUND==========---------->')
    print(f'{youtube.title}\n'
          f'Channel: {youtube.author} | '
          f'Publish Date: {youtube.publish_date} | '
          f'Length: {floor(youtube.length / 60)}:{youtube.length - floor(youtube.length / 60) * 60}')
    print('<-------------=========================------------->')

    print('Is this the video you are looking for? (y/n)')
    video_choice = input('Your Choice: ').lower()

    if not (video_choice == 'y' or video_choice == 'yes'):
        print('Closing')
        print('<----------==========End==========---------->', end='\n\n')
        return
    video_list = youtube.streaming_data.get('formats')

    print('Choose a Video Format:')
    count = 0
    for v in video_list:
        print(f'{count + 1}. {v.get("qualityLabel")} at {v.get("fps")} fps')
        count += 1
    print(f'{count + 1}. Exit')
    quality_choice = input('Your Choice: ')

    if len(video_list) >= int(quality_choice) >= 1:
        res = video_list[int(quality_choice) - 1].get('qualityLabel')
    elif int(quality_choice) == count + 1:
        print('Closing')
        print('<----------==========End==========---------->', end='\n\n')
        return
    else:
        print('Invalid Option!\nClosing')
        print('<----------==========End==========---------->', end='\n\n')
        return
    video = youtube.streams.filter(res=res).first()

    print(f'Downloading: {video.title} at {video.resolution} resolution')
    if video.exists_at_path(config_path):
        print(f'Output: File already exists at {config_path}\nClosing')
        print('<----------==========End==========---------->', end='\n\n')
        return

    config.read(config_path)
    t = time.perf_counter()
    video.download(output_path=config.get('Client Info', 'Download Path'), filename=video.default_filename)
    print('Finished in', time.perf_counter() - t, 'seconds')


def main_interface():
    while True:
        if not os.path.exists(config_path):
            print('<----------==========Init==========---------->')
            create_config()
        else:
            print('<----------==========Start==========---------->')
            print('Choose your options:\n1. Download Video\n2. Download Playlist\n'
                  '3. Download Playlist Parallel(experimental)\n4. Change Download Path\n5. Exit')
            choice = input('Your Choice: ')
            if choice == '1':
                check_config()
                download()
            elif choice == '2':
                check_config()
                download_playlist()
            elif choice == '3':
                check_config()
                download_playlist(True)
            elif choice == '4':
                create_config()
            elif choice == '5':
                print('Closing')
                print('<----------==========End==========---------->', end='\n\n')
                break
            else:
                print('Not a Valid Option')


if __name__ == '__main__':
    main_interface()
