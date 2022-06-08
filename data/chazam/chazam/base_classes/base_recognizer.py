import abc
from time import time
from typing import Dict, List, Tuple

import numpy as np
from chazam.config.settings import DEFAULT_FS


class BaseRecognizer(object, metaclass=abc.ABCMeta):
    def __init__(self, chazam):
        self.chazam = chazam
        self.Fs = DEFAULT_FS

    def _recognize(self, *data) -> Tuple[List[Dict[str, any]], int, int, int]:
        fingerprint_times = []
        hashes = set()  # para borra posibles fingerprints duplicados.
        for channel in data:
            fingerprints, fingerprint_time = self.chazam.generate_fingerprints(channel, Fs=self.Fs)
            fingerprint_times.append(fingerprint_time)
            hashes |= set(fingerprints)

        matches, d_hashes, query_time = self.chazam.find_matches(hashes)

        t = time()
        final_results = self.chazam.align_matches(matches, d_hashes, len(hashes))
        align_time = time() - t

        return final_results, np.sum(fingerprint_times), query_time, align_time

    @abc.abstractmethod
    def recognize(self) -> Dict[str, any]:
        pass  # base, no hace nada
