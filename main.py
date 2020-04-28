from flask import Flask, jsonify, request, Response, abort, make_response
from flask_socketio import SocketIO, send, emit
import requests, time
from flask_cors import CORS, cross_origin
import json, time, random, hashlib, atexit, os, jwt, datetime
from google.cloud import texttospeech
# from camera import VideoCamera
import json
import base64
import threading
import psycopg2
import speech_recognition as sr
from google.cloud import speech
from google.cloud.speech_v1p1beta1 import enums
from functools import wraps


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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'diploma-seceret'
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, cors_allowed_origins="https://diplomovka-fe.herokuapp.com")
socketio = SocketIO(app, cors_allowed_origins="https://diplomovka-fe.herokuapp.com")


db_connection = psycopg2.connect(user = "oguyvjhp", password = "PtvRuNnyOrTnWiYbtkha1C7cu0f5Avsi",  host = "kandula.db.elephantsql.com",  port = "5432", database = "oguyvjhp")
PI3_URL_grovepi = 'http://88.212.50.96:8080/rasberry_pi_sensors_grovepi'
PI3_URL_LIGHTS = 'http://88.212.50.96:8080/rasberry_pi_light_sensor' 
PI3_URL = 'http://88.212.50.96:8080/rasberry_pi_sensors'
PI3_LIGHT_SENSORS = 'http://88.212.50.96:8080/rasberry_pi_light_sensor'

def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
def tuple_to_dict(tup, di): 
    di = dict(tup) 
    return di 

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'res': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            query = """SELECT email FROM public.users WHERE email='{0}'""".format(data['user'])
            cursor = db_connection.cursor()
            cursor.execute(query)
            user = cursor.fetchone()
            db_connection.commit()
        except:
            return jsonify({'res': 'Token is invalid'})

        return f(user, *args, **kwargs)
    return decorated
        
    
@app.route('/user/auth')
@token_required
def auth(user):
    query = """SELECT * FROM public.users WHERE email='{0}'""".format(user[0])
    cursor = db_connection.cursor()
    cursor.execute(query)
    data = cursor.fetchone()
    db_connection.commit()

    return jsonify({'res': 'user verified', 'user': {'id': data[0], 'surname': data[1].strip(), 'lastname': data[2].strip(), 'email': data[3].strip() } })

