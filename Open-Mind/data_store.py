import json

file = "storage.json"

# loads the stored_data
try:
    with open(file, "r") as f:
        stored_data = json.load(f)

except FileNotFoundError:
    stored_data = {"messages": [],
                    "spaces": [{"name": "Programming", "description": "For all who love programming. All programming languages welcome (lol except javascript)", "members": ["caleb", "user1"], "rooms": ["room 1", "room 2"]},
                                {"name": "Film Fellas", "description": "Movie buffs unite!! We talk movies of all genres", "members": ["caleb", "user1"], "rooms": ["room 3"]},
                                {"name": "Backend-Boyz (and girls)", "description": "Backend technologies, languages, frameworks, you name it ", "members": ["caleb", "user1"], "rooms": ["room 3"]},
                                {"name": "ALX Projects", "description": "Offering help on ALX projects, we know how difficult they can be", "members": ["caleb", "user1"], "rooms": ["Simple Shell", "AirBnB (Console)", "Monty", "Search Algorithms"]}],
                    "users": [{"username": "caleb", "password": "caleb", "spaces":["Programming", "Film Fellas", "Backend-Boyz", "ALX Projects"]}]}


def save_data(file, data):
    """function to store data in the json file"""
    with open(file, "w") as f:
        json.dump(stored_data, f)