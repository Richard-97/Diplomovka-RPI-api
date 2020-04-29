from flask import Flask, jsonify, request, Response, abort, make_response

app = Flask(__name__)

@app.route('/logIn')
def main():
    return jsonify({'test': 'OK'})

if __name__ == '__main__':
    app.run(host='0.0.0.0')