@app.route('/logIn')
#@cross_origin()
def logIn():
    if(request.method == 'GET'):
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return make_response('Not verified', 401, {'WWW.Authenticate': 'Basic realm="Login required."'})
        try:   
            email = auth.username
            password = hashlib.md5(auth.password.encode()).hexdigest()
            query = """SELECT password FROM public.users WHERE email='{0}'""".format(email)
            cursor = db_connection.cursor()
            cursor.execute(query)
            data = cursor.fetchone()
            db_connection.commit()
        
            if data == None:
                return jsonify({"response": "user doesnt exist"})
            elif data[0].strip() == password: 
                token = jwt.encode({'user': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
                return jsonify({'token': token.decode('UTF-8')})
            else: return jsonify({"response": "bad password"})
            
        except Exception as err:
            print(err)
            return jsonify({"response": "error"})
        
@app.route('/registration', methods=['POST'])
def registration():
    if(request.method == 'POST'):
        try:
            firstName = request.get_json()['firstName']
            lastName = request.get_json()['lastName']
            email = request.get_json()['email']
            password = hashlib.md5(request.get_json()['password'].encode()).hexdigest()

            query = 'SELECT id, email FROM users'
            cursor = db_connection.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            db_connection.commit()
            newID = 1
            if data != None:
                for i in data:
                    if(email == i[1].strip()):
                        return jsonify({'response': 'user exists'})
            else: 
                newID = data.pop()[0] + 1  
         
            query = "INSERT INTO users (id, first_name, last_name, email, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}') ".format(newID, firstName, lastName, email, password)
            cursor = db_connection.cursor()
            cursor.execute(query)
            db_connection.commit()
            return jsonify({'response': 'success'})
        except Exception as err:
            print(err)
            return jsonify({'response': 'error'})

@app.route('/updateLastActionTable', methods=['POST'])
def updateLastActionTable():
    try:
        userID = request.get_json()['userID']
        action = request.get_json()['action']
        time = request.get_json()['time']
        query = """INSERT INTO "tableActions" ("userID", action, time) VALUES ('{0}', '{1}', '{2}');""".format(userID, action, time)
        cursor = db_connection.cursor()
        cursor.execute(query)
        db_connection.commit()
        return jsonify({"response": "success"})
    except Exception as err:
        return jsonify({"response": "error"})


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
    return jsonify({"conncection": "ok"})


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
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="speechToTextCredentials.json"
    # print('GOOGLE', os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    # client = texttospeech.TextToSpeechClient()
    # text = request.get_json()['text']
    # synthesis_input = texttospeech.types.SynthesisInput(text=text)
    # voice = texttospeech.types.VoiceSelectionParams(
    # language_code='sk-SK',
    # name='sk-SK-Wavenet-A',
    # ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE)

    # # Select the type of audio file you want returned
    # audio_config = texttospeech.types.AudioConfig(
    #     audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    # # Perform the text-to-speech request on the text input with the selected
    # # voice parameters and audio file type
    # response = client.synthesize_speech(synthesis_input, voice, audio_config)
    # # with open('output.mp3', 'wb') as out:
    # #     out.write(response.audio_content)
    # return Response(response.audio_content, mimetype="audio/mp3")
    rpi_sensors_grovepi = requests.get(url=PI3_URL_grovepi).json()
    return jsonify({"text to speech": rpi_sensors_grovepi})
    

@socketio.on('connect')
def connectHandler():
    send('YES WORKING')

@socketio.on('join')
def connectHandler2(data):
    query = 'SELECT title, power FROM public.sensors'
    cursor = db_connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    db_connection.commit()
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
    db_connection.commit()
    dictionary = {}
    data = tuple_to_dict(data, dictionary)
    emit('update_actions', data, broadcast=True)

@socketio.on('update_sensors')
def test5(data):
    print('update_sensors')
    query = 'UPDATE sensors SET power =' + str(data["bool"]).lower() +" WHERE id = " + str(data["id"])
    cursor = db_connection.cursor()
    cursor.execute(query)

    query = 'SELECT tb.action, tb.time, u.email from "tableActions" tb LEFT JOIN "users" u ON u.id=tb."userID"'
    cursor = db_connection.cursor()
    cursor.execute(query)
    tableData = cursor.fetchall()
    db_connection.commit()
    retTable = []
    for i in tableData:
        retTable.append({
            'action':i[0],
            'id': i[2].strip(),
            'time': """{0}.{1}.{2} {3}:{4}""".format(i[1].day, i[1].month, i[1].year, i[1].hour, i[1].minute)
            })
    query = 'SELECT title, power FROM public.sensors'
    cursor.execute(query)
    data = cursor.fetchall()
    db_connection.commit()
    dictionary = {}
    data = tuple_to_dict(data, dictionary)


    emit('update_actions', data, broadcast=True)
    emit('update_table_data', retTable, broadcast=True)

@socketio.on('update_sensor_lights')
def update_sensor_lights(data):
    query = 'UPDATE sensors SET power =' + str(data["bool"]).lower() +" WHERE id = 10"
    cursor = db_connection.cursor()
    cursor.execute(query)   
    db_connection.commit()

    headers = {'content-type': 'application/json'}
    req = requests.post(url=PI3_LIGHT_SENSORS, data=json.dumps({'lights': data['bool']}), headers=headers)

@socketio.on('update_sensors_grovepi_interval')
def update_sensors_interval():
    try:
        rpi_sensors_grovepi = requests.get(url=PI3_URL_grovepi).json()
        print(rpi_sensors_grovepi)
        emit('update_sensors', rpi_sensors_grovepi, broadcast=True)
    except Exception as err:
        emit('error', )

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
    #socketio.run(app, port=port)