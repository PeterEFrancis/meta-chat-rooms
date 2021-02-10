from flask import Flask, render_template, url_for, redirect, request, send_from_directory, jsonify, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku
import re
import random
import html
import os
import sys
import random as r
import json
import random
import time
import hashlib
from base64 import b64encode
from os import urandom

from flask_socketio import SocketIO, send, join_room, leave_room



app = Flask(__name__)
app.secret_key = "ZpWNmtZBqTeLrJu6SWx6BueHGKWYxfD4fLz7CKTfcerZj4ffVhEG"

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/meta-chat-rooms'
heroku = Heroku(app)
app.config['SECRET_KEY'] = 'secret!'


socketio = SocketIO(app)



@app.route('/static/<string:path>')
def static_path(path):
    return app.send_static_file(path)






#      _       _        _
#   __| | __ _| |_ __ _| |__   __ _ ___  ___
#  / _` |/ _` | __/ _` | '_ \ / _` / __|/ _ \
# | (_| | (_| | || (_| | |_) | (_| \__ \  __/
#  \__,_|\__,_|\__\__,_|_.__/ \__,_|___/\___|
#


db = SQLAlchemy(app)

class Room(db.Model):
    __tablename__ = "rooms"
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    pods = db.Column(db.Text)
    name = db.Column(db.Text)
    host = db.Column(db.Text)
    chatstream = db.Column(db.Text)
    date = db.Column(db.Text)
    open = db.Column(db.Boolean)
    custom_html = db.Column(db.Text)
    unassigned_id = db.Column(db.Text)

    def __init__(self, host):
        print(__name__)
        self.pods = '[]'
        self.name = 'New Room'
        self.host = host
        self.chatstream = '[]'
        self.date = time.asctime(time.localtime(time.time()))
        self.open = True
        self.custom_html = ''
        self.unassigned_id = ''

    def get_pods(self):
        return eval(self.pods)
    def get_pod_dict(self):
        dict = {}
        for pod_id in self.get_pods():
            dict[pod_id] = {
                'name': get_pod(pod_id).name,
                'players': get_pod(pod_id).get_players()
            }
        return {
            'unassigned_id': self.unassigned_id,
            'dict': dict
        }
    def add_pod(self, pod_id):
        pod_id = int(pod_id)
        pods = self.get_pods()
        pods.append(pod_id)
        self.pods = str(pods)
        db.session.commit()
    def remove_pod(self, pod_id):
        if pod_id == self.unassigned_id:
            raise "Cannot remove the Unassigned Pod."
        else:
            pod_id = int(pod_id)
            pods = self.get_pods()
            pods.remove(pod_id)
            self.pods = str(pods)
            db.session.commit()
    def has_pod(self, pod_id):
        pod_id = int(pod_id)
        return pod_id in self.get_pods()

    def add_player(self, pod_id, playername):
        if not self.has_pod(pod_id):
            raise "you dont have access to this pod"
        elif self.has_player(playername):
            raise "this playername already is already taken"
        get_pod(pod_id).add_player(playername)
    def remove_player(self, playername):
        for pod_id in self.get_pods():
            pod = get_pod(pod_id)
            if pod.has_player(playername):
                pod.remove_player(playername)
    def has_player(self, playername):
        for pod_id in self.get_pods():
            if get_pod(pod_id).has_player(playername):
                return True
        return False


    def set_open(self, open):
        self.open = open
        db.session.commit()

    def set_name(self, name):
        self.name = name
        db.session.commit()

    def set_custom_html(self, custom_html):
        self.custom_html = custom_html
        db.session.commit()

    def get_chatstream(self):
        return eval(self.chatstream)
    def send(self, sender_id, sender_name, message, recipient_id, recipient_name):
        cs = self.get_chatstream()
        cs.append({
            'sender_name': sender_name,
            'sender_id': sender_id,
            'message': message,
            'recipient_id':recipient_id,
            'recipient_name':recipient_name,
            'time': time.time()
        })
        self.chatstream = str(cs)
        db.session.commit()

    def move_player(self, playername, pod_id):
        if self.has_player(playername):
            self.remove_player(playername)
            self.add_player(pod_id, playername)
        else:
            raise f"Player {playername} is not in this room."

    def which_pod(self, playername):
        for pod_id in self.get_pods():
            print(pod_id)
            if get_pod(pod_id).has_player(playername):
                return pod_id
        return False

