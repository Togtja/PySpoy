import json, webbrowser #Default lib
import requests #External libs
from pynput import keyboard 

#TODO: Make it a class
clientID = None
player_url =  	"https://api.spotify.com/v1/me/player/"
with open(".config") as conf_file:
    clientID = conf_file.read()

current_r = requests.Session()
current_r.headers.update({"Accept":"application/json"})
current_r.headers.update({"Content-Type":"application/json"})
client_payload={
    "client_id" : clientID,
    "response_type" : "code",
    "redirect_uri" : "https://google.com"
}
dump = json.dumps(client_payload)
print(dump)
auth_url = "https://accounts.spotify.com/authorize?client_id="+clientID+"&response_type=code&redirect_uri=https%3A%2F%2Fexample.com%2Fcallback"+"&scope=user-modify-playback-state"
webbrowser.open(auth_url)

keybind = {"Play": [{keyboard.Key.alt_gr, keyboard.Key.up}],
            "Pause": [{keyboard.Key.alt_gr, keyboard.Key.down}]}
cur_key = set()

def press_comb(key, binding : str):
    if key not in cur_key:
        cur_key.add(key)
    for combo in keybind[binding]:
        if (combo == cur_key):
            return True
        
    return False

def on_press(key : keyboard.Key):
    if(key.__str__() == "<65027>"):
        key = keyboard.Key.alt_gr

    print("The key:", key.__str__())
    if(press_comb(key, "Play")):
        play(current_r)
    if(press_comb(key, "Pause")):
        pause(current_r)

def on_release(key):
    if(key.__str__() == "<65027>"):
        key = keyboard.Key.alt_gr
    if key in cur_key:
        cur_key.remove(key)
        

def play(ses : requests.Session):
    code = ses.put(url=player_url+"play")
    print("return code:", code.status_code)

def pause(ses: requests.Session):
    code = ses.put(url=player_url+"pause")
    print("return code:", code.status_code)

def test():
    print("COMBO!")
if __name__ == "__main__":
    with keyboard.Listener(on_press=on_press, on_release=on_release) as l1:
        l1.join()
    #with keyboard.GlobalHotKeys({
    #    '<65027>+p': test
    #}) as target:
    #    target.join()s

        
    #print(req.json())

