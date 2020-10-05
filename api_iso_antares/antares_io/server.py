from flask import Flask, request

from api_iso_antares.engine.url import UrlEngine

application = Flask(__name__)

engine = UrlEngine()


@application.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def home(path: str):
    return engine.apply(path)


if __name__ == '__main__':
    application.run(debug=False, host='0.0.0.0', port=8080)