def is_room(room_id):
    room_id = int(room_id)
    return len(list(db.session.query(Room).filter(Room.id == room_id))) != 0

def get_room(room_id):
    room_id = int(room_id)
    return db.session.query(Room).filter(Room.id == room_id)[0]

def delete_room(room_id):
    room_id = int(room_id)
    # delete all pods in the room
    for pod_id in self.get_pods():
        delete_pod(get_pod(pod_id))
    # remove room from host
    for user in db.session.query(User):
        if room_id in user.get_rooms():
            user.remove_game(room_id)
            break
    # delete the Room object
    db.session.query(Room).filter(Room.id == room_id).delete()
    db.session.commit()

def new_room(host):
    room = Room(host)
    db.session.add(room)
    db.session.commit()

    pod = Pod(room.id, 'unassigned')
    db.session.add(pod)
    db.session.commit()

    room.unassigned_id = str(pod.id)
    db.session.commit()

    room.add_pod(pod.id)

    return room

def new_pod(room_id):
    room = get_room(room_id)
    poss_nums = list(filter(lambda x: x.isdigit(), map(lambda x: get_pod(x).name.split(" ")[-1], room.get_pods())))
    next_num = 1
    if len(poss_nums) != 0:
        nums = list(map(lambda x: int(x), poss_nums))
        print(nums)
        while next_num in nums:
            next_num += 1
    pod = Pod(room_id, f'New Pod {next_num}')
    db.session.add(pod)
    db.session.commit()
    room.add_pod(pod.id)


class Pod(db.Model):
    __tablename__ = "pods"
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    room = db.Column(db.Text) # (parent)
    players = db.Column(db.Text)
    pods = db.Column(db.Text)
    name = db.Column(db.Text)
    chatstream = db.Column(db.Text)

    def __init__(self, room_id, name):
        self.room = room_id
        self.players = '[]'
        self.pods = '[]'
        self.name = name
        self.chatstream = '[]'

    def get_players(self):
        return eval(self.players)
    def add_player(self, player):
        players = self.get_players()
        players.append(player)
        self.players = str(players)
        db.session.commit()
    def remove_player(self, player):
        players = self.get_players()
        players.remove(player)
        self.players = str(players)
        db.session.commit()
    def has_player(self, player):
        return player in self.get_players()

    def get_chatstream(self):
        return eval(self.chatstream)

    def set_name(self, name):
        if self.id == get_room(self.room).unassigned_id:
            raise "Cannot change the 'unassigned' pod name."
        else:
            self.name = name
            db.session.commit()

    def send(self, sender, recipient, message):
        cs = self.get_chatstream()
        cs.append({
            'sender_id': sender,
            'sender_name': sender,
            'recipient_id': recipient,
            'recipient_name': recipient,
            'message': message,
            'time': time.time()
        })
        self.chatstream = str(cs)
        db.session.commit()

def is_pod(pod_id):
    pod_id = int(pod_id)
    return len(list(db.session.query(Pod).filter(Pod.id == pod_id))) != 0

def get_pod(pod_id):
    pod_id = int(pod_id)
    return db.session.query(Pod).filter(Pod.id == pod_id)[0]

def delete_pod(pod_id):
    pod_id = int(pod_id)
    pod = get_pod(pod_id)
    if pod.id == get_room(pod.room).unassigned_id:
        raise "Cannot delete the 'unassigned' pod."
    else:
        db.session.query(Pod).filter(Pod.id == pod_id).delete()
        db.session.commit()



class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    salt = db.Column(db.Text)
    hashed_password = db.Column(db.Text)
    rooms = db.Column(db.Text)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)
        self.rooms = '[]'

    def set_password(self, password):
        self.salt = get_salt(12)
        self.hashed_password = SHA1(password + self.salt)
        db.session.commit()

    def get_rooms(self):
        return eval(self.rooms)
    def add_room(self, room_id):
        rooms = self.get_rooms()
        rooms.append(room_id)
        self.rooms = str(rooms)
        db.session.commit()
    def remove_room(self, room_id):
        rooms = self.get_rooms()
        rooms.remove(room_id)
        self.rooms = str(rooms)
        db.session.commit()
    def has_room(self, room_id):
        return int(room_id) in self.get_rooms()


def is_user(username):
    return len(list(db.session.query(User).filter(User.username == username))) != 0

def get_user(username):
    return db.session.query(User).filter(User.username == username)[0]

def delete_user(username):
    # delete all of the user's rooms
    for room_id in get_user(username).get_rooms():
        delete_room(room_id)
    # delete user object
    db.session.query(User).filter(User.username == username).delete()
    db.session.commit()








