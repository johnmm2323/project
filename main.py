from kivy import require
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from threading import Thread
from requests import get

require('1.9.0')


class AlarmRoot(Widget):
    def __init__(self, **kwargs):
        super(AlarmRoot, self).__init__(**kwargs)
        self.logged = 0
        self.tk = str()
        self.found = 0
        self.sound = SoundLoader.load("assets/alarm_sound.wav")

    def btn_action(self, touch, *args):
        if self.collide_point(*touch.pos):
            if not self.logged:
                self.ids.main_btn.source = "assets/off_btn.png"
                self.ids.main_msg.color = (1, 0, 0, 1)
                Clock.schedule_once(self.reset_btn, 0.1)

    def reset_btn(self, *args):
        self.ids.main_btn.source = "assets/default_btn.png"
        self.ids.main_msg.color = (1, 1, 1, 1)

    def verification(self, touch, *args):
        if self.collide_point(*touch.pos):
            token = str(self.ids.main_input.text)
            Thread(target=self.do_verification, args=(token,)).start()

    def do_verification(self, token):
        self.ids.main_msg.text = "Please wait..."
        result = get(f"http://localhost:8000/update?tk={token}").json()
        if result["error"]:
            Clock.schedule_once(lambda dt: self.handle_verification(False))
        else:
            self.tk = token
            Clock.schedule_once(lambda dt: self.handle_verification(True))

    def handle_verification(self, success):
        if success:
            self.logged = 1
            self.remove_widget(self.ids.verification_btn)
            self.remove_widget(self.ids.main_input)
            self.ids.main_msg.text = "Verification successful, checking starts after 3 seconds..."
            self.ids.main_btn.source = "assets/on_btn.png"
            Clock.schedule_once(self.update_text, 3)
        else:
            self.ids.main_msg.text = "Invalid token."

    def update_text(self, *args):
        self.ids.main_btn.source = "assets/default_btn.png"
        self.ids.main_msg.text = "Nothing new...Checking again."
        Thread(target=self.send_request, args=(self.start_checking,)).start()

    def start_checking(self, result):
        self.ids.main_msg.text = "Checking..."
        print(result)
        if result["telegram"]["new_message"] and result["discord"]["new_message"]:
            self.ids.main_msg.text = "NEW MESSAGE FROM TELEGRAM AND DISCORD."
            self.found = 1
        elif result["telegram"]["new_message"]:
            self.ids.main_msg.text = "NEW MESSAGE FROM TELEGRAM."
            self.found = 1
        elif result["discord"]["new_message"]:
            self.ids.main_msg.text = "NEW MESSAGE FROM DISCORD."
            self.found = 1

        if self.found:
            self.ids.main_btn.on_touch_down = self.deactive
            self.ids.main_btn.source = "assets/off_btn.png"
            self.sound.loop = True
            self.sound.play()
        else:
            Clock.schedule_once(self.update_text, 0.5)

    def send_request(self, callback):
        result = get(url=f"http://localhost:8000/update?tk={self.tk}").json()
        callback(result)

    def deactive(self, touch, *args):
        if self.collide_point(*touch.pos):
            if self.found == 1:
                self.ids.main_btn.source = "assets/default_btn.png"
                self.sound.stop()
                self.found = 0
                Clock.schedule_once(self.update_text, 0.5)


class AlarmApp(App):
    def build(self):
        return AlarmRoot()


if __name__ == '__main__':
    AlarmApp().run()
