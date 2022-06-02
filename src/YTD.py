import os.path
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from math import floor
import time

import pytube.exceptions
from pytube import YouTube
from pytube.cli import on_progress


def on_download_complete(stream, file_path):
    print('Downloaded successfully and saved to:', file_path)


def download_vid(video):
    video.get('object'). \
        download(output_path=video.get('output_path'),
                 filename=video.get('filename'),
                 filename_prefix=video.get('filename_prefix'))


def closing_statement():
    print('<----------==========End==========---------->', end='\n\n')


class YTD:

    def __init__(self, config_path=os.path.join(os.getcwd() + r'\config.ini')):
        self.config_path = config_path
        self.config = ConfigParser()

    def verify_config(self, change_download_path=False):
        """
        Checks if the config file exists with required configurations. Creates and initialises it if anything is wrong.
        :return: None
        """

        # if user chooses to rewrite the download path
        if change_download_path:
            os.remove(self.config_path)

        # if config path doesn't exist
        if not os.path.exists(self.config_path):
            download_path = input('Set Download Path: ')

            # if download path entered by user exist
            if os.path.isdir(download_path):
                self.config['Client Info'] = {
                    'Download Path': download_path
                }
                with open(self.config_path, 'w') as file:
                    self.config.write(file)
                    file.flush()
                    file.close()
                    print('Download path updated successfully!')
            else:
                print('Not a Valid Path!\nClosing')
                closing_statement()
                return

        # if config exists but download path doesn't
        self.config.read(self.config_path)
        if not os.path.exists(self.config.get('Client Info', 'Download Path')):
            print('Download Path might have been modified.')
            os.remove(self.config_path)
            self.verify_config()

    def download_playlist(self, parallel_download=False):
        self.verify_config()
        link = input('Enter the Playlist URL: ')
        try:
            youtube_list = pytube.Playlist(link)
        except pytube.exceptions.RegexMatchError:
            print('Not a Valid URL!\nClosing...')
            closing_statement()
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
            closing_statement()
            return

        streaming_qualities = {1: '720p', 2: '360p'}
        print('Choose a Video Quality:')
        print('1. 720p\n2. 360p\n3. Exit')
        quality_choice = int(input('Your Choice: '))

        if quality_choice == 3:
            print('Closing')
            closing_statement()
            return

        self.config.read(self.config_path)
        dir_name = os.path.join(self.config.get('Client Info', 'Download Path'),
                                youtube_list.title.replace('|', '').replace('?', ''))

        videos = []
        print('Fetching Downloads...')
        for i, youtube in enumerate(youtube_list.videos):
            youtube.register_on_complete_callback(on_download_complete)
            if not parallel_download:
                youtube.register_on_progress_callback(on_progress)

            video = youtube.streams.get_by_resolution(streaming_qualities.get(quality_choice))

            if video is None:
                video = youtube.streams.get_by_resolution(streaming_qualities.get(quality_choice + 1))
                print(f'Downloading: {video.title} at a lower {video.resolution} resolution')

            print('<----------==========VIDEO FOUND==========---------->')
            print(f'{i + 1}/{video_count}')
            print(f'{youtube.title}\n'
                  f'Channel: {youtube.author} | '
                  f'Publish Date: {youtube.publish_date} | '
                  f'Length: {floor(youtube.length / 60)}:{youtube.length - floor(youtube.length / 60) * 60}')
            print(f'<-------------=========={i + 1}/{video_count}==========------------->')

            if video.exists_at_path(dir_name):
                print(f'Output: Video already exists at {dir_name}\nSkipping...')
                continue

            videos.append({'object': video,
                           'output_path': dir_name,
                           'filename': video.default_filename,
                           'filename_prefix': str(i) + '. '})

        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        print('Downloading...')
        if parallel_download:
            t1 = time.perf_counter()
            with ThreadPoolExecutor() as executor:
                executor.map(download_vid, videos)
            t2 = time.perf_counter()
            print(f'Finished in {floor((t2 - t1) / 60)} min(s) : {(t2 - t1) - floor((t2 - t1) / 60) * 60} sec(s)')

        else:
            t1 = time.perf_counter()
            for video in videos:
                video.get('object'). \
                    download(output_path=video.get('output_path'),
                             filename=video.get('filename'),
                             filename_prefix=video.get('filename_prefix'))
            t2 = time.perf_counter()
            print(f'Finished in {floor((t2 - t1) / 60)} min(s) : {(t2 - t1) - floor((t2 - t1) / 60) * 60} sec(s)')

        closing_statement()

    def download(self):
        # verify config
        self.verify_config()

        # create a YouTube object
        link = input('Enter the Video URL: ')
        try:
            youtube = YouTube(link, on_progress_callback=on_progress, on_complete_callback=on_download_complete)
        except pytube.exceptions.RegexMatchError:
            print('Not a Valid URL!\nClosing...')
            closing_statement()
            return

        # displaying the video that is found
        print('<----------==========VIDEO FOUND==========---------->')
        print(f'{youtube.title}\n'
              f'Channel: {youtube.author} | '
              f'Publish Date: {youtube.publish_date} | '
              f'Length: {floor(youtube.length / 60)}:{youtube.length - floor(youtube.length / 60) * 60}')
        print('<-------------=========================------------->')

        # check if user wants this video
        print('Is this the video you are looking for? (y/n)')
        video_choice = input('Your Choice: ').lower()
        if not (video_choice == 'y' or video_choice == 'yes'):
            print('Exiting...')
            closing_statement()
            return

        # displaying different video formats available to the user. Exiting if user wants to.
        video_list = youtube.streaming_data.get('formats')
        print('Choose a Video Format:')
        count = 1
        for v in video_list:
            print(f'{count}. {v.get("qualityLabel")} at {v.get("fps")} fps')
            count += 1
        print(f'{count}. Exit')
        choice = input('Your Choice: ')
        if len(video_list) >= int(choice) >= 1:
            res = video_list[int(choice)].get('qualityLabel')
        elif int(choice) == count:
            print('Exiting')
            closing_statement()
            return
        else:
            print('Invalid Option!\nClosing...')
            closing_statement()
            return

        # Getting the desired video
        video = youtube.streams.filter(res=res).first()
        print(f'Downloading: {video.title} at {video.resolution} resolution')

        video_filename = video.default_filename

        # Checking if video already exists at the download path
        if video.exists_at_path(self.config.get('Client Info', 'Download Path')):
            print(f'File already exists at {self.config.get("Client Info", "Download Path")} with the same name')
            print('What do you want to do?\n1. Rewrite the file present there\n2. Rename your video\n3. Exit')
            choice = int(input('Your Choice: '))
            if choice == 1:
                os.remove(os.path.join(self.config.get('Client Info', 'Download Path'), video.default_filename))

            elif choice == 2:
                video_filename = input('Enter your new filename: ')

            elif choice == 3:
                closing_statement()
                return

        # download the video with all the given settings along with a performance counter
        t1 = time.perf_counter()
        video.download(output_path=self.config.get('Client Info', 'Download Path'), filename=video_filename)
        t2 = time.perf_counter()
        print(f'Finished in {floor((t2 - t1 / 60))} min(s) : {(t2 - t1) - floor((t2 - t1) / 60) * 60} sec(s)')

        closing_statement()

    def main_interface(self):
        """
        Spawns a CLI for the users to easily use the basic functionalities of the program

        :return: None
        """
        while True:
            # checking if config files are present and creating a new config if necessary
            if not os.path.exists(self.config_path):
                print('<----------==========Init==========---------->')
                self.verify_config()
            else:
                print('<----------==========Start==========---------->')
                print('Choose your options:\n1. Download Video\n2. Download Playlist\n'
                      '3. Download Playlist Parallel(experimental)\n4. Change Download Path\n5. Exit')
                choice = input('Your Choice: ')
                if choice == '1':
                    self.download()
                elif choice == '2':
                    self.download_playlist()
                elif choice == '3':
                    self.download_playlist(True)
                elif choice == '4':
                    self.verify_config(True)
                elif choice == '5':
                    print('Closing')
                    closing_statement()
                    break
                else:
                    print('Not a Valid Option')


if __name__ == '__main__':
    YTD().main_interface()
