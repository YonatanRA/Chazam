from pydub import AudioSegment

def audio_cutting(theme: str, start_min: int, start_sec: int, end_min: int, end_sec: int) -> None:

    start_time = start_min * 60 * 1000 + start_sec * 1000 
    end_time = end_min * 60 * 1000 + end_sec * 1000

    song = AudioSegment.from_wav(f'audio/{theme}.wav')
    
    extract = song[start_time:end_time]
    extract.export(f'sample/{theme}.wav', format='wav')