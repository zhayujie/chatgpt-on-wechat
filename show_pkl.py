import json
import pickle

with open("itchat.pkl", "rb") as file:
    data = pickle.load(file)
    print(json.dumps(data, indent=4))
