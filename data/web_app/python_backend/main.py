from flask import Flask, request
from flask_cors import CORS        # cross-origin resource sharing

from chazam import Chazam

from config import WAV_PATH, COVERS, DATA_DEFAULT


app=Flask(__name__)

cors=CORS(app, resources={r'*': {'origins': '*'}})

ih_chazam=Chazam()


@app.route('/', methods=['POST', 'GET'])
def main():

    audio=request.files['blob']
    audio.save(WAV_PATH)

    song=ih_chazam.recognize(WAV_PATH)

    try:
        if song['results'][0]['input_confidence']<0.2:
            return f'{DATA_DEFAULT}', 200

        else:

            song_name=song['results'][0]['song_name'].decode('utf-8').split('-')

            data={'artist': song_name[0].strip(),
                  'song': song_name[1].strip(),
                  'cover': COVERS[song['results'][0]['song_name'].decode('utf-8')],
                  'match_time': song['total_time']
                  }

            return f'{data}', 200

    except:
        return f'{DATA_DEFAULT}', 200



if __name__== '__main__':
    app.run(debug=True)