#  _          _
# | |__   ___| |_ __   ___ _ __ ___
# | '_ \ / _ | | '_ \ / _ | '__/ __|
# | | | |  __| | |_) |  __| |  \__ \
# |_| |_|\___|_| .__/ \___|_|  |___/
#              |_|





def SHA1(string):
    return hashlib.sha1(string.encode()).hexdigest()

def get_salt(n):
    return b64encode(urandom(n)).decode('utf-8')














#                  _             _
#   ___ ___  _ __ | |_ ___ _ __ | |_
#  / __/ _ \| '_ \| __/ _ | '_ \| __|
# | (_| (_) | | | | ||  __| | | | |_
#  \___\___/|_| |_|\__\___|_| |_|\__|



def get_account_bar():
    username = ''
    if 'username' in session:
        username = session['username']
    return render_template(
        'account_bar.html',
        loggedin = ('username' in session),
        username = username,
        rooms = db.session.query(Room).filter(Room.host == username)
    )


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', account_bar=get_account_bar())



@app.route('/room/<string:room_id>')
def room_root(room_id):
    if not is_room(room_id):
        return "no room found."
    room = get_room(room_id)
    if session_is_host(room_id) or session_is_admin():
        session['room'] = room_id
        return render_template(
            'room.html',
            account_bar = get_account_bar(),
            username=session['username'],
            room_id = room.id
        )
    if session_in_room(room_id):
        pid, playername = session['room-' + room_id]
        if room.has_player(playername):
            return redirect(f'/room/{room_id}/pod/{room.which_pod(playername)}')
    return redirect(f'/join/{room_id}')


@app.route('/room/<string:room_id>/pod/<string:pod_id>')
def room_pod(room_id, pod_id):
    if not is_room(room_id):
        return "No room found."
    if not is_pod(pod_id):
        return redirect(f'/room/{room_id}')
    room = get_room(room_id)
    pod = get_pod(pod_id)
    if session_in_room(room_id):
        old_pod_id, playername = session['room-' + room_id]
        if room.has_pod(pod_id) and room.has_player(playername):
            session['room'] = room_id
            if pod.has_player(playername):
                session['pod'] = pod_id
                session['room-' + room_id] = [pod_id, playername]
                return render_template(
                    'pod.html',
                    account_bar = get_account_bar(),
                    playername=playername,
                    room_id=room_id,
                    pod_id=pod_id,
                    pod_name=pod.name
                )
            else:
                # in a different pod
                return redirect(f'/room/{room_id}/pod/{room.which_pod(playername)}')
        else:
            # no longer in the room
            session.pop('room-' + room_id, None)
    if session_is_host(room_id) or session_is_admin():
        return redirect(f'/room/{room_id}')
    return redirect('/join/' + room_id)





@app.route('/join')
def join_blank():
    return render_template('join.html', account_bar=get_account_bar(), code="")


@app.route('/join/<string:room_id>')
def join(room_id):
    if not is_room(room_id):
        return redirect('/join')
    room = get_room(room_id)
    # if the user is the host of the room
    if session_is_host(room_id) or session_is_admin():
        return redirect(f'/room/{room_id}')
    if session_in_room(room_id):
        pod_id, playername = session['room-' + room_id]
        if room.has_pod(pod_id) and room.has_player(playername):
            return redirect(f'/room/{room_id}/pod/{pod_id}')
        else:
            # no longer in the room
            session.pop('room-' + room_id, None)
    return render_template('join.html', account_bar=get_account_bar(), room_id=room_id)








#             _   _
#   __ _  ___| |_(_) ___  _ __  ___
#  / _` |/ __| __| |/ _ \| '_ \/ __|
# | (_| | (__| |_| | (_) | | | \__ \
#  \__,_|\___|\__|_|\___/|_| |_|___/


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    if not username.isalnum():
        return jsonify({'success':'false','error':'Username must contain only alphanumeric characters.'})
    if len(list(db.session.query(User).filter(User.username == request.form['username']))) != 0:
        return jsonify({'success':'false','error':'A user with this username already exists.'})
    db.session.add(User(request.form['username'],request.form['password']))
    db.session.commit()
    return jsonify({'success':'true'})


@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' not in session:
        return jsonify({'success':'false', 'error':"You are not logged in."})
    if not is_user(session['username']):
        return jsonify({'success':'false', 'error':"You are logged into a user that no longer exists."})
    get_user(session['username']).set_password(request.form['password'])
    return jsonify({'success':'true'})


