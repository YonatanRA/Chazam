import queue

import mysql.connector
from chazam.base_classes.common_database import CommonDatabase
from chazam.config.settings import (FIELD_FILE_SHA1, FIELD_FINGERPRINTED,
                                    FIELD_HASH, FIELD_OFFSET, FIELD_SONG_ID,
                                    FIELD_SONGNAME, FIELD_TOTAL_HASHES,
                                    FINGERPRINTS_TABLENAME, SONGS_TABLENAME)
from mysql.connector.errors import DatabaseError


class MySQLDatabase(CommonDatabase):
    """
    Manejo de base de datos SQL.
    """
    type = 'mysql'

    # creación de tablas
    CREATE_SONGS_TABLE = f"""
        create table if not exists `{SONGS_TABLENAME}` (
            `{FIELD_SONG_ID}` mediumint unsigned not null auto_increment,
            `{FIELD_SONGNAME}` varchar(250) not null,
            `{FIELD_FINGERPRINTED}` tinyint default 0,
            `{FIELD_FILE_SHA1}` binary(20) not null,
            `{FIELD_TOTAL_HASHES}` int not null default 0,
            `date_created` datetime not null default current_timestamp,
            `date_modified` datetime not null default current_timestamp on update current_timestamp,
            constraint `pk_{SONGS_TABLENAME}_{FIELD_SONG_ID}` primary key (`{FIELD_SONG_ID}`),
            constraint `uq_{SONGS_TABLENAME}_{FIELD_SONG_ID}` unique key (`{FIELD_SONG_ID}`)
        ) ENGINE=INNODB;
    """

    CREATE_FINGERPRINTS_TABLE = f"""
        create table if not exists `{FINGERPRINTS_TABLENAME}` (
            `{FIELD_HASH}` BINARY(10) NOT NULL,
            `{FIELD_SONG_ID}` MEDIUMINT UNSIGNED NOT NULL,
            `{FIELD_OFFSET}` INT UNSIGNED NOT NULL,
            `date_created` datetime not null default current_timestamp,
            `date_modified` datetime not null default current_timestamp on update current_timestamp,
            index `ix_{FINGERPRINTS_TABLENAME}_{FIELD_HASH}` (`{FIELD_HASH}`),
            constraint `uq_{FINGERPRINTS_TABLENAME}_{FIELD_SONG_ID}_{FIELD_OFFSET}_{FIELD_HASH}`
                unique key  (`{FIELD_SONG_ID}`, `{FIELD_OFFSET}`, `{FIELD_HASH}`),
            constraint `fk_{FINGERPRINTS_TABLENAME}_{FIELD_SONG_ID}` FOREIGN KEY (`{FIELD_SONG_ID}`)
                references `{SONGS_TABLENAME}`(`{FIELD_SONG_ID}`) on delete cascade
    ) ENGINE=INNODB;
    """

    # queries de inserción
    INSERT_FINGERPRINT = f"""
        insert ignore into `{FINGERPRINTS_TABLENAME}` (
                `{FIELD_SONG_ID}`,
                `{FIELD_HASH}`,
                `{FIELD_OFFSET}`)
        values (%s, UNHEX(%s), %s);
    """

    INSERT_SONG = f"""
        insert into `{SONGS_TABLENAME}` (`{FIELD_SONGNAME}`,`{FIELD_FILE_SHA1}`,`{FIELD_TOTAL_HASHES}`)
        values (%s, UNHEX(%s), %s);
    """

    # queries de selección
    SELECT = f"""
        select `{FIELD_SONG_ID}`, `{FIELD_OFFSET}`
        from `{FINGERPRINTS_TABLENAME}`
        where `{FIELD_HASH}` = UNHEX(%s);
    """

    SELECT_MULTIPLE = f"""
        select HEX(`{FIELD_HASH}`), `{FIELD_SONG_ID}`, `{FIELD_OFFSET}`
        from `{FINGERPRINTS_TABLENAME}`
        where `{FIELD_HASH}` in (%s);
    """

    SELECT_ALL = f"select `{FIELD_SONG_ID}`, `{FIELD_OFFSET}` from `{FINGERPRINTS_TABLENAME}`;"

    SELECT_SONG = f"""
        select `{FIELD_SONGNAME}`, HEX(`{FIELD_FILE_SHA1}`) as `{FIELD_FILE_SHA1}`, `{FIELD_TOTAL_HASHES}`
        from `{SONGS_TABLENAME}`
        where `{FIELD_SONG_ID}` = %s;
    """

    SELECT_NUM_FINGERPRINTS = f"select count(*) as n from `{FINGERPRINTS_TABLENAME}`;"

    SELECT_UNIQUE_SONG_IDS = f"""
        select count(`{FIELD_SONG_ID}`) as n
        from `{SONGS_TABLENAME}`
        where `{FIELD_FINGERPRINTED}` = 1;
    """

    SELECT_SONGS = f"""
        select
            `{FIELD_SONG_ID}`
        ,   `{FIELD_SONGNAME}`
        ,   HEX(`{FIELD_FILE_SHA1}`) as `{FIELD_FILE_SHA1}`
        ,   `{FIELD_TOTAL_HASHES}`
        ,   `date_created`
        from `{SONGS_TABLENAME}`
        where `{FIELD_FINGERPRINTED}` = 1;
    """

    # borrar tablas
    DROP_FINGERPRINTS = f"drop table if exists `{FINGERPRINTS_TABLENAME}`;"
    DROP_SONGS = f"drop table if exists `{SONGS_TABLENAME}`;"

    # actualizar registros
    UPDATE_SONG_FINGERPRINTED = f"""
        update `{SONGS_TABLENAME}` set `{FIELD_FINGERPRINTED}` = 1 where `{FIELD_SONG_ID}` = %s;
    """

    # eliminar registros
    DELETE_UNFINGERPRINTED = f"""
        delete from `{SONGS_TABLENAME}` where `{FIELD_FINGERPRINTED}` = 0;
    """

    DELETE_SONGS = f"""
        delete from `{SONGS_TABLENAME}` where `{FIELD_SONG_ID}` in (%s);
    """

    # match
    IN_MATCH = f'UNHEX(%s)'

    def __init__(self, **options):
        super().__init__()
        self.cursor = cursor_factory(**options)
        self._options = options

    def after_fork(self) -> None:
        # Elimina la cache del cursor. El proceso anterior se borra.
        Cursor.clear_cache()

    def insert_song(self, song_name: str, file_hash: str, total_hashes: int) -> int:
        """
        Inserts a song name into the database, returns the new
        identifier of the song.

        :param song_name: The name of the song.
        :param file_hash: Hash from the fingerprinted file.
        :param total_hashes: amount of hashes to be inserted on fingerprint table.
        :return: the inserted id.
        """
        with self.cursor() as cur:
            cur.execute(self.INSERT_SONG, (song_name, file_hash, total_hashes))
            return cur.lastrowid

    def __getstate__(self):
        return self._options,

    def __setstate__(self, state):
        self._options, = state
        self.cursor = cursor_factory(**self._options)


def cursor_factory(**factory_options):
    def cursor(**options):
        options.update(factory_options)
        return Cursor(**options)

    return cursor


class Cursor(object):
    """
    Establishes a connection to the database and returns an open cursor.
    # Use as context manager
    with Cursor() as cur:
        cur.execute(query)
        ...
    """

    def __init__(self, dictionary=False, **options):
        super().__init__()

        self._cache = queue.Queue(maxsize=5)

        try:
            conn = self._cache.get_nowait()
            # Ping the connection before using it from the cache.
            conn.ping(True)
        except queue.Empty:
            conn = mysql.connector.connect(**options)

        self.conn = conn
        self.dictionary = dictionary

    @classmethod
    def clear_cache(cls):
        cls._cache = queue.Queue(maxsize=5)

    def __enter__(self):
        self.cursor = self.conn.cursor(dictionary=self.dictionary)
        return self.cursor

    def __exit__(self, extype, exvalue, traceback):
        # if we had a MySQL related error we try to rollback the cursor.
        if extype is DatabaseError:
            self.cursor.rollback()

        self.cursor.close()
        self.conn.commit()

        # Put it back on the queue
        try:
            self._cache.put_nowait(self.conn)
        except queue.Full:
            self.conn.close()
