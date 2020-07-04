import os, json, webbrowser, threading #Default lib
import base64, time, urllib.parse
import requests #External libs
from pynput import keyboard 

import webserver # Own lib

#TODO: Make it a class
class PySpoy():
    def __init__(self):
        self.listen_key = True
        self.player_url = "https://api.spotify.com/v1/me/player/"
        with open(".config") as conf_file:
            self.clientID = conf_file.read()
        self.current_r = requests.Session()
        self.rederect = "http://localhost:"+ str(webserver.PORT)
        self.access = "user-modify-playback-state"
        self.auth_url = "https://accounts.spotify.com/authorize?client_id="+ self.clientID + "&response_type=code&redirect_uri=" + urllib.parse.quote(self.rederect) +"&scope=" + self.access
        #Start a server for the authentication token
        try:
            t = threading.Thread(target=webserver.runServer, daemon=True)
            t.start()
            print("started server?")
        except Exception as e:
            print("Off", e)
        webbrowser.open(self.auth_url)
        
        timeout = 60 #Give users 1 minute to authenticate the app
        while(not os.path.exists(webserver.FILE)):
            time.sleep(1)
            timeout += 1
            if timeout <= 60:
                #TODO: Give a good error to user!
                break
        
        with open(webserver.FILE, "r") as f:
            self.authToken = f.read()
        os.remove(webserver.FILE)
        webserver.closeServer()

        self.get_access_token()

        #TODO: make UI for this and load from file
        self.keybind = {"Play/Pause": ([{keyboard.Key.alt_gr, keyboard.Key.up}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.up}], self.playPause),
        "SkipTrack": ([{}], self.skip_song), 
        "PreviousTrack": ([{}], self.prev_song), 
        "Quit": ([{keyboard.Key.shift, keyboard.Key.esc}], self.quit)}

        self.cur_key = set()
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as l1:
            l1.join()

    def get_access_token(self):
        payload = {
            "grant_type": "authorization_code",
            "code": self.authToken,
            "redirect_uri" : self.rederect,
            "client_id":     self.clientID,
            "client_secret": "Secret!"
        }

        res = self.current_r.post("https://accounts.spotify.com/api/token", data=payload)
        res_json = res.json()
        self.access_token = res_json["access_token"]
        self.token_timer = res_json["expires_in"]
        self.token_type = res_json["token_type"]
        self.authToken = res_json["refresh_token"] #Set the authtoken to be the refresh token
        self.current_r.headers.update({"Authorization":self.token_type + " " +  self.access_token})

    def quit(self):
        self.listen_key = False
               
    #TODO: Find a better way to know if state is play or pause, to minimize calls
    def playPause(self):
        code = self.current_r.put(url=self.player_url+"play")
        print("play code: ", code.status_code)
        if(code.status_code == 403):
            code = self.current_r.put(url=self.player_url+"pause")
            print("pause code:", code.status_code)

    def skip_song(self):
        pass
    
    def prev_song(self):
        pass

    def press_comb(self, key, binding : str):
        if key not in self.cur_key:
            self.cur_key.add(key)
        for combo in self.keybind[binding][0]:
            if (combo == self.cur_key):
                self.keybind[binding][1]()
            
        return False
    
    def on_press(self, key):
         #Fix for some keyboards
        if(key.__str__() == "<65027>"):
            key = keyboard.Key.alt_gr
    
        print("The key:", key.__str__())
        for keyShort in self.keybind:
            self.press_comb(key, keyShort)
        return self.listen_key
    
    def on_release(self, key):
        if(key.__str__() == "<65027>"):
            key = keyboard.Key.alt_gr
        if key in self.cur_key:
            self.cur_key.remove(key)
        return self.listen_key

    def add_key_binding(self, binding, keys : set):
        self.keybind[binding][0].add(keys)
    def remove_key_binding(self, binding, keys : set):
        self.keybind[binding][0].remove(keys)

instance = PySpoy()