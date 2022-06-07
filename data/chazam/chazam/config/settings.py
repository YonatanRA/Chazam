# chazam config

# Respuesta JSON
SONG_ID = 'song_id'
SONG_NAME = 'song_name'
RESULTS = 'results'

HASHES_MATCHED = 'hashes_matched_in_input'

### Hashes fingerprintedeados en la base datos.
FINGERPRINTED_HASHES = 'fingerprinted_hashes_in_db'
# Percentage regarding hashes matched vs hashes fingerprinted in the db.
FINGERPRINTED_CONFIDENCE = 'fingerprinted_confidence'

### Hashes generados por el archivo de entrada.
INPUT_HASHES = 'input_total_hashes'
### Porcentaje segun los hashes que machean contra los que entran.
INPUT_CONFIDENCE = 'input_confidence'

TOTAL_TIME = 'total_time'
FINGERPRINT_TIME = 'fingerprint_time'
QUERY_TIME = 'query_time'
ALIGN_TIME = 'align_time'
OFFSET = 'offset'
OFFSET_SECS = 'offset_seconds'

# Base de datos
### Instancias de la clase DATABASE:
DATABASES = {
    'mysql': ('chazam.database_handler.mysql_database', 'MySQLDatabase'),
    'postgres': ('chazam.database_handler.postgres_database', 'PostgreSQLDatabase')
}

### Conexión a la base de datos de MySQL
SQL_CONFIG = {'database': {'host': '127.0.0.1',
                           'user': 'root',
                           'password': 'password',
                           'database': 'fingerprint'}}

### tabla canciones
SONGS_TABLENAME = 'songs'

### columnas tabla canciones
FIELD_SONG_ID = 'song_id'
FIELD_SONGNAME = 'song_name'
FIELD_FINGERPRINTED = "fingerprinted"
FIELD_FILE_SHA1 = 'file_sha1'
FIELD_TOTAL_HASHES = 'total_hashes'

### tabla fingerprints
FINGERPRINTS_TABLENAME = 'fingerprints'

### columnas tabla fingerprints
FIELD_HASH = 'hash'
FIELD_OFFSET = 'offset'

# CONFIGURACION del FINGERPRINTING:
# En realidad es parámetro para la función scipy.generate_binary_structure.
# Este parámetro cambia la forma de la máscara usada para extraer los máximos locales del espectrograma.
# Valores posibles son 1 o 2.
# 1 implica usar la forma de diamante en la máscara, elementos de la diagonal no son considerados vecinos.
# 2 implica usar la forma cuadrada en la máscara, elementos de la diagonal son considerados vecinos.
CONNECTIVITY_MASK = 2

# Frecuencia de muestreo del audio
DEFAULT_FS = 48000

# Tamaño de la ventana para FFT, afecta a la granularidad
DEFAULT_WINDOW_SIZE = 12000

# Ratio de superposición entre ventanas siguientes de la FFT.
# Subir este valor aumentará la granularidad del offset(mejor reconocimiento en el tiempo), pero muchos más fingerprints
DEFAULT_OVERLAP_RATIO = 0.9  # valor por defecto 0.5

# Grado por el cual un fingerprint puede ser pareado con sus vecinos.
# Aumentar este valor genera más fingerprints, pero mejor acierto.
DEFAULT_FAN_VALUE = 25  # valor por defecto 15

# Mínima amplitud en el espectrograma para ser considerado pico.
# Aumentar este valor disminuye el número de fingerprints, pero peor acierto.
DEFAULT_AMP_MIN = 10  # valor por defecto 10

# Número de celdas alrededor para considerar un pico.
# Aumentar este valor disminuye el número de fingerprints, pero peor acierto.
PEAK_NEIGHBORHOOD_SIZE = 20  # valor por defecto 20

# Umbrales temporales de cuanto de cerca en el tiempo esta para ser parte del fingerprint.
# Si el máximo es demasiado bajo, valores más altos de  DEFAULT_FAN_VALUE pueden no funcionar como se espera.
MIN_HASH_TIME_DELTA = 0  # valor por defecto 0
MAX_HASH_TIME_DELTA = 200  # valor por defecto 200

# True ordena temporalmente los fingerprints.
# No ordenarlos reduce la performance.
PEAK_SORT = True  # valor por defecto True

# Número de bits para hash SHA1 hash en el cálculo del fingerprint calculation.
# Cuanto más alto más memoria de almacenamiento se usa, pero menos coincidencias.
FINGERPRINT_REDUCTION = 20  # valor por defecto 20

# Número de resultados entregados por el reconocedor, canciones que coinciden por orden de confianza.
TOPN = 1  # valor por defecto 1
