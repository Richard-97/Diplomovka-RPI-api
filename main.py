from flask import Flask, jsonify, request, Response, abort, make_response
from flask_socketio import SocketIO, send, emit
import requests, time
from flask_cors import CORS, cross_origin
import json, time, random, hashlib, atexit, os, jwt, datetime
from google.cloud import texttospeech
from camera import VideoCamera
import json
import base64
import threading
import psycopg2
import speech_recognition as sr
from google.cloud import speech
from google.cloud.speech_v1p1beta1 import enums
from functools import wraps
import grovepi, io
import RPi.GPIO as GPIO
import Adafruit_DHT
import pygame.camera
from pygame.locals import *
from PIL import Image

from rule_base_system import StartSystem

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

CORS(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")


red_led = 5
green_led = 7
blue_led = 2

gas_sensor = 0 #A0
light_sensor = 2 #A2
magnetic_switch = 3 #D3
switch = 6 #D6
pir_sensor = 8 #D8
potentiometer = 1 #A1

fire_sensor_GPIO = 2
temp_hum_sensor_GPIO = 3

GPIO.setmode(GPIO.BCM)
GPIO.setup(fire_sensor_GPIO, GPIO.IN)
GPIO.setwarnings(False)

grovepi.pinMode(gas_sensor,"INPUT")
grovepi.pinMode(light_sensor,"INPUT")
grovepi.pinMode(potentiometer,"INPUT")
grovepi.pinMode(pir_sensor,"INPUT")
grovepi.pinMode(magnetic_switch,"INPUT")
grovepi.pinMode(switch,"INPUT")
grovepi.pinMode(red_led,"OUTPUT")
grovepi.pinMode(green_led,"OUTPUT")
grovepi.pinMode(blue_led,"OUTPUT")

fire_detection = False


db_connection = psycopg2.connect(user = "postgres", password = "Ronaldo",  host = "localhost",  port = "5432", database = "diplomovka")

def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
def tuple_to_dict(tup, di): 
    di = dict(tup) 
    return di
def getSensorsValues():
    return {
        "gas_sensor": {"data": 50, "density": 10},
        "potenciometer": 1,
        "light_sensors": 300,
        "motion_sensor": True,
        "door_sensor": False,
        "switch_sensor": False,
        "fire_sensor": 1,
        "temperature": 23,
        "humidity": 52,
        "lights": True
        }
    hum, temp = Adafruit_DHT.read_retry(11, 3)
    print('*****')
    gas_sensor_value = grovepi.analogRead(gas_sensor)
    light_sensor_value = grovepi.analogRead(light_sensor)
    motion_sensor_value = grovepi.digitalRead(pir_sensor)
    switch_sensor = grovepi.digitalRead(switch)
    motion = False
    door_sensor_values = False
    gas_density = (float)(gas_sensor_value / 1024)
    magnetic_check_values = []
    
    for i in range(0,5):
        magnetic_check_values.append(grovepi.digitalRead(magnetic_switch))
        time.sleep(0.5)
        
    if motion_sensor_value==0 or motion_sensor_value==1:
        if motion_sensor_value==1:
            motion = True
        else:
            motion = False
            
    if 1 in magnetic_check_values:
        door_sensor_values = True
    return {
        "gas_sensor": {"data": gas_sensor_value, "density": gas_density},
        "potenciometer": grovepi.analogRead(potentiometer),
        "light_sensors": light_sensor_value,
        "motion_sensor": motion,
        "door_sensor": door_sensor_values,
        "switch_sensor": switch_sensor,
        "fire_sensor": GPIO.input(fire_sensor_GPIO),
        "temperature": temp,
        "humidity": hum,
        "lights": grovepi.digitalRead(red_led)
        }
def lightSensor(b):
    if b:
        grovepi.digitalWrite(red_led,1)
        grovepi.digitalWrite(green_led,1)
        grovepi.digitalWrite(blue_led,1)
    else:
        grovepi.digitalWrite(red_led,0)
        grovepi.digitalWrite(green_led,0)
        grovepi.digitalWrite(blue_led,0)
    
    return {"mainLight": not boolVal}

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
 
@app.route('/surname', methods=['POST'])
def updateSurname():
    value = request.get_json()['value']
    id_ = request.get_json()['id']
    query = """UPDATE users SET first_name='{0}' WHERE id={1}""".format(value, id_)
    cursor = db_connection.cursor()
    cursor.execute(query)
    db_connection.commit()
    return jsonify({'res': 'ok'})

@app.route('/lastname', methods=['POST'])
def updateLastname():
    value = request.get_json()['value']
    id_ = request.get_json()['id']
    query = """UPDATE users SET last_name='{0}' WHERE id={1}""".format(value, id_)
    cursor = db_connection.cursor()
    cursor.execute(query)
    db_connection.commit()
    return jsonify({'res': 'ok'})

@app.route('/email', methods=['POST'])
def updateEmail():
    value = request.get_json()['value']
    id_ = request.get_json()['id']
    query = """UPDATE users SET email='{0}' WHERE id={1}""".format(value, id_)
    cursor = db_connection.cursor()
    cursor.execute(query)
    db_connection.commit()
    return jsonify({'res': 'ok'})

@app.route('/password', methods=['POST'])
def updatePassword():
    value = hashlib.md5(request.get_json()['value'].encode()).hexdigest()
    id_ = request.get_json()['id']
    query = """UPDATE users SET password='{0}' WHERE id={1}""".format(value, id_)
    cursor = db_connection.cursor()
    cursor.execute(query)
    db_connection.commit()
    return jsonify({'res': 'ok'})
    

@app.route('/logIn')
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
        query = """INSERT INTO tableActions (userID, action, time) VALUES ('{0}', '{1}', '{2}');""".format(userID, action, time)
        print(query)
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
    rpi_sensors_grovepi = getSensorsValues()
    return jsonify({"conncection": rpi_sensors_grovepi})


@app.route('/video_feed', methods=['POST'])
def video_feed():
    global GLOBAL_CAMERA
    GLOBAL_CAMERA = request.get_json()['play']
    if GLOBAL_CAMERA:
        for video_frame in gen(VideoCamera()):
            socketio.emit('video_flask',{'data':  video_frame} )
    return Response(gen(VideoCamera()),
                      mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/sensorTest')
def sensorTest():
    motion_sensor_value = grovepi.digitalRead(pir_sensor)
    motion = False
    if motion_sensor_value==0 or motion_sensor_value==1:
        if motion_sensor_value==1:
            motion = True
        else:
            motion = False
    return jsonify({
            'motion': motion
        })
    
@app.route('/text_to_speech', methods=['POST'])
def textToSpeech():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="speechToTextCredentials.json"
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
    #with open('output.mp3', 'wb') as out:
        # out.write(response.audio_content)
    return Response(response.audio_content, mimetype="audio/mp3")
    

@socketio.on('connect')
def connectHandler():
    send('YES WORKING')

@socketio.on('join')
def connectHandler2(data):
    query = 'SELECT title, power FROM sensors'
    cursor = db_connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    db_connection.commit()
    dictionary = {}
    print('*****')
    data = tuple_to_dict(data, dictionary)
    rpi_sensors_grovepi = getSensorsValues()
    print(rpi_sensors_grovepi)
    retTable = []
   
    emit('update_sensors', rpi_sensors_grovepi)
    emit('update_actions', data)
    emit('update_table_data', retTable)

@socketio.on('update_sensors_start')
def update_sensors_start():
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
    query = 'UPDATE sensors SET power =' + str(data["bool"]).lower() +" WHERE id = " + str(data["id"])
    print(query)
    cursor = db_connection.cursor()
    cursor.execute(query)

    query = 'SELECT tb.action, tb.time, u.email from tableActions tb LEFT JOIN users u ON u.id=tb.userID ORDER BY tb.time ASC'
    print(query)
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

    lightSensor(data['bool'])
    
@socketio.on('update_sensors_grovepi_interval')
def update_sensors_interval():
    try:
        rpi_sensors_grovepi = getSensorsValues()
        print(rpi_sensors_grovepi)
        emit('update_sensors', rpi_sensors_grovepi, broadcast=True)
    except Exception as err:
        emit('error', )

@socketio.on('/expertal_system')
def expertalSystem(data):
    temp = data['temperature']
    lights = data['lights']
    windows = data['windows']
    climate = grovepi.digitalRead(switch)
    gas = data['gas']
    fire = data['fire']
    alarm = data['alarm']
    motion_sensor_value = grovepi.digitalRead(pir_sensor)
    motion = False
    
    if motion_sensor_value==0 or motion_sensor_value==1:
        if motion_sensor_value==1:
            motion = True
        else:
            motion = False
    
    system = StartSystem(temp=temp, climate=climate, windows=windows, motion=motion, lights=lights, gas=gas, fire=fire, alarm=alarm)
    retdata = system.getResult()
    emit('expertal_system', retdata)


#@socketio.on('binaryData')
#def startGoogleCloudStream(data):
#    requests = (speech.types.StreamingRecognizeRequest(audio_content=data))
#    responses = client.streaming_recognize(streaming_config, requests)
#    for result in responses:
#        if not response.results:
#            continue#
#
#        result = response.results[0]
#
#        if not result.alternatives:
#            continue
#
#       transcript = result.alternatives[0].transcript


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)