@app.route('/login', methods=['POST'])
def login():
    if not is_user(request.form['username']):
        return jsonify({'success':'false','error':'No user with this username exists.'})
    user = get_user(request.form['username'])
    if user.hashed_password != SHA1(request.form['password'] + user.salt):
        return jsonify({'success':'false','error':'The entered password is incorrect.'})
    session['username'] = request.form['username']
    return jsonify({'success':'true'})


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success':'true'})





@app.route('/new_room', methods=['POST'])
def _new_room():
    if 'username' not in session:
        return jsonify({'success':'false', 'error':"You're not logged in."})

    room = new_room(session['username'])

    if not is_user(session['username']):
        return jsonify({'success':'false', 'error':"You are logged into a user that no longer exists."})

    get_user(session['username']).add_room(room.id)
    return jsonify({'success':'true', 'room_id':room.id})





@app.route('/join_room', methods=['POST'])
def join_chat_room():
    room_id = request.form['room_id']
    if not is_room(room_id):
        return jsonify({'success':'false', 'error':'No room found.'})
    room = get_room(room_id)
    if not room.open:
        return jsonify({'success':'false', 'error':'This room is not open to be joined.'})
    pod_id = 0
    if session_in_room(room_id):
        pod_id, playername = session['room-' + room_id]
        if room.has_player(playername):
            return jsonify({'success':'false', 'error':f'You are already in this room with name <u>{playername}</u>.<br><br>Click <a href="/room/{room_id}">here</a> to enter.'})

    if room.has_player(request.form['player']):
        return jsonify({'success':'false', 'error':'This name is already in use. Try another!'})

    unassigned_id = str(get_pod(room.get_pods()[0]).id)
    session['room'] = room_id
    session['room-' + room_id] = [unassigned_id, request.form['player']]

    room.add_player(unassigned_id, request.form['player'])
    socketio.emit('update pods', room='room-'+room_id)
    socketio.emit('update players', room='pod-'+unassigned_id)
    return jsonify({'success':'true', 'room_id':room_id})


@app.route('/leave_room', methods=['POST'])
def leave_room():
    room_id = request.form['room_id']
    if not is_room(room_id):
        return jsonify({'success':'false', 'error':'No room found.'})
    room = get_room(room_id)
    if session_in_room(room_id):
        pod_id, playername = session['room-' + room_id]
        if room.has_player(playername):
            room.remove_player(playername)
    session.pop('room-' + room_id, None)
    session.pop('room', None)
    session.pop('pod', None)
    socketio.emit('update pods', room='room-' + room_id)
    socketio.emit('update players', room='pod-'+pod_id)
    return jsonify({'success':'true'})



@app.route('/leave_pod', methods=['POST'])
def leave_pod():
    room_id = request.form['room_id']
    if not is_room(room_id):
        return jsonify({'success':'false', 'error':'No room found.'})
    room = get_room(room_id)
    if session_in_room(room_id):
        pod_id, playername = session['room-' + room_id]
        if room.has_player(playername):
            room.move_player(playername, room.unassigned_id)
            session['room-' + room_id] = [room.unassigned_id, playername]
            session['pod'] = room.unassigned_id
    socketio.emit('update pods', room='room-' + room_id)
    socketio.emit('update players', room='pod-'+pod_id)
    return jsonify({'success':'true'})










#    __ _  ___ ___ ___ ___ ___
#   / _` |/ __/ __/ _ / __/ __|
#  | (_| | (_| (_|  __\__ \__ \
#   \__,_|\___\___\___|___|___/


