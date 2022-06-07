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

    @staticmethod
    def generate_fingerprints(samples: List[int], Fs=DEFAULT_FS) -> Tuple[List[Tuple[str, int]], float]:
        f"""

        Genera los fingerprints para cada muestra de audio.

        :param samples: lista de enteros que representan cada canal del audio.
        :param Fs: frecuencia de muestreo, por defecto {DEFAULT_FS}.
        :return: lista de tuplas de hash y el correspondiente offset (tiempo), junto con el tiempo de generación.
        """
        t = time()

        hashes = fingerprint(samples, Fs=Fs)

        fingerprint_time = time() - t

        return hashes, fingerprint_time

    def find_matches(self, hashes: List[Tuple[str, int]]) -> Tuple[List[Tuple[int, int]], Dict[str, int], float]:
        """
        Encuentra las correspondencias de audio dados los fingerprints.

        :param hashes: lista de tuplas de hashes y sus offsets.
        :return: una tupla con las correspondencias, un diccionario con key=song_id y value=cuentas de los diferentes hashes para cada canción
        y el tiempo de consulta a la base de datos.

        """
        t = time()

        matches, d_hashes = self.db.return_matches(hashes)  # d_hashes=deduplicate hashes

        query_time = time() - t

        return matches, d_hashes, query_time

    def align_matches(self, matches: List[Tuple[int, int]], d_hashes: Dict[str, int], queried_hashes: int,
                      topn: int = TOPN) -> List[Dict[str, any]]:
        """
        Encuentra las correspondencias de hashes que se alinean temporalmente con otras
        correspondencias y saca un consenso sobre que hashes representan verdaderamente la señal de audio.

        :param matches: correspondencias desde la base de datos
        :param d_hashes: diccionario que contiene las correspondencias en hashes para cada canción (key=song_id).
        :param queried_hashes: cantidad de hashes enviados contra la base de datos.
        :param topn: número de resultados que vuelven de la base de datos (por defecto 1).
        :return: una lista de diccionarios con la información de correspondencias.
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
            hashes_matched = d_hashes[song_id]

            song = {
                SONG_ID: song_id,
                SONG_NAME: song_name.encode('utf8'),
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
