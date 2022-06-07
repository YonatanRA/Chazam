import os

CONFIG = {'database': {'host': 'yonrod.mysql.pythonanywhere-services.com',
                       'user': 'yonrod',
                       'password': 'password_1234567890',
                       'database': 'yon$fingerprint'}}

WAV_PATH = os.path.dirname(os.path.abspath(__file__)) + '/match/audio.wav'

COVERS = {
    'Rosalía - Saoko': 'https://images.genius.com/717bbc9f2bb3c17d3a8161b898f682e1.1000x1000x1.png',
    'Rosalía - Chicken Teriyaki': 'https://images.genius.com/717bbc9f2bb3c17d3a8161b898f682e1.1000x1000x1.png',
    'Robert Miles - Children': 'https://m.media-amazon.com/images/I/91wmq5EE0zL._SL1414_.jpg',
    'Chanel - SloMo': 'https://images.genius.com/0ee67ebc42b7c0d9924dcd8148dea503.1000x1000x1.png',
    'Masayoshi Takanaka - Manifestation': 'https://i.discogs.com/tpI98ojXWZd4BS47eeHlzDTVkPTeUgfYRwY2vxy0t0I/rs:fit/g:sm/q:90/h:568/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE5NzEz/NDQ4LTE2Mjc5MDgz/OTItMTk4NC5qcGVn.jpeg',
    'Masayoshi Takanaka - Speed of Love': 'https://i.scdn.co/image/ab67616d0000b273047f1d8d58425016d92dffec',
    'Radio Futura - Han caído los dos': 'https://i.ytimg.com/vi/dk0njJTT7Q8/hqdefault.jpg',
    'Michael Jackson - Workin Day and Night': 'https://i1.sndcdn.com/artworks-000503561646-j6vazd-t500x500.jpg',
    'Jamiroquai - Runaway': 'https://m.media-amazon.com/images/I/51T72MN2C7L._SX425_.jpg',
    'Radio Futura - Escuela de Calor': 'https://undiaundisco.files.wordpress.com/2015/05/escuela-de-calor.jpg',
    'The Doors - L.A. Woman': 'https://www.lahabitacion235.com/wp-content/uploads/2017/12/The-Doors-L.A.-Woman.jpg',
    'Santana ft. Mana - Corazon Espinado': 'https://i.discogs.com/K5lqQBfdIAoo2ZXlUTuWCVnMWJriezS68imzB4EIl20/rs:fit/g:sm/q:90/h:507/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTcyOTk0/OTUtMTUyNjg2MTIy/MC01NTkwLmpwZWc.jpeg',
    'Foals - Wake Me Up': 'https://www.rockzonemag.com/wp-content/uploads/2021/11/FOALS_WMU.gif',
    'Yello - Oh Yeah': 'https://i1.sndcdn.com/artworks-000208466318-l6lpg5-t500x500.jpg',
    'Woodkid - Run Boy Run': 'https://pics.filmaffinity.com/Woodkid_Run_Boy_Run_V_deo_musical-191105087-large.jpg',
    'Parcels - Lightenup': 'https://i.ytimg.com/vi/BBDwPuq-aWM/maxresdefault.jpg',
    'Stardust - Music Sounds Better With You': 'https://i.ytimg.com/vi/FQlAEiCb8m0/maxresdefault.jpg',
    'Too Many Zooz - Bad Guy': 'https://i.ytimg.com/vi/iD4RyLt_FbE/maxresdefault.jpg',
    'Charlie Winston - Lately': 'https://i.scdn.co/image/ab67616d0000b27398fa77ab7369e87401fd420a',
    'Wax Tailor Ft. Charlie Winston - I Own You': 'https://i.ytimg.com/vi/PYsEo4TTTtM/maxresdefault.jpg',
    'Måneskin - Beggin': 'https://i1.sndcdn.com/artworks-FwMjIfwKk3NLXoyH-LllOIw-t500x500.jpg',
    'Daft Punk ft. Pharrell Williams - Get Lucky': 'https://m.media-amazon.com/images/I/61DVe0f7EWL._SS500_.jpg',
    'Red Hot Chili Peppers - Go Robot': 'https://m.media-amazon.com/images/I/51Eby0+By+L._SX450_.jpg',
    'Michael Jackson - Billie Jean': 'https://i.discogs.com/Bt5Iot_gGPssTvrUFn2f0RZj1M04GKHhadwYMrCA-aw/rs:fit/g:sm/q:90/h:597/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTY1NjE2/OC0xNTg2MzQxMDQ4/LTg0NTkuanBlZw.jpeg',
    'Daft Punk - One More Time': 'https://www.yaconic.com/wp-content/uploads/2019/10/daft-punk--1024x576.jpg',
    'OutKast - Hey Ya!': 'https://i.discogs.com/6wFhFFheU2Oqg7R8GLCMeYA8BKXOQZZMvKC1Mk-MBqw/rs:fit/g:sm/q:90/h:521/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTQxNTAy/Ny0xNTM0Njk3ODg5/LTY3NzYuanBlZw.jpeg',

}

DATA_DEFAULT = {'artist': 'No se muy bien...',
                'song': '...que decirte alegre.😎',
                'cover': 'https://cdn2.f-cdn.com/contestentries/216828/6574242/555231a14fee4_thumb900.jpg',
                'match_time': 0.0}
