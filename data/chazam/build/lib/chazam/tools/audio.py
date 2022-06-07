from pydub import AudioSegment


def audio_cutting(theme: str, start_min: int, start_sec: int, end_min: int, end_sec: int) -> None:
    """
    Función para cortar audio desde start_min:start_sec hasta end_min:end_sec

    :theme: str, canción para ser cortada.
    :start_min: int, minuto inicial
    :start_sec: int, segundo inicial
    :end_min: int, minuto final
    :end_sec: int, segundo final
    """
    start_time = start_min * 60 * 1000 + start_sec * 1000
    end_time = end_min * 60 * 1000 + end_sec * 1000

    song = AudioSegment.from_wav(f'audio/{theme}.wav')

    extract = song[start_time:end_time]
    extract.export(f'sample/{theme}.wav', format='wav')
