from __future__ import absolute_import, division, print_function

import sqlite3
import logging
import os
import simplejson
import configparser
import shutil
import json

from datetime import datetime
from sqlite3 import Error
from trakt import Trakt
from urllib.request import Request, urlopen

# Variables
directory_database = os.path.join(os.path.dirname(__file__), 'db')
directory_data = os.path.join(os.path.dirname(__file__), 'frontend/data')
plex_database_destination = os.path.join(directory_database, 'com.plexapp.plugins.library.db')
config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
output_file = os.path.join(os.path.dirname(__file__), 'frontend/data/shows.json')

logging.basicConfig(level=logging.DEBUG)


def plex_create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


def plex_select_all_tv(conn):
    cur = conn.cursor()
    query = '''SELECT show.title as Show, season.[index] as Season, episode.[index] as Episode, episode.title as Title, librairie.name, media.duration/60000 AS duration, media.width, media.height, printf("%.4f",media.frames_per_second) AS framerate, media.bitrate/1024 AS birate, media.video_codec, media.size/1048576 AS SIZE, show.year FROM metadata_items episode JOIN metadata_items season ON season.id = episode.parent_id JOIN metadata_items show ON show.id = season.parent_id JOIN media_items media ON media.metadata_item_id = episode.id JOIN library_sections librairie ON librairie.id = episode.library_section_id WHERE episode.metadata_type = 4 ORDER BY show.title, season.[index], episode.[index]'''
    cur.execute(query)

    rows = cur.fetchall()
    shows = set()
    for row in rows:
        shows.add(row[0])

    items = []
    for show in shows:
        tv_show = {}
        tv_show['name'] = show
        tv_show['items'] = []
        items.append(
            tv_show
        )
    for row in rows:
        for item in items:
            if row[0] == item['name']:
                item['items'].append(row)

    for show in items:
        show['set_seasons'] = set()
        for episode in show['items']:
            show['set_seasons'].add(episode[1])

    for show in items:
        show['seasons'] = []
        for item in show['set_seasons']:
            season = {}
            season['number'] = item
            show['seasons'].append(season)

    for show in items:
        for season in show['seasons']:
            season['episodes'] = []
            for episode in show['items']:
                if season['number'] == episode[1]:
                    episode_tmp = {}
                    episode_tmp['episode'] = episode[2]
                    episode_tmp['name'] = episode[3]
                    show['year'] = episode[12]

                    season['episodes'].append(episode_tmp)

        del show['items']
        del show['set_seasons']

    return items


def get_translated_title(query, item, client_id, language):
    for show_key, show_value in item.keys:
        if show_key == 'slug':
            headers = {
                'Content-Type': 'application/json',
                'trakt-api-version': '2',
                'trakt-api-key': client_id
            }
            request = Request('https://api.trakt.tv/shows/' + show_value + '/translations/' + language, headers=headers)

            response_body = urlopen(request).read()
            j = json.loads(response_body.decode("utf-8"))
            if len(j) > 0:
                if j[0]['title'] in query:
                    return item


def find_trakt_show(query, media=None, year=None, client_id=None, language='en'):
    items = Trakt['search'].query(query, media, year, extended='full')

    tv_show = {}
    try:
        if items[0].score < 1000:
            for item in items:
                match = get_translated_title(query, item, client_id, language)
                if match != None:
                    items[0] = match

        for show_key, show_value in items[0].keys:

            if show_key == 'trakt':
                tv_show['plex_title'] = query
                tv_show['title'] = items[0].title
                tv_show['href'] = items[0].title.replace(' ', '').replace("'", '').replace(":", '').replace("-",
                                                                                                            '').replace(".",
                                                                                                                        '').replace(
                    ":", '')
                tv_show['year'] = items[0].year
                tv_show['seasons'] = []

                seasons = Trakt['shows'].seasons(show_value, extended='full')

                if "Season S00" in str(seasons):
                    count_seasons = len(seasons) - 1
                else:
                    count_seasons = len(seasons)

                season = 1
                while season <= count_seasons:
                    show_season = {}
                    details_season = Trakt['shows'].season(show_value, season, extended='full')
                    show_season['number'] = season
                    count_episodes = len(details_season)
                    show_season['episodes'] = []

                    episode = 0
                    while episode < count_episodes:
                        season_episode = {}
                        season_episode['number'] = details_season[episode].keys[0][1]
                        season_episode['title'] = details_season[episode].title
                        if details_season[episode].first_aired != None:
                            timestamp = datetime.strptime(str(details_season[episode].first_aired).split(' ')[0],
                                                          '%Y-%m-%d')
                            details_season[episode].first_aired = timestamp.strftime('%B %d, %Y')
                            season_episode['aired_timestamp'] = timestamp.timestamp()

                            if timestamp.timestamp() > datetime.now().timestamp():
                                season_episode['aired'] = False
                            else:
                                season_episode['aired'] = True

                        else:
                            season_episode['aired'] = False

                        season_episode['first_aired'] = details_season[episode].first_aired
                        season_episode['owning'] = False
                        show_season['episodes'].append(season_episode)
                        episode += 1

                    tv_show['seasons'].append(show_season)
                    season += 1

        return tv_show

    except:
        pass


