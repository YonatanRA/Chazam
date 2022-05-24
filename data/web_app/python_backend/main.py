from flask import Flask, request
from flask_cors import CORS

from chazam import Chazam

from config import CONFIG, WAV_PATH, COVERS, DATA_DEFAULT


app=Flask(__name__)

cors=CORS(app, resources={r'*': {'origins': '*'}})

ih_chazam=Chazam(CONFIG)


@app.route('/', methods=['POST', 'GET'])
def main():

    audio=request.files['blob']
    audio.save(WAV_PATH)

    song=ih_chazam.recognize(WAV_PATH)

    try:
        if song['confidence'] < 100:
            return f'{DATA_DEFAULT}', 200

        else:

            song_name=song['song_name'].split('-')

            data={'artist': song_name[0].strip(),
                  'song': song_name[1].strip(),
                  'cover': COVERS[song['song_name']],
                  'match_time': song['match_time']
                  }

            return f'{data}', 200

    except:
        return f'{DATA_DEFAULT}', 200



if __name__== '__main__':
    app.run(debug=True)



