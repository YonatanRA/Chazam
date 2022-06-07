<< << << < HEAD
== == == =
<< << << < HEAD
>> >> >> > n
from itertools import groupby
from time import time
from typing import Dict, List, Tuple

import chazam.logic.decoder as decoder
from chazam.base_classes.base_database import get_database
from chazam.config.settings import (DEFAULT_FS, DEFAULT_OVERLAP_RATIO,
                                    DEFAULT_WINDOW_SIZE, FIELD_FILE_SHA1,
                                    FIELD_TOTAL_HASHES,
                                    FINGERPRINTED_CONFIDENCE,
                                    FINGERPRINTED_HASHES, HASHES_MATCHED,
                                    INPUT_CONFIDENCE, INPUT_HASHES, OFFSET,
                                    OFFSET_SECS, SONG_ID, SONG_NAME, TOPN,
                                    SQL_CONFIG)
from chazam.logic.file_recognizer import FileRecognizer
from chazam.logic.fingerprint import fingerprint


class Chazam:

    def __init__(self, config: dict = SQL_CONFIG):

        self.config = config

        # inicializar base de datos
        db_cls = get_database(config.get('database_type', 'mysql').lower())
        self.db = db_cls(**config.get('database', {}))
        self.db.setup()

        # si queremos limitar el tiempo de fingerprint en segundos, None o -1 significan la cancion entera
        self.limit = self.config.get('fingerprint_limit', None)

        if self.limit == -1:  # para compatibilidad JSON
            self.limit = None

        self.__load_fingerprinted_audio_hashes()

    def __load_fingerprinted_audio_hashes(self) -> None:
        """
        Conjunto con los hashes de los fingerprints, para saber si una cancion ha sido procesada.
        """

        # obtener canciones ya indexadas
        self.songs = self.db.get_songs()

        self.songhashes_set = set()  # valores unicos para saber cuales ha sido ya fingerprinteadas

        for song in self.songs:
            song_hash = song[FIELD_FILE_SHA1]
            self.songhashes_set.add(song_hash)

    def get_fingerprinted_songs(self) -> List[Dict[str, any]]:
        """
        Extrae todas las canciones fingerprinteadas de la base de datos.

        :return: una lista de canciones procesadas de la base de datos.
        """
        return self.db.get_songs()

    def delete_songs_by_id(self, song_ids: List[int]) -> None:
        """
        Borra las canciones por su id.

        :param song_ids: ids de canciones para borrar de la base de datos.
        """
        self.db.delete_songs_by_id(song_ids)

    def fingerprint_directory(self, path: str, ext: List[str], n_jobs: int = None) -> None:
        """
        Realiza el fingerprint de todas las canciones en una carpeta dada las extensiones (wav, mp3...)

        :param path: ruta al directorio.
        :param ext: lista de extensiones a procesar.
        :param n_jobs: cantidad de cores a usar (multiprocessing), usa el máximo si no se asigna valor.
        """
        try:
            n_jobs = n_jobs or multiprocessing.cpu_count()
        except NotImplementedError:
            n_jobs = 1
        else:
            n_jobs = 1 if n_jobs <= 0 else n_jobs

        pool = multiprocessing.Pool(n_jobs)

        files_to_fingerprint = []
        for file, _ in decoder.find_files(path, ext):
            # no proceses los que ya estan
            if decoder.unique_hash(file) in self.songhashes_set:
                print(f'{file} already fingerprinted, continuing...')
                continue

            files_to_fingerprint.append(file)

        # Preparar entrada para _fingerprint_helper
        worker_input = list(zip(files_to_fingerprint, [self.limit] * len(files_to_fingerprint)))
        iterator = pool.imap_unordered(Chazam._fingerprint_helper, worker_input)

        # bucle hasta tenerlos todos
        while True:
            try:
                song_name, hashes, file_hash = next(iterator)
            except multiprocessing.TimeoutError:
                continue
            except StopIteration:
                break
            except Exception:
                print('Failed fingerprinting')
                traceback.print_exc(file=sys.stdout)
            else:
                sid = self.db.insert_song(song_name, file_hash, len(hashes))

                self.db.insert_hashes(sid, hashes)
                self.db.set_song_fingerprinted(sid)
                self.__load_fingerprinted_audio_hashes()

        pool.close()
        pool.join()

    def fingerprint_file(self, file_path: str, song_name: str = None) -> None:
        """
        Realiza el fingerprint de un archivo.

        :param file_path: ruta al archivo.
        :param song_name: nombre de la cancion.
        """
        song_name_from_path = decoder.get_audio_name_from_path(file_path)
        song_hash = decoder.unique_hash(file_path)
        song_name = song_name or song_name_from_path

        # no proceses los que ya estan
        if song_hash in self.songhashes_set:
            print(f'{song_name} already fingerprinted, continuing...')
        else:
            song_name, hashes, file_hash = Chazam._fingerprint_helper(file_path)
            sid = self.db.insert_song(song_name, file_hash)

            self.db.insert_hashes(sid, hashes)
            self.db.set_song_fingerprinted(sid)
            self.__load_fingerprinted_audio_hashes()

    def generate_fingerprints(self, samples: List[int], Fs=DEFAULT_FS) -> Tuple[List[Tuple[str, int]], float]:
        f"""

        Genera los fingerprints para cada muestra de audio.

        :param samples: lista de enteros que representan cada canal del audio.
        :param Fs: frecuencia de muestreo, por defecto {DEFAULT_FS}.
        :return: a list of tuples for hash and its corresponding offset, together with the generation time.
        """
        t = time()

        hashes = fingerprint(samples, Fs=Fs)

        fingerprint_time = time() - t

        return hashes, fingerprint_time

    def find_matches(self, hashes: List[Tuple[str, int]]) -> Tuple[List[Tuple[int, int]], Dict[str, int], float]:
        """
        Finds the corresponding matches on the fingerprinted audios for the given hashes.

        :param hashes: list of tuples for hashes and their corresponding offsets
        :return: a tuple containing the matches found against the db, a dictionary which counts the different
         hashes matched for each song (with the song id as key), and the time that the query took.

        """
        t = time()

        matches, dedup_hashes = self.db.return_matches(hashes)

        query_time = time() - t

        return matches, dedup_hashes, query_time

    def align_matches(self, matches: List[Tuple[int, int]], dedup_hashes: Dict[str, int], queried_hashes: int,
                      topn: int = TOPN) -> List[Dict[str, any]]:
        """
        Finds hash matches that align in time with other matches and finds
        consensus about which hashes are "true" signal from the audio.

        :param matches: matches from the database
        :param dedup_hashes: dictionary containing the hashes matched without duplicates for each song
        (key is the song id).
        :param queried_hashes: amount of hashes sent for matching against the db
        :param topn: number of results being returned back.
        :return: a list of dictionaries (based on topn) with match information.
        """

        # count offset occurrences per song and keep only the maximum ones.
        sorted_matches = sorted(matches, key=lambda m: (m[0], m[1]))
        counts = [(*key, len(list(group))) for key, group in groupby(sorted_matches, key=lambda m: (m[0], m[1]))]
        songs_matches = sorted(
            [max(list(group), key=lambda g: g[2]) for key, group in groupby(counts, key=lambda count: count[0])],
            key=lambda count: count[2], reverse=True
        )

        songs_result = []
        for song_id, offset, _ in songs_matches[0:topn]:  # consider topn elements in the result
            song = self.db.get_song_by_id(song_id)

            song_name = song.get(SONG_NAME, None)
            song_hashes = song.get(FIELD_TOTAL_HASHES, None)
            nseconds = round(float(offset) / DEFAULT_FS * DEFAULT_WINDOW_SIZE * DEFAULT_OVERLAP_RATIO, 5)
            hashes_matched = dedup_hashes[song_id]

            song = {
                SONG_ID: song_id,
                SONG_NAME: song_name.encode("utf8"),
                INPUT_HASHES: queried_hashes,
                FINGERPRINTED_HASHES: song_hashes,
                HASHES_MATCHED: hashes_matched,
                # Percentage regarding hashes matched vs hashes from the input.
                INPUT_CONFIDENCE: round(hashes_matched / queried_hashes, 2),
                # Percentage regarding hashes matched vs hashes fingerprinted in the db.
                FINGERPRINTED_CONFIDENCE: round(hashes_matched / song_hashes, 2),
                OFFSET: offset,
                OFFSET_SECS: nseconds,
                FIELD_FILE_SHA1: song.get(FIELD_FILE_SHA1, None).encode('utf8')
            }

            songs_result.append(song)

        return songs_result

    def recognize(self, *options, **kwoptions) -> Dict[str, any]:
        r = FileRecognizer(self)
        return r.recognize(*options, **kwoptions)

    @staticmethod
    def _fingerprint_helper(arguments):
        # Pool.imap sends arguments as tuples so we have to unpack them ourself.
        try:
            file_name, limit = arguments
        except ValueError:
            pass

        song_name, extension = os.path.splitext(os.path.basename(file_name))

        fingerprints, file_hash = Chazam.get_file_fingerprints(file_name, limit, print_output=True)

        return song_name, fingerprints, file_hash

    @staticmethod
    def get_file_fingerprints(file_name: str, limit: int, print_output: bool = False):
        channels, fs, file_hash = decoder.read(file_name, limit)
        fingerprints = set()
        channel_amount = len(channels)
        for channeln, channel in enumerate(channels, start=1):
            if print_output:
                print(f'Fingerprinting channel {channeln}/{channel_amount} for {file_name}')

            hashes = fingerprint(channel, Fs=fs)

            if print_output:
                print(f'Finished channel {channeln}/{channel_amount} for {file_name}')

            fingerprints |= set(hashes)

        return fingerprints, file_hash