def compare_plex_trakt(plex, trakt):
    for show_plex in plex:
        for show_trakt in trakt:
            if show_plex['name'] == show_trakt['plex_title']:

                for season_plex in show_plex['seasons']:
                    for season_trakt in show_trakt['seasons']:
                        if season_plex['number'] == season_trakt['number']:

                            for episode_plex in season_plex['episodes']:
                                for episode_trakt in season_trakt['episodes']:
                                    if episode_plex['episode'] == episode_trakt['number']:
                                        episode_trakt['owning'] = True
                                        episode_trakt['plex_title'] = episode_plex['name']

    return trakt


def calculate_owning(data):
    for show in data:
        show_owning_true = 0
        show_owning_false = 0

        try:
            for season in show['seasons']:
                season_owning_true = 0
                season_owning_false = 0

                try:
                    for episode in season['episodes']:
                        if episode['aired'] == True:
                            if episode['owning'] == True:
                                season_owning_true += 1
                                show_owning_true += 1
                            else:
                                season_owning_false += 1
                                show_owning_false += 1

                    if (season_owning_true + season_owning_false) == 0:
                        season['aired'] = False
                    else:
                        season['aired'] = True
                        season_owning_percent = (100 / (season_owning_true + season_owning_false)) * season_owning_true
                        season['owning_percent'] = season_owning_percent
                        season['owning_episodes_true'] = season_owning_true
                        season['owning_episodes_false'] = season_owning_false
                except:
                    pass
        except:
            pass

        show['owning_percent'] = (100 / (show_owning_true + show_owning_false)) * show_owning_true
        show['owning_episodes_true'] = show_owning_true
        show['owning_episodes_false'] = show_owning_false

    return data


def prepare_file_system(plex_database_origin):
    if not os.path.exists(directory_database):
        os.makedirs(directory_database)

    if not os.path.exists(directory_data):
        os.makedirs(directory_data)

    try:
        shutil.copy2(plex_database_origin, plex_database_destination)
    except:
        print('Copy of plex database failed! Exit.')
        exit(1)


if __name__ == '__main__':

    # Read config
    config = configparser.ConfigParser()
    config.read(config_file)

    # Prepare
    prepare_file_system(config['Plex']['database_location'])

    # Configure
    Trakt.configuration.defaults.client(
        id=config['trakt.tv']['client_id'],
        secret=config['trakt.tv']['client_secret']
    )

    # create a database connection
    conn = plex_create_connection(plex_database_destination)
    plex_shows = plex_select_all_tv(conn)

    trakt_shows = []
    for show in plex_shows:
        print(config['Plex']['library_language'])
        trakt_show = find_trakt_show(show['name'], 'show', show['year'], config['trakt.tv']['client_id'],
                                     config['Plex']['library_language'])
        trakt_shows.append(trakt_show)

    data = compare_plex_trakt(plex_shows, trakt_shows)

    result = calculate_owning(data)

    data_file = open(output_file, "w")
    data_file.write(simplejson.dumps(result, indent=4, sort_keys=True, default=str))
    data_file.close()