@app.route('/room_access/<string:function>', methods=['POST'])
def room_access(function):
    if 'room' not in session:
        return jsonify({'success':'false', 'error':"You're not in a room."})
    room_id = request.form['room_id']
    if session['room'] != room_id:
        return jsonify({'success':'false', 'error':"You're not in this room."})
    if not is_room(request.form['room_id']):
        return jsonify({'success':'false', 'error':"This room doesn't exist."})

    room = get_room(request.form['room_id'])

    if function == "get_room_chatstream":
        id = request.form['id']
        return jsonify({
            'success':'true',
            'chatstream':list(
                filter(
                    lambda chat :
                        chat['recipient_id'] == 'everyone'
                        or chat['recipient_id'] == id
                        or chat['sender_id'] == id,
                    room.get_chatstream()
                )
            )
        })
    elif function == 'room_send':
        room.send(
            sender_id=request.form['sender_id'],
            sender_name=request.form['sender_name'],
            message=request.form['message'],
            recipient_id=request.form['recipient_id'],
            recipient_name=request.form['recipient_name']
        )
        socketio.emit('update room chat', room='room-'+room_id)
        return jsonify({'success':'true'})
    elif function == "get_room_name":
        return jsonify({'success':'true', 'name':room.name})
    elif function == 'get_pod_name':
        return jsonify({'success':'true', 'name':get_pod(session['room-' + room_id][0]).name})
    elif function == "get_custom_html":
        return jsonify({'success':'true', 'custom_html':room.custom_html})
    elif function == "get_pod_dict":
        return jsonify({'success':'true', 'pods':room.get_pod_dict()})

    # pod id supplied
    if 'pod_id' in request.form:
        if not is_pod(request.form['pod_id']):
            return jsonify({'success':'false', 'error':"This pod doesn't exist."})
        if not room.has_pod(request.form['pod_id']):
            return jsonify({'success':'false', 'error':"You don't have this pod."})

        pod_id = request.form['pod_id']
        pod = get_pod(pod_id)

        if function == "pod_send":
            p, playername = session['room-' + room_id]
            pod.send(
                sender=playername,
                recipient=request.form['recipient'],
                message=request.form['message']
            )
            socketio.emit('update pod chat', room='pod-'+pod_id)
            return jsonify({'success':'true'})
        elif function == "get_pod_chatstream":
            id = request.form['id']
            return jsonify({
                'success':'true',
                'chatstream':list(
                    filter(
                        lambda chat :
                            chat['recipient_id'] == 'everyone'
                            or chat['recipient_id'] == id
                            or chat['sender_id'] == id,
                        pod.get_chatstream()
                    )
                )
            })
        elif function == "get_players":
            return jsonify({'success':'true', 'players':pod.get_players()})


    return jsonify({'success':'false', 'error':"The function you tried to access doesn't exist."})



@app.route('/host_access/<string:function>', methods=['POST'])
def host_access(function):
    if 'username' not in session:
        return jsonify({'success':'false', 'error':"You are not logged in."})
    if not is_user(session['username']):
        return jsonify({'success':'false', 'error':"You are logged into a user that no longer exists."})
    room_id = request.form['room_id']
    if not is_room(room_id):
        return jsonify({'success':'false', 'error':'No room Found.'})
    room = get_room(room_id)
    if (not get_user(session['username']).has_room(room_id)) and session['username'] != 'admin':
        return jsonify({'success':'false', 'error':"You don't have access to edit this game."})

    if function == "get_open":
        return jsonify({'success':'true', 'open':room.open})
    elif function == "set_open":
        room.set_open(bool(int(request.form['open'])))
        socketio.emit('update open', room='room-'+room_id)
        return jsonify({'success':'true', 'open':'true' if room.open else 'false'})
    elif function == "delete_room":
        delete_room(room_id)
        socketio.emit('reload', room='room-'+room_id)
        return jsonify({'success':'true'})
    elif function == "change_room_name":
        room.set_name(request.form['name'])
        socketio.emit('update room name', room='room-'+room_id)
        return jsonify({'success':'true'})
    elif function == "change_custom_html":
        room.set_custom_html(request.form['custom_html'])
        socketio.emit('update custom_html', room='room-'+room_id)
        return jsonify({'success':'true'})
    elif function == "new_pod":
        new_pod(room_id)
        socketio.emit('update pods', room='room-'+room_id)
        return jsonify({'success':'true'})

    # pod id supplied
    if 'pod_id' in request.form:
        if not is_pod(request.form['pod_id']):
            return jsonify({'success':'false', 'error':"This pod doesn't exist."})
        if not room.has_pod(request.form['pod_id']):
            return jsonify({'success':'false', 'error':"You don't have this pod."})

        pod_id = request.form['pod_id']
        pod = get_pod(pod_id)

        if function == "change_pod_name":
            pod.set_name(request.form['pod_name'])
            socketio.emit('update pods', room='room-'+room_id)
            socketio.emit('update pod name', room='pod-'+pod_id)
            return jsonify({'success':'true'})
        elif function == "move_player":
            old_pod_id = request.form['old_pod_id']
            playername = request.form['playername']
            room.move_player(playername, pod_id)
            socketio.emit('redirect', {
                'player':playername,
                'link':f'/room/{room_id}/pod/{pod_id}'
            }, room='pod-'+old_pod_id)
            socketio.emit('update pods', room='room-'+room_id)
            socketio.emit('update players', room='pod-'+old_pod_id)
            socketio.emit('update players', room='pod-'+pod_id)
            return jsonify({'success':'true'})
        elif function == "delete_pod":
            players = pod.get_players()
            for playername in players:
                room.move_player(playername, room.unassigned_id)
            room.remove_pod(pod_id)
            socketio.emit('reload', {'players':players}, room='pod-'+pod_id)
            socketio.emit('update pods', room='room-'+room_id)
            return jsonify({'success':'true'})
        elif function == "remove_player":
            playername = request.form['playername']
            room.remove_player(playername)
            socketio.emit('redirect', {
                'player':playername,
                'link':'/'
            }, room='pod-'+pod_id)
            socketio.emit('update pods', room='room-'+room_id)
            socketio.emit('update players', room='pod-'+pod_id)
            return jsonify({'success':'true'})

    return jsonify({'success':'false', 'error':"The function you tried to access doesn't exist."})















 #  ____                _          _
 # / ___|   ___    ___ | | __ ___ | |_
 # \___ \  / _ \  / __|| |/ // _ \| __|
 #  ___) || (_) || (__ |   <|  __/| |_
 # |____/  \___/  \___||_|\_\\___| \__|



