from flask import Flask, jsonify, request, Response
import os
from flask_socketio import SocketIO, send, emit
import requests, time
from flask_cors import CORS
import json, time, random, hashlib, atexit, os
from google.cloud import texttospeech
# from camera import VideoCamera
import json
import base64
import threading
import psycopg2
import speech_recognition as sr
from google.cloud import speech
from google.cloud.speech_v1p1beta1 import enums

#from rule_base_system import StartSystem

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="speechToTextCredentials.json"

GLOBAL_CAMERA_LOOP = None
client = speech.SpeechClient()
config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='sk-SK',
        max_alternatives=1)
streaming_config = speech.types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

psql_hostname = 'localhost'
psql_username = 'USERNAME'
psql_password = 'PASSWORD'
psql_database = 'DBNAME'

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, cors_allowed_origins="https://diplomovka-fe.herokuapp.com/")
CORS(app)


#db_connection = psycopg2.connect(user = "oguyvjhp", password = "PtvRuNnyOrTnWiYbtkha1C7cu0f5Avsi",  host = "postgres://oguyvjhp:PtvRuN...@kandula.db.elephantsql.com:5432/oguyvjhp ",  port = "5432", database = "postgres")
db_connection = psycopg2.connect(user = "oguyvjhp", password = "PtvRuNnyOrTnWiYbtkha1C7cu0f5Avsi",  host = "kandula.db.elephantsql.com",  port = "5432", database = "oguyvjhp")
PI3_URL_grovepi = 'http://192.168.10.102:5001/rasberry_pi_sensors_grovepi'
PI3_URL_LIGHTS = 'http://192.168.10.102:5001/rasberry_pi_light_sensor' 
PI3_URL = 'http://192.168.10.102:5001/rasberry_pi_sensors'
PI3_LIGHT_SENSORS = 'http://192.168.10.102:5001/rasberry_pi_light_sensor'

def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
def tuple_to_dict(tup, di): 
    di = dict(tup) 
    return di 

@app.route('/all_sensor_data', methods=['GET'])
def all_sensor_data():
    data = list(mongo.db.sensors.find({}, {'_id': False}))
    return jsonify({'sensors': data})
@app.route('/logIn', methods=['POST'])
def logIn():
    if(request.method == 'POST'):
        email = request.get_json()['email']
        password = request.get_json()['password']
        query = """SELECT * FROM public.users WHERE email='%s' AND password='%s'""" %email, password
        cursor = db_connection.cursor()
        cursor.execute(query)
        data = cursor.fetchone()
        if data == None:
            return jsonify({"response": "error"})
        else:
            return jsonify({"response": "success"})
        
@app.route('/registration', methods=['POST'])
def registration():
    if(request.method == 'POST'):
        try:
            firstName = request.get_json()['firstName']
            lastName = request.get_json()['lastName']
            email = request.get_json()['email']
            password = request.get_json()['password']
            admin = request.get_json()['admin']
            query = "INSERT INTO public.users (first_name, last_name, email, password, admin) VALUES ('"+firstName+"','"+lastName+"','"+email+"','"+password+"','"+str(admin).lower()+"')"
            cursor = db_connection.cursor()
            cursor.execute(query)
            db_connection.commit()
            return jsonify({'response': 'success'})
        except Exception as err:
            print(err)
            return jsonify({'response': 'error'})


GLOBAL_CAMERA = False
def gen(camera):
    while True:
        time.sleep(0.2)
        if not GLOBAL_CAMERA: 
            camera.stop()
            break
        frame = camera.get_frame()
        yield frame
@app.route('/', methods=['GET'])
def test4545():
    return jsonify({"response": "kokot"})

@app.route('/test', methods=['GET'])
def test():
    query = "INSERT INTO users(id, first_name, last_name, email, password) VALUES (2, 'Martin', 'Tovarnak', 'martin.tovarnak@student.tuke.sk', 'test')"
    cursor = db_connection.cursor()
    cursor.execute(query)
    db_connection.commit()
    return jsonify({"response": "connected"})
# @app.route('/video_feed', methods=['POST'])
# def video_feed():
#     global GLOBAL_CAMERA
#     GLOBAL_CAMERA = request.get_json()['play']
#     if GLOBAL_CAMERA:
#         for video_frame in gen(VideoCamera()):  
#             socketio.emit('video_flask',{'data':  video_frame} )
#     return Response(gen(VideoCamera()),
#                       mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/text_to_speech', methods=['POST'])
def textToSpeech():
    print('TEXTTOSPEECH')
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="textToSpeechCredentials.json"
    client = texttospeech.TextToSpeechClient()
    text = request.get_json()['text']
    synthesis_input = texttospeech.types.SynthesisInput(text=text)
    voice = texttospeech.types.VoiceSelectionParams(
    language_code='sk-SK',
    name='sk-SK-Wavenet-A',
    ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE)

    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(synthesis_input, voice, audio_config)
    with open('output.mp3', 'wb') as out:
        out.write(response.audio_content)
    return Response(response.audio_content, mimetype="audio/mp3")
    

@socketio.on('connect')
def connectHandler():
    send('YES WORKING')

@socketio.on('join')
def connectHandler2(data):
    print('JOIN')
    query = 'SELECT title, power FROM public.sensors'
    cursor = db_connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    dictionary = {}
    data = tuple_to_dict(data, dictionary)
    rpi_sensors_grovepi = requests.get(url=PI3_URL_grovepi).json()
    emit('update_sensors', rpi_sensors_grovepi)
    emit('update_actions', data)

@socketio.on('update_sensors_start')
def update_sensors_start():
    print('update_sensors_start')
    query = 'SELECT title, power FROM public.sensors'
    cursor = db_connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    dictionary = {}
    data = tuple_to_dict(data, dictionary)
    emit('update_actions', data, broadcast=True)

@socketio.on('update_sensors')
def test5(data):
    print('update_sensors')
    query = 'UPDATE sensors SET power =' + str(data["bool"]).lower() +" WHERE id = " + str(data["id"])
    cursor = db_connection.cursor()
    cursor.execute(query)
    db_connection.commit()

    query = 'SELECT title, power FROM public.sensors'
    cursor.execute(query)
    data = cursor.fetchall()
    dictionary = {}
    data = tuple_to_dict(data, dictionary)

    emit('update_actions', data, broadcast=True)

@socketio.on('update_sensor_lights')
def update_sensor_lights(data):
    print('update_sensor_lights', data['bool'])

    headers = {'content-type': 'application/json'}
    req = requests.post(url=PI3_LIGHT_SENSORS, data=json.dumps({'lights': data['bool']}), headers=headers)
    print('reeeeq', req.json())

@socketio.on('update_sensors_grovepi_interval')
def update_sensors_interval():
    print('update_sensors_grovepi_interval')
    rpi_sensors_grovepi = requests.get(url=PI3_URL_grovepi).json()

    emit('update_sensors', rpi_sensors_grovepi, broadcast=True)

@socketio.on('expertal_system')
def expertalSystem():
    #a = StartSystem(temp=21, hum=80, motion=False, lights=True, gas=50).getResult()
    emit('expertal_system', {"ok":4})

@socketio.on('binaryData')
def startGoogleCloudStream(data):
    requests = (speech.types.StreamingRecognizeRequest(audio_content=data))
    responses = client.streaming_recognize(streaming_config, requests)
    for result in responses:
        if not response.results:
            continue

        result = response.results[0]

        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', port), app, handler_class=WebSocketHandler)
    server.serve_forever()

    #app.run(host='0.0.0.0', port=port)