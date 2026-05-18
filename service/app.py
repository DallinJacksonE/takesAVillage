if True:
    from gevent import monkey
    monkey.patch_all()

import os
import json
from flask import Flask, jsonify
from flask_socketio import SocketIO

from api import api_bp
from sockets import register_socket_events
from game_manager import game_loop

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'config.json')

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        app.config['SECRET_KEY'] = config_data['flask']['secret_key']
except (FileNotFoundError, KeyError):
    app.config['SECRET_KEY'] = 'dev_fallback_key'

socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

# Register HTTP Routes
app.register_blueprint(api_bp)

# Register WebSocket Events
register_socket_events(socketio)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "API route not found"}), 404


# Start the game loop
socketio.start_background_task(game_loop, socketio)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True, use_reloader=True, port=5000)
