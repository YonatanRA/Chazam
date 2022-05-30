# sacar picos

import numpy as np

from typing import List, Tuple

from scipy.ndimage.filters import maximum_filter

from scipy.ndimage.morphology import binary_erosion, generate_binary_structure, iterate_structure

import hashlib

from operator import itemgetter

from pydub import AudioSegment



def get_spectrum_peaks(arr: np.array, amp_min: int = 10) -> List[Tuple[List[int], List[int]]]:

    struct = generate_binary_structure(2, 2)

    neighborhood = iterate_structure(struct, 20)

    local_max = maximum_filter(arr, footprint=neighborhood) == arr

    background = (arr == 0)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

    detected_peaks = local_max != eroded_background

    amps = arr[detected_peaks]
    freqs, times = np.where(detected_peaks)

    amps = amps.flatten()

    filter_idxs = np.where(amps > amp_min)

    freqs_filter = freqs[filter_idxs]
    times_filter = times[filter_idxs]

    return list(zip(freqs_filter, times_filter))




def hashing(peaks: List[Tuple[int, int]], distance: int = 15) -> List[Tuple[str, int]]:

    idx_freq = 0
    idx_time = 1

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

                if 0 <= t_delta <= 200:
                    
                    h = hashlib.sha1(f'{str(freq1)}|{str(freq2)}|{str(t_delta)}'.encode('utf-8'))

                    hashes.append((h.hexdigest()[0:20], t1))

    return hashes





def audio_cutting(theme: str, start_min: int, start_sec: int, end_min: int, end_sec: int) -> None:

    start_time = start_min * 60 * 1000 + start_sec * 1000 
    end_time = end_min * 60 * 1000 + end_sec * 1000

    song = AudioSegment.from_wav(f'audio/{theme}.wav')
    
    extract = song[start_time:end_time]
    extract.export(f'sample/{theme}.wav', format='wav')
    
    
    
    