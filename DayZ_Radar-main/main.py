# Standard Libraries
import eventlet
import logging
import os
import signal
from time import time
# Third-Party Libraries
from flask import Flask, render_template, request
from flask_socketio import SocketIO

# Application-specific imports
from game import game

# Monkey patch for eventlet
eventlet.monkey_patch()

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('flask_app')
app.config['DEBUG'] = False
socketio = SocketIO(app, cors_allowed_origins='*', async_mode="eventlet", pingTimeout=60000, pingInterval=25000)

logging.basicConfig(format='%(message)s', level=logging.INFO)  # Added timestamp
logging.getLogger("werkzeug").disabled = True

# Global Variables
stop_flag = eventlet.event.Event()
ip_to_sid = {}

def main_thread(game):
    print('Starting main thread.......')
    emit = socketio.emit
    game.player_ptr = game.get_local_player()
    game.get_all_entities()
    while not stop_flag.wait(0):
        eventlet.sleep(0.002)
        players = game.process_entities()
        if not players:
            print(f'No players found. Retrying...')
            game.get_all_entities()
            eventlet.sleep(10)
            continue
        emit('updateData', players)

def get_players_thread(game):
    while not stop_flag.wait(0):
        eventlet.sleep(120)
        game.entity_type_cache = {}
        game.visual_address_cache = {}
        game.near_ptr_cache = None
        game.far_ptr_cache = None
        game.get_all_entities()
        if not game.all_entities:
            eventlet.sleep(30)
            continue

@app.before_request
def log_unexpected_routes():
    explicit_routes = {"/", "/static/css/app.css", "/static/data.js", "/favicon.ico"}
    if request.path not in explicit_routes:
        logging.info(f"IP:{request.remote_addr} Accessed at {request.path}")

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('connect')
def handle_connect():
    ip = request.remote_addr
    old_sid = ip_to_sid.get(ip)

    # If there's an older connection from the same IP, notify it to disconnect
    if old_sid:
        socketio.emit('force_disconnect', room=old_sid)

    # Store the new connection's session ID
    ip_to_sid[ip] = request.sid

@socketio.on('drawing')
def handle_drawing(data):
    socketio.emit('drawing', data, broadcast=True, include_self=False)

@socketio.on('clearCanvas')
def handle_clear_canvas():
    socketio.emit('clearCanvas', broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    ip = request.remote_addr
    if ip in ip_to_sid and ip_to_sid[ip] == request.sid:
        del ip_to_sid[ip]
    
def shutdown_server(signal, frame):
    print('Shutting down server...')
    stop_flag.send(None)
    socketio.stop()
    game.vmm.close()
    exit(0)

signal.signal(signal.SIGINT, shutdown_server)

if __name__ == '__main__':
    eventlet.sleep(3)
    eventlet.spawn(main_thread, game)
    eventlet.sleep(3)
    eventlet.spawn(get_players_thread, game)
    socketio.run(app, port=8080, host='192.168.10.30', use_reloader=False)