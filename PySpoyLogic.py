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

        self.current_r = requests.Session()
        self.current_r.headers.update({'Content-type': 'application/x-www-form-urlencoded'})
        auth_code = self.get_access_code()
        refresh_token, expire = self.get_access_token(auth_code)

        self.refresh_thread = threading.Thread(target=self.refresh_token_t, args=(refresh_token, expire,), daemon=True)
        self.refresh_thread.start()
 
        #TODO: make UI for this and load from file
        self.keybind = {"Play/Pause": ([{keyboard.Key.alt_gr, keyboard.Key.ctrl_l, keyboard.Key.up}, {keyboard.Key.alt_gr, keyboard.Key.up}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.up}, {keyboard.Key.alt, keyboard.Key.ctrl, keyboard.Key.up}], self.playPause),
        "PreviousTrack": ([{keyboard.Key.alt_gr, keyboard.Key.ctrl_l, keyboard.Key.left}, {keyboard.Key.alt_gr, keyboard.Key.left}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.left}, {keyboard.Key.alt, keyboard.Key.ctrl, keyboard.Key.left}], self.prev_song), 
        "SkipTrack": ([{keyboard.Key.alt_gr, keyboard.Key.ctrl_l, keyboard.Key.right}, {keyboard.Key.alt_gr, keyboard.Key.right}, {keyboard.Key.alt_r, keyboard.Key.ctrl_l, keyboard.Key.right}, {keyboard.Key.alt, keyboard.Key.ctrl, keyboard.Key.right}], self.skip_song), 
        "Quit": ([{keyboard.Key.shift, keyboard.Key.esc}], self.quit)}

        self.cur_key = set()
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as l1:
            try:
                l1.join()
            except Exception as e:
                print("Exception", e)

    def b64encodeString(self, string):
        return base64.urlsafe_b64encode(string.encode('ascii')).decode('ascii').replace("=", "")

    def get_access_code(self):
        self.player_url = "https://api.spotify.com/v1/me/player/"
        with open(".config") as conf_file:
            self.clientID = conf_file.read()
        
        self.redirect = "http://localhost:"+ str(webserver.PORT)
        self.access = "user-modify-playback-state user-read-currently-playing user-read-playback-state"
        
        self.state = "".join(random.choices(ascii_letters, k=16))
        self.verifier = "".join(random.choices("QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm0123456789-._~", k=random.randint(43,128)))
        self.challenge = base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest()).decode("ascii").replace("=", "")
        print(self.challenge)
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
            authToken = f.read()
        os.remove(webserver.FILE)
        webserver.closeServer()
        return authToken

    def get_access_token(self, code):
        """Warning Run get_access_code before
        """
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri" : self.redirect,
            "client_id":     self.clientID,
            "code_verifier": self.verifier
        }
        print("client_id",     self.clientID)
        res = self.current_r.post("https://accounts.spotify.com/api/token", data=payload)
        res_json = res.json()
        if "error" in res_json:
            print(res_json["error"])
            return
        self.current_r.headers.update({"Authorization":res_json["token_type"] + " " +  res_json["access_token"]})
        return res_json["refresh_token"], res_json["expires_in"]

    def refresh_token_t(self, token, expires_in):
        print("We will be waiting for", expires_in)
        while True:
            time.sleep(expires_in)
            expires_in, refresh_token = self.refresh_token(token)
            if expires_in is None:
                break
            if refresh_token is not None:
                token = refresh_token


    def refresh_token(self, token):
        print("refreshing token")
        payload = {
            "client_id": self.clientID,
            "grant_type": "refresh_token",
            "refresh_token" : token
        }
        self.current_r.headers.clear()
        self.current_r.headers.update({'Content-type': 'application/x-www-form-urlencoded'})
        res = self.current_r.post("https://accounts.spotify.com/api/token", data=payload)
        res_json = res.json()
        if "error" in res_json:
            print(res_json["error"])
            return 
        self.current_r.headers.update({"Authorization":res_json["token_type"] + " " +  res_json["access_token"]})
        
        refresh_token = None
        if "refresh_token" in res_json:
            refresh_token = res_json["refresh_token"]
        return res_json["expires_in"], refresh_token

    def quit(self):
        self.listen_key = False
               
    #TODO: Find a better way to know if state is play or pause, to minimize calls
    def playPause(self):
        #self.key_control.press(keyboard.Key.media_play_pause)
        #self.key_control.release(keyboard.Key.media_play_pause)
        playing = self.is_playing()
        if(playing == None):
            print("Failed to get 200 response from 'is_playing'")
            return
        if(playing):
            code = self.current_r.put(url=self.player_url+"pause")
            print("pause return code:", code.status_code)
        else:
            code = self.current_r.put(url=self.player_url+"play")
            print("play return code: ", code.status_code)
        """
        """

    def is_playing(self):
        code = self.current_r.get(self.player_url+"currently-playing")
        print("is_playing return code:", code.status_code)
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

    def press_comb(self, binding : str):
        for combo in self.keybind[binding][0]:
            if combo.intersection(self.cur_key) == combo:
                return self.keybind[binding][1]

    def on_press(self, key):
        #Clear pressed down keys after 5000ms (This is a temp fix for missed released keys)
        if self.last_click is not None and self.last_click + 2 < time.time():
            self.last_click = time.time()
            self.cur_key.clear()
         #Fix for some keyboards
        if(key.__str__() == "<65027>"):
            key = keyboard.Key.alt_gr

        if key not in self.cur_key:
            self.cur_key.add(key)
        print("Keys pressed down:",self.cur_key)
        for keyShort in self.keybind:
            func = self.press_comb(keyShort)
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
            for func in self.run_on_release:
                func()
            self.run_on_release.clear()
            self.pause_listen = False

        self.last_click = time.time()
        return self.listen_key

    def add_key_binding(self, binding, keys : set):
        self.keybind[binding][0].add(keys)
        
    def remove_key_binding(self, binding, keys : set):
        self.keybind[binding][0].remove(keys)

instance = PySpoy()