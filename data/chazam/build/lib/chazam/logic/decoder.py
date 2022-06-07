import fnmatch
import os
from hashlib import sha1
from typing import List, Tuple

import numpy as np
from chazam.tools import wavio
from pydub import AudioSegment
from pydub.utils import audioop


def unique_hash(file_path: str, block_size: int = 2 ** 20) -> str:
    """ Función generadora de hashes dado un archivo. Inspirado en la versión MD5:
    http://stackoverflow.com/a/1131255/712997

    :param file_path: ruta al archivo.
    :param block_size: tamaño del bloque ha ser leído.

    :return: un hash en una string hexagesimal.
    """
    s = sha1()
    with open(file_path, 'rb') as f:
        while True:
            buf = f.read(block_size)
            if not buf:
                break
            s.update(buf)
    return s.hexdigest().upper()


def find_files(path: str, extensions: List[str]) -> List[Tuple[str, str]]:
    """
    Obtener todos los archivos que corresponden con las extensiones dadas.

    :param path: ruta al directorio de archivos de audio.
    :param extensions: extensiones de los archivos de audio a obtener.

    :return: una lista de tuplas con los nombres de archivo y las extensiones.
    """
    extensions = [e.replace('.', '') for e in extensions]  # permite con punto o sin el para las extensiones (mp3, .mp3)

    results = []
    for dir_path, dir_names, files in os.walk(path):
        for extension in extensions:
            for f in fnmatch.filter(files, f'*.{extension}'):
                p = os.path.join(dir_path, f)
                results.append((p, extension))
    return results


def read(file_name: str, limit: int = None) -> Tuple[List[List[int]], int, str]:
    """
    Lectura de archivos de audio con pydub (ffmpeg) y devuelve los datos que contiene.
    Se usa wavio si el audio es wav 24-bit, como backup.

    :param file_name: archivo a leer.
    :param limit: número de segundos límite.

    :return: tupla de listas de (canales, frecuencia de muestreo, archivo hash).
    """
    # pydub no soporta archivos wav 24-bit, se usa wavio cuando falla
    try:
        audio_file = AudioSegment.from_file(file_name)

        if limit:
            audio_file = audio_file[:limit * 1000]

        data = np.fromstring(audio_file.raw_data, np.int16)

        channels = []
        for chn in range(audio_file.channels):
            channels.append(data[chn::audio_file.channels])

    except audioop.error:
        _, _, audio_file = wavio.read(file_name)

        if limit:
            audio_file = audio_file[:limit * 1000]

        audio_file = audio_file.T
        audio_file = audio_file.astype(np.int16)

        channels = []
        for chn in audio_file:
            channels.append(chn)

    return channels, audio_file.frame_rate, unique_hash(file_name)


def get_audio_name_from_path(file_path: str) -> str:
    """
    Extracts song name from a file path.

    :param file_path: path to an audio file.
    :return: file name
    """
    return os.path.splitext(os.path.basename(file_path))[0]
