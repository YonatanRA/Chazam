import abc
from typing import Dict, List, Tuple

from chazam.base_classes.base_database import BaseDatabase


class CommonDatabase(BaseDatabase, metaclass=abc.ABCMeta):
    # Reutilización para diferentes bases de datos

    def __init__(self):
        super().__init__()

    def before_fork(self) -> None:
        """
        LLamada antes de nuevo proceso de la instancia de la base de datos.
        """
        pass

    def after_fork(self) -> None:
        """
        LLamada después de nuevo proceso de la instancia de la base de datos.
        Será llamada en el nuevo proceso.
        """
        pass

    def setup(self) -> None:
        """
        Llamada en la creación de tablas.
        """
        with self.cursor() as cur:
            cur.execute(self.CREATE_SONGS_TABLE)
            cur.execute(self.CREATE_FINGERPRINTS_TABLE)
            cur.execute(self.DELETE_UNFINGERPRINTED)

    def empty(self) -> None:
        """
        Llamada cuando la base de datos está vacía.
        """
        with self.cursor() as cur:
            cur.execute(self.DROP_FINGERPRINTS)
            cur.execute(self.DROP_SONGS)

        self.setup()

    def delete_unfingerprinted_songs(self) -> None:
        """
        Llamada para borrar canciones no procesadas.
        """
        with self.cursor() as cur:
            cur.execute(self.DELETE_UNFINGERPRINTED)

    def get_num_songs(self) -> int:
        """
        Cuenta el número de canciones.

        :return: número de canciones en la base de datos.
        """
        with self.cursor(buffered=True) as cur:
            cur.execute(self.SELECT_UNIQUE_SONG_IDS)
            count = cur.fetchone()[0] if cur.rowcount != 0 else 0

        return count

    def get_num_fingerprints(self) -> int:
        """
        Cuenta el número de fingerprints.

        :return: número de fingerprints en la base de datos.
        """
        with self.cursor(buffered=True) as cur:
            cur.execute(self.SELECT_NUM_FINGERPRINTS)
            count = cur.fetchone()[0] if cur.rowcount != 0 else 0

        return count

    def set_song_fingerprinted(self, song_id):
        """
        Establece si una canción ha sido procesada..

        :param song_id: id de la canción.
        """
        with self.cursor() as cur:
            cur.execute(self.UPDATE_SONG_FINGERPRINTED, (song_id,))

    def get_songs(self) -> List[Dict[str, str]]:
        """
        Devuelve todas las canciones procesadas de la base de datos.

        :return: un diccionario con toda la info de las canciones.
        """
        with self.cursor(dictionary=True) as cur:
            cur.execute(self.SELECT_SONGS)
            return list(cur)

    def get_song_by_id(self, song_id: int) -> Dict[str, str]:
        """
        Info de la canción.
        :param song_id: id de la canción.

        :return: un diccionario con la info de la cancione.
        """
        with self.cursor(dictionary=True) as cur:
            cur.execute(self.SELECT_SONG, (song_id,))
            return cur.fetchone()

    def insert(self, fingerprint: str, song_id: int, offset: int):
        """
        Inserta un solo fingerprint en la base de datos.
        :param fingerprint: parte del hash sha1, hexadecimal
        :param song_id: id de la canción.
        :param offset: punto temporal de donde viene el fingerprint.
        """
        with self.cursor() as cur:
            cur.execute(self.INSERT_FINGERPRINT, (fingerprint, song_id, offset))

    @abc.abstractmethod
    def insert_song(self, song_name: str, file_hash: str, total_hashes: int) -> int:
        """
        Inserta una canción en la base de datos, devuelve el id de la canción insertada.

        :param song_name: nombre de la canción.
        :param file_hash: hash del archivo fingerprinteado.
        :param total_hashes: número total de hashes insertados.

        :return: id de la canción.
        """
        pass

    def query(self, fingerprint: str = None) -> List[Tuple]:
        """
        Devuelve todas las coincidencias de fingerprints asociados con el hash.
        Si se pasa None devuelve todas las entradas de la base de datos.

        :param fingerprint: parte del hash sha1, en hexadecimal

        :return: una lista de los fingerprints en la base de datos.
        """
        with self.cursor() as cur:
            if fingerprint:
                cur.execute(self.SELECT, (fingerprint,))
            else:  # selecciona todos si es None
                cur.execute(self.SELECT_ALL)
            return list(cur)

    def get_iterable_kv_pairs(self) -> List[Tuple]:
        """
        Devuelve todos los fingerprints en la base de datos.

        :return: una lista de todos los fingerprints guardados en la base de datos.
        """
        return self.query(None)

    def insert_hashes(self, song_id: int, hashes: List[Tuple[str, int]], batch_size: int = 1000) -> None:
        """
        Inserción multiple de fingerprints.

        :param song_id: id de la canción
        :param hashes: lista de tuplas con formato (hash, offset)
            - hash: parte del hash sha1, en hexadecimal
            - offset: tiempo donde el hash empieza.
        :param batch_size: tamaño de los batches.
        """
        values = [(song_id, hsh, int(offset)) for hsh, offset in hashes]

        with self.cursor() as cur:
            for index in range(0, len(hashes), batch_size):
                cur.executemany(self.INSERT_FINGERPRINT, values[index: index + batch_size])

    def return_matches(self, hashes: List[Tuple[str, int]],
                       batch_size: int = 1000) -> Tuple[List[Tuple[int, int]], Dict[int, int]]:
        """
        Busca en la base de datos las parejas de valores (hash, offset).

        :param hashes: lista de tuplas con formato (hash, offset)
            - hash: parte del hash sha1, en hexadecimal
            - offset: tiempo donde el hash empieza.
        :param batch_size: tamaño de los batches.

        :return: una lista de tuplas (sid, offset_difference) y un
        diccionario con la cantidad de hashes que coinciden de cada canción
        sin considerar duplicados.
            - song id: id de la canción
            - offset_difference: (database_offset - sampled_offset)
        """
        # Crea un diccionario de hashes
        mapper = {}
        for hsh, offset in hashes:
            if hsh.upper() in mapper.keys():
                mapper[hsh.upper()].append(offset)
            else:
                mapper[hsh.upper()] = [offset]

        values = list(mapper.keys())

        d_hashes = {}  # quitar hashes duplicados

        results = []
        with self.cursor() as cur:
            for index in range(0, len(values), batch_size):
                # query
                query = self.SELECT_MULTIPLE % ', '.join([self.IN_MATCH] * len(values[index: index + batch_size]))

                cur.execute(query, values[index: index + batch_size])

                for hsh, sid, offset in cur:
                    if sid not in d_hashes.keys():
                        d_hashes[sid] = 1
                    else:
                        d_hashes[sid] += 1
                    #  evalua todos los offset de cada hash que coincide
                    for song_sampled_offset in mapper[hsh]:
                        results.append((sid, offset - song_sampled_offset))

            return results, d_hashes

    def delete_songs_by_id(self, song_ids: List[int], batch_size: int = 1000) -> None:
        """
        Dada una lista de canciones, las borra y también sus correspondientes fingerprints.

        :param song_ids: lista de ids de canciones.
        :param batch_size: tamaño de los batches.
        """
        with self.cursor() as cur:
            for index in range(0, len(song_ids), batch_size):
                # query
                query = self.DELETE_SONGS % ', '.join(['%s'] * len(song_ids[index: index + batch_size]))

                cur.execute(query, song_ids[index: index + batch_size])
