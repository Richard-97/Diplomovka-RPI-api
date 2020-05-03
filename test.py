from flask import Flask, jsonify, request, Response, abort, make_response
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send, emit
import time
from cameraModule import VideoCamera
app = Flask(__name__)
app.config['SECRET_KEY'] = 'diploma-seceret'

CORS(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/logIn')
def main():
    return jsonify({'test': 'OK'})

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
    print('VIDEO START')
    global GLOBAL_CAMERA
    GLOBAL_CAMERA = request.get_json()['play']
    if GLOBAL_CAMERA:
        for video_frame in gen(VideoCamera()):
            socketio.emit('video_flask',{'data':  video_frame} )
            
    return Response(gen(VideoCamera()),
                      mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)