@socketio.on('join room')
def on_join_room(data):
    join_room('room-' + data['room_id']);


@socketio.on('leave room')
def on_leave_room(data):
    leave_room('player-' + data['room_id'])


@socketio.on('join pod')
def join_pod(data):
    join_room('pod-' + data['pod_id'])


@socketio.on('leave pod')
def on_leave_room(data):
    leave_room('player-' + data['pod_id'])






#                   _
#  ___  ___ ___ ___(_) ___  _ __
# / __|/ _ / __/ __| |/ _ \| '_ \
# \__ |  __\__ \__ | | (_) | | | |
# |___/\___|___|___|_|\___/|_| |_|



@app.route('/session')
def sess():
    return "<style>table,th,tr,td{border: 1px solid black;}</style><table><tr><th colspan='2'>Session</th><tr>" + "</tr><tr>".join(f"<td>{el}</td><td>{session[el]}</td>" for el in session) + "</tr></table>"



def session_is_host(room_id):
    if 'username' in session:
        if is_user(session['username']):
            if get_user(session['username']).has_room(room_id):
                return True
    return False

def session_is_admin():
    return 'username' in session and session['username'] == 'admin'


def session_in_room(room_id):
    return 'room-' + room_id in session





#            _           _
#   __ _  __| |_ __ ___ (_)_ __
#  / _` |/ _` | '_ ` _ \| | '_ \
# | (_| | (_| | | | | | | | | | |
#  \__,_|\__,_|_| |_| |_|_|_| |_|


@app.route('/initialize')
def initialize():
    db.drop_all()
    db.create_all()
    users = [
        ['a','7he9J08ghw9hr','f998a13487d4f1b7f273e80716fcebc02f1d69fd'],
        ['b','9f7Jge5jr6jSRj','b09007d934e774ab5a59194b52676503a157dfbd'],
        ['admin','Kg63KSRjsr5js','ff92bed28c618a2b17303ffefa5e40fd2e3c286e']
    ]
    for username,salt,hash in users:
        u = User(username,'temp')
        u.salt = salt
        u.hashed_password = hash
        db.session.add(u)
        db.session.commit()
    return 'Initialization is done.'




@app.route('/admin/<string:s>', methods=['POST', 'GET'])
def admin(s):
    if not is_user('admin'):
        return redirect('/')
    if 'username' not in session or session['username'] != 'admin':
        return 'Access denied.', 403

    if s == 'access' and request.method == 'GET':
        return render_template('admin.html', account_bar=get_account_bar(), all_rooms=db.session.query(Room),  all_pods=db.session.query(Pod), all_users=db.session.query(User))

    if s == 'delete_user' and request.method == 'POST':
        username = request.form['username']
        if not is_user(username):
            print(username)
            return jsonify({'success':'false', 'error':'no username exists'})
        if username == 'admin':
            return jsonify({'success':'false', 'error':"You can't delete the admin account."})
        delete_user(username)
        return jsonify({'success':'true'})


    return 'Access denied.', 403










if __name__ == "__main__":
    app.debug = True
    # app.run()
    socketio.run(app)
