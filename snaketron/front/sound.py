from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.core.audio import SoundLoader

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional

    from kivy.core.audio import Sound


class SoundController:
    def __init__(self, **sounds: Path) -> None:
        self.sound_paths: dict[str, Optional[Sound]] = {}
        for sound_name, sound_path in sounds.items():
            assert sound_path.is_file()
            sound = SoundLoader.load(str(sound_path))
            if sound is None:
                print(f"Unable to load sound: {sound_path}")
            else:
                print(f"Loaded sound {sound_name}")
                self.sound_paths[sound_name] = sound

    def play_sound(self, sound_name: str, loop: bool=False) -> None:
        sound = self.sound_paths.get(sound_name)
        print(f"DEBUG: play_sound {sound_name} {loop=}: {sound=}")
        if sound is not None:
            sound.loop = loop
            sound.play()

    def stop_sound(self, sound_name: str) -> None:
        sound = self.sound_paths.get(sound_name)
        print(f"DEBUG: stop_sound {sound_name}: {sound=}")
        if sound is not None:
            sound.stop()


if __name__ == '__main__':
    from pathlib import Path

    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button

    class TestWindow(BoxLayout):
        pass

    class MusicApp(App):
        def build(self):
            self.sound_controller = SoundController(ambiant_music=Path('front', 'sounds', 'The-Game-Has-Changed_Tron-Legacy_Daft-Punk.mp3'))

            Builder.load_string('''
<MusicApp>:
    id: app

<TestWindow>:
    Button:
        text: "play music"
        on_press: app.sound_controller.play_sound("ambiant_music", loop=True)
    Button:
        text: "stop music"
        on_press: app.sound_controller.stop_sound("ambiant_music")
''')
            return TestWindow()


    app = MusicApp()
    app.run()
