import hashlib
from operator import itemgetter
from typing import List, Tuple

import matplotlib.mlab as mlab
import numpy as np
from chazam.config.settings import (CONNECTIVITY_MASK, DEFAULT_AMP_MIN,
                                    DEFAULT_FAN_VALUE, DEFAULT_FS,
                                    DEFAULT_OVERLAP_RATIO, DEFAULT_WINDOW_SIZE,
                                    FINGERPRINT_REDUCTION, MAX_HASH_TIME_DELTA,
                                    MIN_HASH_TIME_DELTA,
                                    PEAK_NEIGHBORHOOD_SIZE, PEAK_SORT)
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import (binary_erosion,
                                      generate_binary_structure,
                                      iterate_structure)


def fingerprint(channel: List[int],
                Fs: int = DEFAULT_FS,
                w_size: int = DEFAULT_WINDOW_SIZE,
                w_ratio: float = DEFAULT_OVERLAP_RATIO,
                fan_value: int = DEFAULT_FAN_VALUE,
                amp_min: int = DEFAULT_AMP_MIN) -> List[Tuple[str, int]]:
    """
    Fast Fourier Transform del canal, transformación logarítmica de la salida, encuentra máximos locales y devuelve los hashes.

    :param channel: canal para fingerprintear.
    :param Fs: frecuencia de muestreo del audio.
    :param w_size: tamaño de la ventana de la transformada rápida de Fourier.
    :param w_ratio: ratio de la ventana por el cual se superpone con la anterior y siguiente ventana.
    :param fan_value: grado por el cual un fingerprint puede ser pareado con sus vecinos.
    :param amp_min: mínima amplitud en el espectrograma para ser considerado pico.

    :return: una lista de hashes con sus correspondientes offsets.
    """
    # FFT de la señal y extrae las componentes de frecuencias.
    arr = mlab.specgram(
        channel,
        NFFT=w_size,
        Fs=Fs,
        window=mlab.window_hanning,
        noverlap=int(w_size * w_ratio))[0]

    # aplica transformación logarítmica de la salida porque specgram devuelve un array lineal. los 0s son excluidos para evitar warnings.
    arr = 10 * np.log10(arr, out=np.zeros_like(arr), where=(arr != 0))

    # extrae los picos del espectrograma.
    local_maxima = get_spectrum_peaks(arr, amp_min=amp_min)

    # devuelve hashes.
    return hashing(local_maxima, distance=fan_value)


def get_spectrum_peaks(arr: np.array, amp_min: int = DEFAULT_AMP_MIN) \
        -> np.array(Tuple[List[int], List[int]]):
    """
    Extrae los picos máximos del espectrograma (matriz, arr).

    :param arr: representación matricial del espectrograma.
    :param amp_min: mínima amplitud en el espectrograma para ser considerado pico.

    :return: una lista de tuplas con frecuencia y tiempo de cada pico máximo.
    """
    # El código original usa una máscara que no considera elementos diagonales como vecinos,
    # una figura en diamante, y luego aplica la dilatación. Se propone una figura en cuadrado:
    #       F   T   F           T   T   T
    #       T   T   T   ==>     T   T   T
    #       F   T   F           T   T   T
    # Esta aproximación mejora la velocidad en un 3X sin afectar al acierto.
    # Se genera la mascara con la siguiente función de scipy:
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.generate_binary_structure.html
    mask = generate_binary_structure(2, CONNECTIVITY_MASK)

    #  Y se aplica la dilatación con la siguiente función de scipy:
    #  http://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.iterate_structure.html
    #  Si PEAK_NEIGHBORHOOD_SIZE = 2 se puede escribir:
    #  filter_ = np.ones((PEAK_NEIGHBORHOOD_SIZE * 2 + 1, PEAK_NEIGHBORHOOD_SIZE * 2 + 1), dtype=bool)
    filter_ = iterate_structure(mask, PEAK_NEIGHBORHOOD_SIZE)

    # encuentra el máximo local usando la máscara.
    local_max = maximum_filter(arr, footprint=filter_) == arr

    # aplica erosion, elimina el suelo.
    background = (arr == 0)
    eroded_background = binary_erosion(background, structure=filter_, border_value=1)

    # máscara booleana de arr con True en los picos (aplica XOR en ambas matrices).
    detected_peaks = local_max != eroded_background

    # extrae picos
    amps = arr[detected_peaks]
    freq, times = np.where(detected_peaks)

    # aplana el array y saca los indices para frecuencia y tiempo
    amps = amps.flatten()

    filter_idxs = np.where(amps > amp_min)

    freq_filter = freq[filter_idxs]
    times_filter = times[filter_idxs]

    return list(zip(freq_filter, times_filter))


def hashing(peaks: List[Tuple[int, int]], distance: int = DEFAULT_FAN_VALUE) -> List[Tuple[str, int]]:
    """
    Aplica el fingerprinting y la función hash a los picos resultantes (máximos locales).
    Estructura del hash:
       sha1_hash[0:FINGERPRINT_REDUCTION]    time_offset
        [(e05b341a9b77a51fd26, 32), ... ]

    :param peaks: lista de picos (frecuencia, tiempo).
    :param distance: distancia para que sea considerado un pico en el fingerprint.

    :return: una lista de hashes con sus offsets (tiempo donde empieza el fingerprint).
    """
    idx_freq = 0  # las frecuencias primero en la tupla...
    idx_time = 1  # ...y el tiempo después, los indices.

    if PEAK_SORT:
        peaks.sort(key=itemgetter(1))

    hashes = []
    for i in range(len(peaks)):
        for j in range(1, distance):
            if (i + j) < len(peaks):

                freq1 = peaks[i][idx_freq]
                freq2 = peaks[i + j][idx_freq]
                t1 = peaks[i][idx_time]
                t2 = peaks[i + j][idx_time]
                t_delta = t2 - t1

                if MIN_HASH_TIME_DELTA <= t_delta <= MAX_HASH_TIME_DELTA:
                    h = hashlib.sha1(f'{str(freq1)}|{str(freq2)}|{str(t_delta)}'.encode('utf-8'))

                    hashes.append((h.hexdigest()[0:FINGERPRINT_REDUCTION], t1))

    return hashes
