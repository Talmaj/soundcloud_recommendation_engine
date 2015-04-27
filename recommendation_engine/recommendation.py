__author__ = 'Talmaj'
import pandas as pd

class engine(object):
    def __init__(self, client):
        self.client = client
        self.followings = self.get_followings()
        self.followings_ids = self.get_ids_from_obj(self.followings)
        self.known_tracks = self.get_known_tracks()

    def track_info(self, track):
        '''
        Selects only important information from a track.

        :param track: dict track
        :return dic: dict wanted values
        '''
        dic = {}
        for key in ['id', 'comment_count', 'favoritings_count', 'playback_count', 'user_id', 'created_at', 'duration']:
            try:
                dic[key] = track[key]
            except KeyError:
                if 'count' in key:
                    dic[key] = 0
                else:
                    raise ValueError
        return dic

    def user_info(self, user):
        '''
        Selects only important information from a user.

        :param user: dict user
        :return dic: dict wanted values
        '''
        dic = {}
        for key in ['city', 'country', 'followers_count', 'followings_count', 'id']:
            try:
                dic[key] = user[key]
            except KeyError:
                if 'count' in key:
                    dic[key] = 0
                else:
                    raise ValueError
        return dic

    def get_followings(self, id='me'):
        '''
        Returns a list of followings users on SC.
        '''
        id = '/users/%d'%id if id != 'me' else '/me'
        followings = []
        for following in self.client.get('%s/followings'%id):
            followings.append(self.user_info(following.obj))
        return followings

    def get_ids_from_obj(self, objects):
        '''
        Used to extract ids from tracks or users
        :param objects: dictionary
        :return: list of ids
        '''
        ids = [obj['id'] for obj in objects]
        return ids

    def extract_repeated_values(self, li, min_repetitions=2): # TODO do only in python, without pandas
        '''
        Extracts the values that are repeated a least min_repetitions times
        :param li: list of values
        :param min_repetitions: minimum repetitions for values
        :return: list of repeated values
        '''
        li = pd.Series(list(li))
        li_count = li.value_counts()
        repeated_values = li_count[(li_count >= min_repetitions)].index.tolist()
        return repeated_values

    def get_known_tracks(self):
        pass


class from_playlists(engine):
    '''
    Class for identifiying potential artists to follow and music to listen to from created playlists
    '''
    def __init__(self, client):
        engine.__init__(self, client)
        self.music = self.get_music()
        self.artists = self.get_artists(self.music)
        self.favorite_artists = self.get_favorite_artists(self.artists)
        self.recommended_artists = self.get_recommended_artists(self.favorite_artists)

    def get_music(self):
        music = []
        for playlist in self.client.get('/me/playlists'):
            for track in playlist.tracks: # TODO add weighting to newer playlists
                music.append(self.track_info(track))
        return music

    def get_artists(self, music):
        artists = [track['user_id'] for track in music]
        return artists

    def get_favorite_artists(self, artists): # TODO avoid usage of pandas
        favorite_artists = self.extract_repeated_values(artists, 2)
        return favorite_artists

    def get_recommended_artists(self, favorite_artists):
        recommended_artists = list(set(favorite_artists) - set(self.followings_ids))
        return recommended_artists

class from_followings(engine):
    '''
    Class for identifiying potential artists to follow and music to listen to from followings
    '''
    def __init__(self, client):
        engine.__init__(self, client)
        self.foll_from_followings = self.get_foll_from_followings(self.followings)
        self.foll_from_followings_users = self.get_foll_from_followings_users(self.foll_from_followings)
        self.suggested_artists = self.get_suggested_artists()

    def get_foll_from_followings(self, followings):
        foll_from_followings = [self.get_followings(following['id']) for following in followings]
        return foll_from_followings

    def get_foll_from_followings_users(self, foll_from_followings):
        '''
        all users that the people I follow, follow
        '''
        foll_from_followings_users = []
        for following in foll_from_followings:
            foll_from_followings_users.extend(self.get_ids_from_obj(following))
        return foll_from_followings_users

    def get_suggested_artists(self):
        return list(set(self.extract_repeated_values(self.foll_from_followings_users, 2)) - set(self.followings_ids))

class from_favorites(engine):
    pass



def track_quality(track):
    '''
    quality_1: favoritings_count/playback_count
    quality_2: comment_count/duration

    :param track: dict (information of a track)
    :return: dict with two new quality values
    '''
    try:
        track['quality_1'] =  round(track['favoritings_count'] / float(track['playback_count']), 4)
    except ZeroDivisionError:
        track['quality_1'] = 0.0

    track['quality_2'] =  round(track['comment_count'] / float(track['duration'] / 60000.0), 4) # duration in milliseconds, now converted to minutes
    return track

def get_recommended_tracks(user_ids, n=None, criteria='quality_2'):
    '''
    Selects recommended tracks

    :param user_ids: list of user ids to select the tracks from
    :param n: number of tracks to select from each user
    :param criteria: on which criteria to sort on (info in track quality function)
    :return: list of recommended tracks
    '''
    recommended_tracks = {}
    for artist in user_ids:
        #followers_count = client.get('/users/%d'%artist).obj['followers_count'] # TODO fetch from database

        tracks = []
        for track in client.get('/users/%d/tracks'%artist):
            track = track_info(track.obj)
            track = track_quality(track)
            tracks.append(track)

        tracks = sorted(tracks, key=lambda track: track[criteria], reverse=True)

        if len(tracks): #avoid adding empty lists of tracks
            recommended_tracks[artist] = tracks[:n]

    return recommended_tracks