<< << << < HEAD
== == == =
== == == =
from chazam.database import get_database, Database
import chazam.decoder as decoder
import chazam.fingerprint as fingerprint
from chazam.recognize import FileRecognizer
import multiprocessing
import os
import traceback
import sys


class Chazam():
    SONG_ID = "song_id"
    SONG_NAME = 'song_name'
    CONFIDENCE = 'confidence'
    MATCH_TIME = 'match_time'
    OFFSET = 'offset'
    OFFSET_SECS = 'offset_seconds'

    def __init__(self, config):
        super(Chazam, self).__init__()

        self.config = config

        # initialize db
        db_cls = get_database(config.get("database_type", None))

        self.db = db_cls(**config.get("database", {}))
        self.db.setup()

        # if we should limit seconds fingerprinted,
        # None|-1 means use entire track
        self.limit = self.config.get("fingerprint_limit", None)
        if self.limit == -1:  # for JSON compatibility
            self.limit = None
        self.get_fingerprinted_songs()

    def get_fingerprinted_songs(self):
        # get songs previously indexed
        self.songs = self.db.get_songs()
        self.songhashes_set = set()  # to know which ones we've computed before

        for song in self.songs:
            # print('song', song)
            song_hash = song[Database.FIELD_FILE_SHA1]
            self.songhashes_set.add(song_hash)

    def fingerprint_directory(self, path, extensions, nprocesses=None):
        # Try to use the maximum amount of processes if not given.
        try:
            nprocesses = nprocesses or multiprocessing.cpu_count()
        except NotImplementedError:
            nprocesses = 1
        else:
            nprocesses = 1 if nprocesses <= 0 else nprocesses

        pool = multiprocessing.Pool(nprocesses)

        filenames_to_fingerprint = []
        for filename, _ in decoder.find_files(path, extensions):

            # don't refingerprint already fingerprinted files
            if decoder.unique_hash(filename) in self.songhashes_set:
                print("%s already fingerprinted, continuing..." % filename)
                continue

            filenames_to_fingerprint.append(filename)

        # Prepare _fingerprint_worker input
        worker_input = zip(filenames_to_fingerprint,
                           [self.limit] * len(filenames_to_fingerprint))

        # Send off our tasks
        iterator = pool.imap_unordered(_fingerprint_worker,
                                       worker_input)

        # Loop till we have all of them
        while True:
            try:
                song_name, hashes, file_hash = iterator.next()
            # print('hashes', hashes)
            except multiprocessing.TimeoutError:
                continue
            except StopIteration:
                break
            except:
                print("Failed fingerprinting")
                # Print traceback because we can't reraise it here
                traceback.print_exc(file=sys.stdout)
            else:
                sid = self.db.insert_song(song_name, file_hash)

                self.db.insert_hashes(sid, hashes)
                self.db.set_song_fingerprinted(sid)
                self.get_fingerprinted_songs()

        pool.close()
        pool.join()

    def fingerprint_file(self, filepath, song_name=None):
        songname = decoder.path_to_songname(filepath)
        song_hash = decoder.unique_hash(filepath)
        song_name = song_name or songname
        # don't refingerprint already fingerprinted files
        if song_hash in self.songhashes_set:
            print("%s already fingerprinted, continuing..." % song_name)
        else:
            song_name, hashes, file_hash = _fingerprint_worker(
                filepath,
                self.limit,
                song_name=song_name
            )
            sid = self.db.insert_song(song_name, file_hash)

            self.db.insert_hashes(sid, hashes)
            self.db.set_song_fingerprinted(sid)
            self.get_fingerprinted_songs()

    def find_matches(self, samples, Fs=fingerprint.DEFAULT_FS):
        hashes = fingerprint.fingerprint(samples, Fs=Fs)
        return self.db.return_matches(hashes)

    def align_matches(self, matches):
        """
            Finds hash matches that align in time with other matches and finds
            consensus about which hashes are "true" signal from the audio.

            Returns a dictionary with match information.
        """
        # align by diffs
        diff_counter = {}
        largest = 0
        largest_count = 0
        song_id = -1
        for tup in matches:
            sid, diff = tup
            if diff not in diff_counter:
                diff_counter[diff] = {}
            if sid not in diff_counter[diff]:
                diff_counter[diff][sid] = 0
            diff_counter[diff][sid] += 1

            if diff_counter[diff][sid] > largest_count:
                largest = diff
                largest_count = diff_counter[diff][sid]
                song_id = sid

        # extract idenfication
        song = self.db.get_song_by_id(song_id)
        if song:
            # TODO: Clarify what `get_song_by_id` should return.
            songname = song.get(Chazam.SONG_NAME, None)
        else:
            return None

        # return match info
        nseconds = round(float(largest) / fingerprint.DEFAULT_FS *
                         fingerprint.DEFAULT_WINDOW_SIZE *
                         fingerprint.DEFAULT_OVERLAP_RATIO, 5)
        song = {
            Chazam.SONG_ID: song_id,
            Chazam.SONG_NAME: songname,
            Chazam.CONFIDENCE: largest_count,
            Chazam.OFFSET: int(largest),
            Chazam.OFFSET_SECS: nseconds,
            Database.FIELD_FILE_SHA1: song.get(Database.FIELD_FILE_SHA1, None), }

        return song

    def recognize(self, *options, **kwoptions):
        r = FileRecognizer(self)
        return r.recognize(*options, **kwoptions)


def _fingerprint_worker(filename, limit=None, song_name=None):
    # Pool.imap sends arguments as tuples so we have to unpack
    # them ourself.
    try:
        filename, limit = filename
    except ValueError:
        pass

    songname, extension = os.path.splitext(os.path.basename(filename))
    song_name = song_name or songname
    channels, Fs, file_hash = decoder.read(filename, limit)
    result = set()
    channel_amount = len(channels)

    for channeln, channel in enumerate(channels):
        # TODO: Remove prints or change them into optional logging.
        print("Fingerprinting channel %d/%d for %s" % (channeln + 1,
                                                       channel_amount,
                                                       filename))
        hashes = fingerprint.fingerprint(channel, Fs=Fs)
        print("Finished channel %d/%d for %s" % (channeln + 1, channel_amount,
                                                 filename))
        result |= set(hashes)

    return song_name, result, file_hash


def chunkify(lst, n):
    """
    Splits a list into roughly n equal parts.
    http://stackoverflow.com/questions/2130016/splitting-a-list-of-arbitrary-size-into-only-roughly-n-equal-parts
    """
    return [lst[i::n] for i in xrange(n)]

>> >> >> > b1c312b(libreria
chazam)
>> >> >> > n
