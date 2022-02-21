import os, json, webbrowser, threading #Default lib
import base64, time, math, random
import requests, hashlib #External libs
from pynput import keyboard
from string import ascii_letters

from urllib import parse

import PySpoyWebserver as webserver# Own lib

class PySpoy():
    def __init__(self):
        self.listen_key = True
        

        self.key_control = keyboard.Controller()
        self.run_on_release = set() #The function to run when the keys are released
        self.pause_listen = False


        self.player_url = "https://api.spotify.com/v1/me/player/"
        with open(".config") as conf_file:
            self.clientID = conf_file.read()
        
        self.current_r = requests.Session()
        self.redirect = "http://localhost:"+ str(webserver.PORT)
        self.access = "user-modify-playback-state user-read-currently-playing user-read-playback-state"
        
        self.state = "".join(random.choices(ascii_letters, k=16))
        self.verifier = "".join(random.choices("QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm0123456789-._~", k=random.randint(43,128)))
        self.challenge = base64.b64encode(hashlib.sha256(self.verifier.encode()).digest()).decode("ascii").replace("=","").replace("+","-").replace("/","_")
        payload_auth_req = {
            "response_type": 'code',
            "client_id": self.clientID,
            "scope": self.access,
            "redirect_uri": self.redirect,
            "state": self.state,
            "code_challenge_method": "S256",
            "code_challenge": self.challenge
        }
        self.auth_url = "https://accounts.spotify.com/authorize?" + parse.urlencode(payload_auth_req)
        print(parse.urlencode(payload_auth_req))
        #Start a server for the authentication token
        try:
            t = threading.Thread(target=webserver.runServer, daemon=True)
            t.start()
            print("started server?")
        except Exception as e:
            print("Off", e)
        webbrowser.open(self.auth_url)
        
        timeout = 60 #Give users 1 minute to authenticate the app
        while not os.path.exists(webserver.FILE):
            time.sleep(1)
            timeout -= 1
            if timeout < 0:
                #TODO: Give a good error to user!
                break
        with open(webserver.FILE, "r") as f:
            self.authToken = f.read()
        os.remove(webserver.FILE)
        webserver.closeServer()
        
        self.get_access_token()
 
        #TODO: make UI for this and load from file
        self.keybind = {"Play/Pause": ([{keyboard.Key.alt_gr, keyboard.Key.ctrl_l, keyboard.Key.up}, {keyboard.Key.alt_gr, keyboard.Key.up}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.up}, {keyboard.Key.alt, keyboard.Key.ctrl, keyboard.Key.up}], self.playPause),
        "SkipTrack": ([{keyboard.Key.alt_gr, keyboard.Key.ctrl_l, keyboard.Key.left}, {keyboard.Key.alt_gr, keyboard.Key.left}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.left}], self.skip_song), 
        "PreviousTrack": ([{keyboard.Key.alt_gr, keyboard.Key.ctrl_l, keyboard.Key.right}, {keyboard.Key.alt_gr, keyboard.Key.right}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.right}], self.prev_song), 
        "Quit": ([{keyboard.Key.shift, keyboard.Key.esc}], self.quit)}

        self.cur_key = set()
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as l1:
            try:
                l1.join()
            except Exception as e:
                print("Exception", e)

    #TODO: Send clientID and secret as encoded64 
    
    def get_access_token(self):
        payload = {
            "grant_type": "authorization_code",
            "code": self.authToken,
            "redirect_uri" : self.redirect,
            "client_id":     self.clientID,
            "code_verifier": self.verifier
        }

        res = self.current_r.post("https://accounts.spotify.com/api/token", data=payload)
        res_json = res.json()
        print(res_json)
        if "error" in res_json:
            print(res_json["error"])
            return
        self.access_token = res_json["access_token"]
        self.token_timer = res_json["expires_in"]
        self.token_type = res_json["token_type"]
        self.authToken = res_json["refresh_token"] #Set the authtoken to be the refresh token
        self.current_r.headers.update({"Authorization":self.token_type + " " +  self.access_token})

    def quit(self):
        self.listen_key = False
               
    #TODO: Find a better way to know if state is play or pause, to minimize calls
    def playPause(self):
        self.key_control.press(keyboard.Key.media_play_pause)
        self.key_control.release(keyboard.Key.media_play_pause)
        """
        playing = self.is_playing()
        if(playing == None):
            print("Failed to get 200 response from 'is_playing'")
            return
        if(playing):
            code = self.current_r.put(url=self.player_url+"pause")
            print("pause code:", code.status_code)
        else:
            code = self.current_r.put(url=self.player_url+"play")
            print("play code: ", code.status_code)
        """

    def is_playing(self):
        code = self.current_r.get(self.player_url+"currently-playing")
        print("is_playing:", code.status_code)
        res = None
        if(code.status_code == 200):
            res = code.json()["is_playing"]
        else:
            print("Failed to get current playing response code: ", code.status_code)
        return res

    def skip_song(self):
        self.key_control.press(keyboard.Key.media_next)
        self.key_control.release(keyboard.Key.media_next)
        pass
    
    def prev_song(self):
        self.key_control.press(keyboard.Key.media_previous)
        self.key_control.release(keyboard.Key.media_previous)
        pass

    def press_comb(self, key, binding : str):
        #TODO: Just add it, if it is in any of the bindings
        if key not in self.cur_key:
            self.cur_key.add(key)
        for combo in self.keybind[binding][0]:
            #TODO: Use intersection to fix bug where a key randomly get stuck in the set
            if (combo == self.cur_key):
                return self.keybind[binding][1]

    def on_press(self, key):
         #Fix for some keyboards
        if(key.__str__() == "<65027>"):
            key = keyboard.Key.alt_gr
    
        print("The key:", key.__str__())
        print("Keys pressed down: ", key, self.cur_key)
        for keyShort in self.keybind:
            func = self.press_comb(key, keyShort)
            if func is not None:
                self.run_on_release.add(func)
        return self.listen_key
    
    def on_release(self, key):
        if self.pause_listen:
            return True
        if(key.__str__() == "<65027>"):
            key = keyboard.Key.alt_gr
        if key in self.cur_key:
            self.cur_key.remove(key)
        
        if len(self.run_on_release) > 0 and len(self.cur_key) == 0:
            self.pause_listen = True
            print("Running func")
            for func in self.run_on_release:
                func()
            self.run_on_release.clear()
            self.pause_listen = False
        return self.listen_key

    def add_key_binding(self, binding, keys : set):
        self.keybind[binding][0].add(keys)
        
    def remove_key_binding(self, binding, keys : set):
        self.keybind[binding][0].remove(keys)

instance = PySpoy()