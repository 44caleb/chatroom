
from flask_session import Session
from flask import Flask, request, jsonify, session, render_template, redirect
from flask_socketio import SocketIO, join_room, send, emit
from uuid import uuid4
from datetime import datetime
# stored_data is a dictionary containing saved user information including messages
from data_store import file, stored_data, save_data

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "SDSDKFLNks12dwqasdsdf"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
socketio = SocketIO(app, manage_session=False)
Session(app)


# data is temporarily stored in this variables before json file storage

messages=[]

@app.route("/register", methods=["GET", "POST"])
def register_user():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return jsonify("Invalid username or password!")

    for user in stored_data["users"]:
        if user["username"] == username:
            return jsonify("Username already exists!")
            
    user_data = {"username": username, "password": password, "spaces": []}
    stored_data["users"].append(user_data)
    save_data(file, stored_data)
    session["user"] = username

    return redirect("/join_space")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "user" in session:
            return redirect("/chat")
        return render_template("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return jsonify("Invalid Username!")

        for user in stored_data["users"]:
            if username == user["username"]:
                if password != user["password"]:
                    return jsonify("Invalid Password!")

                session["user"] = username

                if user["spaces"] == []:
                    print("USER HAS NO SPACES........")
                    return redirect("/join_space")

                #set the user's default space and room upon logging in
                for space in stored_data["spaces"]:
                    if username in space["members"]:
                        session["latest_space"] = space["name"]
                        # set first room in space as default room
                        session["latest_room"] = space["rooms"][0]

                        return redirect("/chat")

        #username was not found
        return jsonify("Invalid Username!")
        

@app.route("/chat")
def chat():
    print("current user is", session["user"])
    for user in stored_data["users"]:
        if session["user"] == user["username"]:
            if user["spaces"] == []:
                return redirect("/join_space")
                
    user_spaces = []
    latest_space = session["latest_space"]
    #loads all spaces current user is a member of
    for space in stored_data["spaces"]:
        if session["user"] in space["members"]:
            user_spaces.append(space["name"])

    #loads all the rooms of the last space current user was in
    for space in stored_data["spaces"]:
        if space["name"] == latest_space:
            space_rooms = space["rooms"]
            break
    return render_template("chat_template.html", user_spaces=user_spaces, space_rooms=space_rooms)


@app.route("/join_space", methods=["GET", "POST"])
def join_space():

    if request.method == "GET":
        all_spaces = []
        for space in stored_data["spaces"]:
            all_spaces.append({"space_name": space["name"], "description": space["description"]})
        return render_template("join_space.html", spaces=all_spaces)

    if request.method == "POST":
        print("this is session user........", session["user"])
        space_name = request.get_json()
        if not space_name:
            abort(400, "Invalid space")

        for space in stored_data["spaces"]:
            if space_name == space["name"]:
                space["members"].append(session["user"])
                session["latest_space"] = space["name"]
                # set the room to the first room of that space
                session["latest_room"] = space["rooms"][0]
                
                #save space to the user's record
                for user in stored_data["users"]:
                    if session["user"] == user["username"]:
                        user["spaces"].append(space["name"])
                        # save to storage

                save_data(file, stored_data)
                return redirect("/chat")
        # space was not found
        abort(400, "Invalid space")



@app.route("/create_space", methods=["GET", "POST"])
def create_space():
    """route to create user defined spaces"""
    if request.method == "GET":
        return render_template("create_space.html")

    data = request.get_json()
    if not data:
        abort(404, "bad request")

    new_space = {}
    new_space["name"] = data["space_name"]
    new_space["members"] = [session["user"]]
    new_space["rooms"] = data["rooms"]
    new_space["description"] = data["space_description"]
    stored_data["spaces"].append(new_space)
    save_data(file, stored_data)
    return redirect("/chat")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

#.............helper routes......................
@app.route("/user_data")
def user_data():
    """gets user's last space and room"""
    room_messages = []
    for message in stored_data["messages"]:
        if session["latest_room"] == message["room"] and session["latest_space"] == message["space"]:
            room_messages.append(message)
    user_data = {"latest_space": session["latest_space"], "latest_room": session["latest_room"], "room_messages": room_messages}
    return jsonify(user_data)

@app.route("/check_space/<space_name>")
def check_space(space_name):
    """checks if user created space already exists"""
    print(space_name)
    for space in stored_data["spaces"]:
        if space_name == space["name"]:
            return jsonify(None)
    return jsonify(space_name)


@app.route("/get_rooms/<space>")
def get_rooms(space):
    """gets rooms for a space"""    
    user_rooms = []
    for user_space in stored_data["spaces"]:
        if user_space["name"] == space:
            user_rooms = user_space["rooms"]
    print(user_rooms)
    print(space)
    return jsonify(user_rooms)


@app.route("/get_messages/<space>")
def get_messages2(space):
    room_messages = []
    for message in stored_data["messages"]:
        if message["space"] == space:
            room_messages.append(message)
    return jsonify(room_messages)



@app.route("/get_messages2/<space>")
def get_messages(space):
    print('THIS IS THE OG MESSAGE LIST............', messages)
    room_messages = []
    for message in messages:
        if message["space"] == space:
            room_messages.append(message)
            print("I APPENDED THE MESSAGES......................")
    print("THESE ARE all THE MESSAGES IN THE API2 ROOM AFTER APPENDING", room_messages)
    return jsonify(room_messages)

@app.route("/add_messages", methods=["POST"])
def add_messages():
    
    print("IN ADD MESSAGES ENDPOINT...............")
    data = request.get_json()
    print(data)
    messages.append(data)
    stored_data["messages"].append(data)
    return jsonify(data)


@app.route("/get_all")
def get_all():
    return jsonify(stored_data)

#....................socket events.......................

@socketio.on("connect")
def connection():
    print(session["user"], "just connected ....................session id is",request.sid )
    for space in stored_data["spaces"]:
        if session["user"] in space["members"]:
            #if user is a member of that space connect to the rooms in the space
            for room in space["rooms"]:
                join_room(room)
    emit("connected", session["user"])

@socketio.on("send_message")
def send_message(data):
    # save the messages sent to storage
    time_sent = datetime.now().strftime("%m/%d/%Y   %I:%M %p")
    print(time_sent)
    stored_data["messages"].append({"message": data["message"], "room": data["room"],
                    "sender": data["sender"], "space": data["space"],
                    "time": time_sent})

    messages.append({"message": data["message"], "room": data["room"],
                    "sender": data["sender"], "space": data["space"],
                    "time": time_sent})
    print('I HAVE JUST STORED THE SENT MESSAGES.THIS IS THE UPDATED MESSAGE LIST..............', messages)
    save_data(file, stored_data)
    emit("broadcast_messages", {"message": data["message"], "sender": data["sender"], "time": time_sent}, to=data["room"])

@socketio.on("joined_space")
def joined_space(space):
    """updates the user's latest space (last connected space)"""
    session["latest_space"] = space

@socketio.on("joined_room")
def joined_room(data):
    print("these are all the message in total serverside...............", stored_data["messages"])
    room_messages=[]
    #load the messages from a particular room
    for message in stored_data["messages"]:
        if data["room"] == message["room"] and data["space"] == message["space"]:
            room_messages.append(message)

    #update latest room
    session["latest_room"] = data["room"]
    print()
    print("these are the room_messages on serverside...............", room_messages)
    emit("load_message", room_messages)


if __name__ == "__main__":
    socketio.run(app)