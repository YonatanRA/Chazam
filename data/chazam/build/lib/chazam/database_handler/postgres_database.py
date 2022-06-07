import queue

import psycopg2
from chazam.base_classes.common_database import CommonDatabase
from chazam.config.settings import (FIELD_FILE_SHA1, FIELD_FINGERPRINTED,
                                    FIELD_HASH, FIELD_OFFSET, FIELD_SONG_ID,
                                    FIELD_SONGNAME, FIELD_TOTAL_HASHES,
                                    FINGERPRINTS_TABLENAME, SONGS_TABLENAME)
from psycopg2.extras import DictCursor


class PostgreSQLDatabase(CommonDatabase):
    """
     Manejo de base de datos PostgresQL.
    """
    type = 'postgres'

    # creación de tablas
    CREATE_SONGS_TABLE = f"""
        create table if not exists "{SONGS_TABLENAME}" (
            "{FIELD_SONG_ID}" serial,
            "{FIELD_SONGNAME}" varchar(250) not null,
            "{FIELD_FINGERPRINTED}" smallint default 0,
            "{FIELD_FILE_SHA1}" bytea,
            "{FIELD_TOTAL_HASHES}" int not null default 0,
            "date_created" timestamp not null default now(),
            "date_modified" timestamp not null default now(),
            constraint "pk_{SONGS_TABLENAME}_{FIELD_SONG_ID}" primary key ("{FIELD_SONG_ID}"),
            constraint "uq_{SONGS_TABLENAME}_{FIELD_SONG_ID}" unique ("{FIELD_SONG_ID}")
        );
    """

    CREATE_FINGERPRINTS_TABLE = f"""
        create table if not exists "{FINGERPRINTS_TABLENAME}" (
            "{FIELD_HASH}" bytea not null,
            "{FIELD_SONG_ID}" INT not null,
            "{FIELD_OFFSET}" INT not null,
            "date_created" timestamp not null default now(),
            "date_modified" timestamp not null default now(),
            constraint "uq_{FINGERPRINTS_TABLENAME}" unique  ("{FIELD_SONG_ID}", "{FIELD_OFFSET}", "{FIELD_HASH}"),
            constraint "fk_{FINGERPRINTS_TABLENAME}_{FIELD_SONG_ID}" foreign key ("{FIELD_SONG_ID}")
                references "{SONGS_TABLENAME}"("{FIELD_SONG_ID}") on delete cascade
        );

        create index if not exists "ix_{FINGERPRINTS_TABLENAME}_{FIELD_HASH}" on "{FINGERPRINTS_TABLENAME}"
        USING hash ("{FIELD_HASH}");
    """

    CREATE_FINGERPRINTS_TABLE_INDEX = f"""
        create index "ix_{FINGERPRINTS_TABLENAME}_{FIELD_HASH}" on "{FINGERPRINTS_TABLENAME}"
        using hash ("{FIELD_HASH}");
    """

    # queries de inserción (ignorar duplicados)
    INSERT_FINGERPRINT = f"""
        insert into "{FINGERPRINTS_TABLENAME}" (
                "{FIELD_SONG_ID}",
                "{FIELD_HASH}",
                "{FIELD_OFFSET}")
        values (%s, decode(%s, 'hex'), %s) on conflict do nothing;
    """

    INSERT_SONG = f"""
        insert into "{SONGS_TABLENAME}" ("{FIELD_SONGNAME}", "{FIELD_FILE_SHA1}","{FIELD_TOTAL_HASHES}")
        values (%s, decode(%s, 'hex'), %s)
        returning "{FIELD_SONG_ID}";
    """

    # queries de selección
    SELECT = f"""
        select "{FIELD_SONG_ID}", "{FIELD_OFFSET}"
        from "{FINGERPRINTS_TABLENAME}"
        where "{FIELD_HASH}" = decode(%s, 'hex');
    """

    SELECT_MULTIPLE = f"""
        select upper(encode("{FIELD_HASH}", 'hex')), "{FIELD_SONG_ID}", "{FIELD_OFFSET}"
        from "{FINGERPRINTS_TABLENAME}"
        where "{FIELD_HASH}" IN (%s);
    """

    SELECT_ALL = f'select "{FIELD_SONG_ID}", "{FIELD_OFFSET}" from "{FINGERPRINTS_TABLENAME}";'

    SELECT_SONG = f"""
        select
            "{FIELD_SONGNAME}",
            upper(encode("{FIELD_FILE_SHA1}", 'hex')) as "{FIELD_FILE_SHA1}",
            "{FIELD_TOTAL_HASHES}"
        from "{SONGS_TABLENAME}"
        where "{FIELD_SONG_ID}" = %s;
    """

    SELECT_NUM_FINGERPRINTS = f'select count(*) as n from "{FINGERPRINTS_TABLENAME}";'

    SELECT_UNIQUE_SONG_IDS = f"""
        select count("{FIELD_SONG_ID}") as n
        from "{SONGS_TABLENAME}"
        where "{FIELD_FINGERPRINTED}" = 1;
    """

    SELECT_SONGS = f"""
        select
            "{FIELD_SONG_ID}",
            "{FIELD_SONGNAME}",
            upper(encode("{FIELD_FILE_SHA1}", 'hex')) as "{FIELD_FILE_SHA1}",
            "{FIELD_TOTAL_HASHES}",
            "date_created"
        from "{SONGS_TABLENAME}"
        where "{FIELD_FINGERPRINTED}" = 1;
    """

    # borrar tablas
    DROP_FINGERPRINTS = F'drop table if exists "{FINGERPRINTS_TABLENAME}";'
    DROP_SONGS = F'drop table if exists "{SONGS_TABLENAME}";'

    # actualizar registros
    UPDATE_SONG_FINGERPRINTED = f"""
        update "{SONGS_TABLENAME}" set
            "{FIELD_FINGERPRINTED}" = 1
        ,   "date_modified" = now()
        where "{FIELD_SONG_ID}" = %s;
    """

    # eliminar registros
    DELETE_UNFINGERPRINTED = f"""
        delete from "{SONGS_TABLENAME}" where "{FIELD_FINGERPRINTED}" = 0;
    """

    DELETE_SONGS = f"""
        delete from "{SONGS_TABLENAME}" where "{FIELD_SONG_ID}" IN (%s);
    """

    # match
    IN_MATCH = f'decode(%s, "hex")'

    def __init__(self, **options):
        super().__init__()
        self.cursor = cursor_factory(**options)
        self._options = options

    def after_fork(self) -> None:
        # Elimina la cache del cursor. El proceso anterior se borra.
        Cursor.clear_cache()

    def insert_song(self, song_name: str, file_hash: str, total_hashes: int) -> int:
        """
        Inserta una canción en la base de datos y devuelve el id de la canción

        :param song_name: nombre de al canción.
        :param file_hash: hash de el archivo fingerprinteado.
        :param total_hashes: número total de hashes a insertar en la tabla de fingerprints.

        :return: id de la canción.
        """
        with self.cursor() as cur:
            cur.execute(self.INSERT_SONG, (song_name, file_hash, total_hashes))
            return cur.fetchone()[0]

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
    Establece la conexión a la base de datos y devuelve un cursor abierto.

    with Cursor() as cur:
        cur.execute(query)
        ...
    """

    def __init__(self, dictionary=False, **options):
        super().__init__()

        self._cache = queue.Queue(maxsize=5)

        try:
            conn = self._cache.get_nowait()
            # se hace ping antes de tirar de la cache
            conn.ping(True)
        except queue.Empty:
            conn = psycopg2.connect(**options)

        self.conn = conn
        self.dictionary = dictionary

    @classmethod
    def clear_cache(cls):
        cls._cache = queue.Queue(maxsize=5)

    def __enter__(self):
        if self.dictionary:
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
        else:
            self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, ex_type, ex_value, traceback):
        # si hay un error con PostgresQL, trata de hacer rollback del cursor.
        if ex_type is psycopg2.DatabaseError:
            self.cursor.rollback()

        self.cursor.close()
        self.conn.commit()

        # Put it back on the queue
        try:
            self._cache.put_nowait(self.conn)
        except queue.Full:
            self.conn.close()
