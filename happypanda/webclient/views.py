﻿"""views module."""
from flask import (render_template,)
from happypanda.webclient.main import happyweb, client, socketio
from happypanda.common import constants, exceptions, hlogger

log = hlogger.Logger(__name__)


def send_status(status, debug=constants.debug):
    socketio.emit("serv_connect", {"status": status, "debug": constants.debug})


def send_response(msg):
    data = client.communicate(msg)
    socketio.emit('response', data)


def reconnect():
    if not client.alive():
        try:
            client.connect()
        except exceptions.ClientError:
            log.exception("Failed to reconnect")

    if client.alive():
        send_status(client.alive())

    return client.alive()


@happyweb.before_first_request
def before_first_request():
    """before first request func."""
    try:
        client.connect()
    except exceptions.ClientError:
        log.exception("Could not establish connection on first try")
    send_status(client.alive())


@happyweb.route('/')
@happyweb.route('/index')
@happyweb.route('/library')
def library():
    return render_template('library.html')


@happyweb.route('/gallery/<int:id>')
def gallery_page(id=0):
    return render_template('library.html')


@happyweb.route('/artist/<int:id>')
def artist_page(id=0):
    pass


@happyweb.route('/apiview')
def api_view(page=0):
    return render_template('api.html')


@socketio.on('connect')
def serv_connect():
    "tests connection with server"
    if not client.alive():
        socketio.emit("reconnect", {})
    send_status(client.alive())


@socketio.on('reconnect')
def serv_reconnect(msg):
    "reconnect connection with server"
    reconnect()


@socketio.on('call')
def server_call(msg):
    try:
        send_response(msg)
    except exceptions.ServerDisconnectError:
        log.exception("Server disconnected, attempting to reconnect..")
        if reconnect():
            send_response(msg)
        else:
            socketio.emit("invalid", {})
    except exceptions.AuthError:
        socketio.emit("invalid", {})
