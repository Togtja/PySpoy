import os, json, webbrowser, threading #Default lib
import base64, time, urllib.parse
import requests #External libs
from pynput import keyboard 

import webserver # Own lib

#TODO: Make it a class
class PySpoy():
    pass

player_url =  	"https://api.spotify.com/v1/me/player/"

with open(".config") as conf_file:
    clientID = conf_file.read()

current_r = requests.Session()

rederect = "http://localhost:"+ str(webserver.PORT)
access = "user-modify-playback-state"

auth_url = "https://accounts.spotify.com/authorize?client_id="+ clientID +"&response_type=code&redirect_uri=" + urllib.parse.quote(rederect) +"&scope=" + access

try:
    t = threading.Thread(target=webserver.runServer, daemon=True)
    t.start()
    print("started server?")
except Exception as e:
    print("Off", e)

webbrowser.open(auth_url)

#TODO: Add timeout
while(not os.path.exists(webserver.FILE)):
    time.sleep(1)
    pass

with open(webserver.FILE, "r") as f:
    authToken = f.read()
os.remove(webserver.FILE)
webserver.closeServer()

payload = {
    "grant_type": "authorization_code",
    "code": authToken,
    "redirect_uri" : rederect,
    "client_id":     clientID,
    "client_secret": "Secret!"
}

res = current_r.post("https://accounts.spotify.com/api/token", data=payload)


access_token = res.json()["access_token"]
current_r.headers.update({"Authorization":"Bearer " +  access_token})

#TODO: make UI for this
keybind = {"Play/Pause": [{keyboard.Key.alt_gr, keyboard.Key.up}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.up}]}
cur_key = set()

def press_comb(key, binding : str):
    if key not in cur_key:
        cur_key.add(key)
    for combo in keybind[binding]:
        if (combo == cur_key):
            return True
        
    return False

def on_press(key : keyboard.Key):
    if(key == keyboard.Key.esc):
        return False
    if(key.__str__() == "<65027>"):
        key = keyboard.Key.alt_gr

    print("The key:", key.__str__())
    if(press_comb(key, "Play/Pause")):
        playPause(current_r)

def on_release(key):
    if(key.__str__() == "<65027>"):
        key = keyboard.Key.alt_gr
    if key in cur_key:
        cur_key.remove(key)
        
#TODO: Find a better way to know if state is play or pause, to minimize calls
def playPause(ses : requests.Session):
    code = ses.put(url=player_url+"play")
    print("play code: ", code.status_code)
    if(code.status_code == 403):
        code = ses.put(url=player_url+"pause")
        print("pause code:", code.status_code)


if __name__ == "__main__":
    with keyboard.Listener(on_press=on_press, on_release=on_release) as l1:
        l1.join()
    """
    with keyboard.GlobalHotKeys({
        '<65027>+p': test
    }) as target:
        target.join()s
    """
        
    #print(req.json())

