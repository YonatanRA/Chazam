import chazam.fingerprint as fingerprint
import chazam.decoder as decoder
import numpy as np

import time

class BaseRecognizer():

	def __init__(self, chazam):
		self.chazam = chazam
		self.Fs = fingerprint.DEFAULT_FS

	def _recognize(self, *data):
		matches = []
		for d in data:
			matches.extend(self.chazam.find_matches(d, Fs=self.Fs))

		return self.chazam.align_matches(matches)

	def recognize(self):
		pass  # base class does nothing


class FileRecognizer(BaseRecognizer):
	def __init__(self, chazam):
		super(FileRecognizer, self).__init__(chazam)

	def recognize_file(self, filename):
		frames, self.Fs, file_hash = decoder.read(filename, self.chazam.limit)

		t = time.time()
		match = self._recognize(*frames)
		t = time.time() - t

		if match:
			match['match_time'] = t

		return match

	def recognize(self, filename):
		return self.recognize_file(filename)


class NoRecordingError(Exception):
	pass
