import abc
import importlib
from typing import Dict, List, Tuple

from chazam.config.settings import DATABASES


class BaseDatabase(object, metaclass=abc.ABCMeta):
    # Nombre de la subclase Database
    type = None

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
        pass

    @abc.abstractmethod
    def empty(self) -> None:
        """
        Llamada cuando la base de datos está vacía.
        """
        pass

    @abc.abstractmethod
    def delete_unfingerprinted_songs(self) -> None:
        """
        Llamada para borrar canciones no procesadas.
        """
        pass

    @abc.abstractmethod
    def get_num_songs(self) -> int:
        """
        Cuenta el número de canciones.

        :return: número de canciones en la base de datos.
        """
        pass

    @abc.abstractmethod
    def get_num_fingerprints(self) -> int:
        """
        Cuenta el número de fingerprints.

        :return: número de fingerprints en la base de datos.
        """
        pass

    @abc.abstractmethod
    def set_song_fingerprinted(self, song_id: int):
        """
        Establece si una canción ha sido procesada..

        :param song_id: id de la canción.
        """
        pass

    @abc.abstractmethod
    def get_songs(self) -> List[Dict[str, str]]:
        """
        Devuelve todas las canciones procesadas de la base de datos.

        :return: un diccionario con toda la info de las canciones.
        """
        pass

    @abc.abstractmethod
    def get_song_by_id(self, song_id: int) -> Dict[str, str]:
        """
        Info de la canción.
        :param song_id: id de la canción.

        :return: un diccionario con la info de la cancione.
        """
        pass

    @abc.abstractmethod
    def insert(self, fingerprint: str, song_id: int, offset: int):
        """
        Inserta un solo fingerprint en la base de datos.
        :param fingerprint: parte del hash sha1, hexadecimal
        :param song_id: id de la canción.
        :param offset: punto temporal de donde viene el fingerprint.
        """
        pass

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

    @abc.abstractmethod
    def query(self, fingerprint: str = None) -> List[Tuple]:
        """
        Devuelve todas las coincidencias de fingerprints asociados con el hash.
        Si se pasa None devuelve todas las entradas de la base de datos.

        :param fingerprint: parte del hash sha1, en hexadecimal

        :return: una lista de los fingerprints en la base de datos.
        """
        pass

    @abc.abstractmethod
    def get_iterable_kv_pairs(self) -> List[Tuple]:
        """
        Devuelve todos los fingerprints en la base de datos.

        :return: una lista de todos los fingerprints guardados en la base de datos.
        """
        pass

    @abc.abstractmethod
    def insert_hashes(self, song_id: int, hashes: List[Tuple[str, int]], batch_size: int = 1000) -> None:
        """
        Inserción multiple de fingerprints.

        :param song_id: id de la canción
        :param hashes: lista de tuplas con formato (hash, offset)
            - hash: parte del hash sha1, en hexadecimal
            - offset: tiempo donde el hash empieza.
        :param batch_size: tamaño de los batches.
        """

    @abc.abstractmethod
    def return_matches(self, hashes: List[Tuple[str, int]], batch_size: int = 1000) \
            -> Tuple[List[Tuple[int, int]], Dict[int, int]]:
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
        pass

    @abc.abstractmethod
    def delete_songs_by_id(self, song_ids: List[int], batch_size: int = 1000) -> None:
        """
        Dada una lista de canciones, las borra y también sus correspondientes fingerprints.

        :param song_ids: lista de ids de canciones.
        :param batch_size: tamaño de los batches.
        """
        pass


def get_database(database_type: str = 'mysql') -> BaseDatabase:
    """
    Dado un tipo de base de datos devuelve una instancia de la misma.

    :param database_type: tipo de base de datos.

    :return: instancia de la base de datos.
    """
    try:
        path, db_class_name = DATABASES[database_type]
        db_module = importlib.import_module(path)
        db_class = getattr(db_module, db_class_name)
        return db_class
    except (ImportError, KeyError):
        raise TypeError('Unsupported database type supplied.')
