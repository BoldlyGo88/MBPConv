import re
import shutil
import sqlite3
from pathlib import Path


movieboxpro = Path('C:\\Users\\happy\\Videos\\MovieBoxPro')
subtitle_cache = Path(str(movieboxpro) + '\\subby')
download_database = str(movieboxpro) + '\\Download.db'
movies, subs, index_errors, fileerrors = 0, 0, 0, 0


def clean_title(title):
    """ Turns Goodfellas_1234_1080p.mp4 into Goodfellas """
    media = re.search(r'^(.*?)_[0-9]+_[^_]+$', title)
    if media:
        return media.group(1).replace('_', '')


def get_subtitles(media_path, media_id, tvshow=False):
    """ Returns the media files year and copies found subtitles to the main folder. Requires Download.db from MovieBoxPro. """
    media_list = read_download_db(download_database)
    year, subtitles = get_media_details(media_id, media_list)

    for subdir in subtitle_cache.glob('*'):
        if subdir.is_dir() and media_id in subdir.name:
            if tvshow:
                pass
            else:
                try:
                    # hardcoded english subtitles but just change en to whatever language you prefer, jp for japanese as an example.
                    shutil.copy2(str(subdir) + '\\en\\' + subtitles, str(media_path).replace(media_path.name, clean_title(media_path.name) + ' (' + year + ').srt'))
                except FileNotFoundError:
                    continue

    return ' (' + year + ')', str(media_path).replace(media_path.name, clean_title(media_path.name) + ' (' + year + ').srt')


def get_media_details(media_id, media_list, is_tv=False):
    """ Returns various information on the media file. """
    for m in media_list:
        if media_id in str(m[0]):
            if is_tv:
                # m[10] = season number, m[11] = episode number, m[13] = episode title
                if m[10] is None or m[11] is None or m[13] is None: continue

                return m[10], m[11], m[13]
            else:
                # m[1] = url containing the year of the media, m[18] = prioritized subtitle file
                if m[1] is None or m[18] is None: continue

                try:
                    return str(m[1]).split('/movie.' + media_id + '.')[1][:4], m[18]
                except IndexError:
                    print('Potential error with media id: ' + media_id + '. Recommended to check year and subtitle file.')
                    continue


def read_download_db(database):
    """ Reads MovieBoxPro Download.db file """
    db_con = sqlite3.connect(database)
    cursor = db_con.cursor()
    media_list = [m for m in cursor.execute('SELECT * FROM Download')]
    db_con.close()

    return media_list


if not movieboxpro.exists(): exit('MovieBoxPro directory does not exist or has not been found!')
if not Path(download_database).exists(): exit('Download.db file does not exist or has not been found!')
# the mistake I just made that warranted these checks to avoid future problems (and tedious work)..
if not subtitle_cache.exists():
    if input('Subtitles directory does not exist or has not be found continue? (y or any): ') != 'y':
        exit('Subtitle directory not found, exiting.')

for main in movieboxpro.glob('*'):
    if main.is_dir() and '_' in main.name:
        pass
    elif main.is_file() and '_' in main.name and '.mp4' in main.name:
        try:
            media_id = re.search(r'_(\d+)_\d+p', main.name).group(1)
            year, tpath = get_subtitles(main, media_id)
            print('Converting: ' + main.name, media_id, year.replace('(','').replace(')',''))
            if Path(tpath).is_file(): subs += 1
            main.rename(str(main).replace(main.name, clean_title(main.name) + year + '.mp4'))
            movies += 1
        except FileExistsError:
            continue


print('\nMovies Converted: ' + str(movies))
print('Subtitles Found & Converted: ' + str(subs))
if index_errors > 0:
    print('Noted ' + str(index_errors) + ' indexing errors, please check that the media and subtitle files are working.')
if fileerrors > 0:
    print('Noted ' + str(fileerrors) + ' file errors, please check that the media and subtitle files are working.')
    print('If you also received indexing errors and the values are equal, these can likely be ignored.')
