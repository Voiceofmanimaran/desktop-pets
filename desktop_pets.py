"""A lightweight, single-window desktop pet for Windows 11.

Put sprites in ``sprites/<CharacterName>/walk_1.png`` (and any additional
numbered walk frames). Install Pillow with ``python -m pip install Pillow``.
"""

import argparse
import math
import random
import re
import sys
import time
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk


# Schedule and display settings.
APPEAR_EVERY_SEC = 600
STAY_SEC = 20
SIZE = 128
TICK_MS = 40
TASKBAR = 48
MAX_PETS = 1

BUBBLE_HEIGHT = 32
FRAME_INTERVAL = 6
TRANSPARENT_COLOR = "#010203"
CHARACTER_NAMES = (
    "Sasuke",
    "Zoro",
    "Zenitsu",
    "Asta",
    "Mikasa",
    "RinNohara",
    "Eren",
    "Ash",
    "Cha",
    "Nezuko",
)
CLICK_LINES = ("Vanakkam!", "Hehe!", "Ouch!", "Chai break?")
CHARACTER_LINES = {
    "Sasuke": ("Be strong!", "Hard work pays off!", "Lightning dash!"),
    "Zoro": ("Take a break!", "Be cool!", "Spin time!"),
    "Zenitsu": ("Heyyyyy!", "You're lucky!", "Just five more minutes..."),
    "Asta": ("Never give up!", "Hard work!", "You can do it!"),
    "Mikasa": ("Love life!", "Keep flying!", "Stay close!"),
    "RinNohara": ("Maara-Dharshuuu?", "Take care!", "♪ Sing with me! ♪"),
    "Eren": ("Stay fearless!", "Be strong!", "Keep moving forward!"),
    "Ash": ("Let's go!", "You're lucky!", "You got this!"),
    "Cha": ("Heyyyyy!", "Love life?", "Peekaboo!"),
    "Nezuko": ("Be cool!", "Take a break!", "Float through it!"),
}
PALETTES = {
    "Sasuke": ((248, 205, 179), (36, 39, 52), (36, 68, 128)),
    "Zoro": ((245, 190, 151), (77, 52, 43), (45, 112, 74)),
    "Zenitsu": ((255, 219, 174), (255, 188, 54), (234, 133, 35)),
    "Asta": ((255, 207, 165), (232, 229, 213), (41, 58, 76)),
    "Mikasa": ((247, 204, 181), (38, 37, 43), (142, 64, 69)),
    "RinNohara": ((255, 215, 187), (111, 65, 50), (86, 64, 114)),
    "Eren": ((248, 194, 151), (105, 71, 54), (130, 86, 57)),
    "Ash": ((255, 216, 177), (47, 49, 65), (55, 102, 166)),
    "Cha": ((255, 219, 179), (250, 195, 74), (53, 67, 94)),
    "Nezuko": ((255, 219, 197), (48, 38, 44), (191, 111, 135)),
}
OUTLINE = (45, 38, 43, 255)
WALK_FRAME = re.compile(r"walk_(\d+)\.png", re.IGNORECASE)


def sprite_canvas(image):
    """Fit one sprite into a transparent square of the configured size."""
    image = image.convert("RGBA")
    image.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(
        image, ((SIZE - image.width) // 2, (SIZE - image.height) // 2)
    )
    return canvas


def make_placeholder(name="Pet"):
    """Draw a simple fallback character when no usable sprite folders exist."""
    skin, hair, outfit = PALETTES.get(
        name, ((246, 204, 177), (65, 49, 58), (65, 91, 133))
    )
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((40, 91, 60, 119), radius=8, fill=OUTLINE)
    draw.rounded_rectangle((68, 91, 88, 119), radius=8, fill=OUTLINE)
    draw.ellipse((32, 111, 62, 124), fill=OUTLINE)
    draw.ellipse((66, 111, 98, 124), fill=OUTLINE)
    draw.rounded_rectangle(
        (36, 69, 92, 103), radius=12, fill=outfit, outline=OUTLINE, width=3
    )
    draw.ellipse((24, 8, 104, 91), fill=hair, outline=OUTLINE, width=3)
    draw.ellipse((31, 24, 97, 91), fill=skin, outline=OUTLINE, width=3)
    draw.polygon(
        ((25, 53), (28, 19), (45, 32), (55, 7), (69, 30), (90, 12),
         (104, 46), (82, 37), (61, 43), (42, 37)),
        fill=hair,
        outline=OUTLINE,
    )
    draw.ellipse((46, 55, 56, 70), fill=(42, 38, 43, 255))
    draw.ellipse((72, 55, 82, 70), fill=(42, 38, 43, 255))
    draw.ellipse((49, 57, 52, 61), fill=(255, 255, 255, 255))
    draw.ellipse((75, 57, 78, 61), fill=(255, 255, 255, 255))
    draw.arc((55, 69, 73, 82), 15, 165, fill=OUTLINE, width=2)
    draw.rounded_rectangle(
        (32, 81, 96, 93), radius=5, fill=outfit, outline=OUTLINE, width=2
    )
    draw.line((42, 88, 86, 88), fill=(235, 231, 221, 255), width=2)
    return image


def discover_characters():
    """Return only roster folders containing numbered walk frames."""
    sprite_root = Path(__file__).resolve().parent / "sprites"
    folders = {}
    if sprite_root.is_dir():
        folders = {
            path.name.casefold(): path
            for path in sprite_root.iterdir()
            if path.is_dir()
        }

    characters = {}
    for name in CHARACTER_NAMES:
        folder = folders.get(name.casefold())
        if folder is None:
            continue
        frames = []
        for path in folder.glob("*.png"):
            match = WALK_FRAME.fullmatch(path.name)
            if match:
                frames.append((int(match.group(1)), path))
        frames.sort(key=lambda item: item[0])
        if frames:
            characters[name] = [path for _, path in frames]
    return characters


def load_frames(name, paths):
    """Load just the selected character's image frames."""
    if paths is None:
        return [make_placeholder(name)]

    frames = []
    for path in paths:
        try:
            with Image.open(path) as source:
                frames.append(sprite_canvas(source))
        except (OSError, ValueError) as error:
            print(f"desktop_pets: cannot load {path}: {error}", file=sys.stderr)
    return frames


class Pet:
    def __init__(self, app, name, frames):
        self.app = app
        self.name = name
        self.frames = frames
        self.window = tk.Toplevel(app.root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.window.configure(background=TRANSPARENT_COLOR)
        self.window_height = SIZE + BUBBLE_HEIGHT
        self.window.geometry(f"{SIZE}x{self.window_height}+0+0")

        self.bubble = tk.Label(
            self.window,
            text="",
            bg="#fffdf7",
            fg="#20232a",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=3,
            relief="solid",
            bd=1,
        )
        self.bubble.place(relx=0.5, y=0, anchor="n")
        self.image_label = tk.Label(
            self.window, bg=TRANSPARENT_COLOR, bd=0, padx=0, pady=0
        )
        self.image_label.place(x=0, y=BUBBLE_HEIGHT, width=SIZE, height=SIZE)

        self.photo_cache = {}
        self.wave_photos = []
        self._create_images()
        self.frame_index = 0
        self.angle = 0
        self.flipped = False
        self._shown_image = None

        self.x = random.randint(0, max(0, app.screen_width - SIZE))
        self.ground_y = max(
            -BUBBLE_HEIGHT,
            app.screen_height - TASKBAR - self.window_height,
        )
        self.y = self.ground_y
        self.direction = random.choice((-1, 1))
        self.born_at = time.monotonic()
        self.alive = True
        self.poofing = False
        self.poof_index = 0
        self.poof_images = []
        self.activity = ""
        self.activity_tick = 0
        self.activity_data = {}
        self.frame_tick = 0
        self.click_jump_tick = 0
        self.click_bubble_tick = 0
        self.signature_bubble = ""

        self.activities = ["signature"]
        self.start_next_activity()

        self.menu = tk.Menu(self.window, tearoff=False)
        self.menu.add_command(label="Vanish now", command=self.app.vanish_all)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.app.quit)
        for widget in (self.window, self.image_label, self.bubble):
            widget.bind("<Button-1>", self.on_click)
            widget.bind("<Button-3>", self.on_menu)
        self.place()
        self.render()

    def _create_images(self):
        angles = range(0, 360, 30) if self.name == "Zoro" else (0, 90, 180, 270)
        for frame_number, frame in enumerate(self.frames):
            if self.name == "RinNohara":
                waving = frame.copy()
                draw = ImageDraw.Draw(waving)
                skin = PALETTES["RinNohara"][0] + (255,)
                draw.line((82, 91, 101, 70), fill=OUTLINE, width=10)
                draw.line((82, 91, 101, 70), fill=skin, width=6)
                draw.ellipse((96, 63, 107, 76), fill=skin, outline=OUTLINE, width=2)
                for finger_x in (98, 102, 106):
                    draw.line(
                        (finger_x, 66, finger_x + 2, 57),
                        fill=skin,
                        width=3,
                    )
                self.wave_photos.append(ImageTk.PhotoImage(waving, master=self.app.root))
                self.wave_photos.append(
                    ImageTk.PhotoImage(
                        waving.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
                        master=self.app.root,
                    )
                )
            for angle in angles:
                transformed = (
                    frame.rotate(angle, resample=Image.Resampling.BICUBIC)
                    if angle
                    else frame
                )
                self.photo_cache[(frame_number, angle, False)] = ImageTk.PhotoImage(
                    transformed, master=self.app.root
                )
                if angle == 0:
                    flipped = transformed.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    self.photo_cache[(frame_number, angle, True)] = ImageTk.PhotoImage(
                        flipped, master=self.app.root
                    )

    def place(self):
        self.window.geometry(
            f"{SIZE}x{self.window_height}{int(self.x):+d}{int(self.y):+d}"
        )

    def _set_bubble(self, text):
        self.bubble.configure(text=text)
        if text:
            self.bubble.place(relx=0.5, y=0, anchor="n")
        else:
            self.bubble.place_forget()

    def on_click(self, event):
        self.click_jump_tick = 0
        self.click_bubble_tick = 50
        self.direction = -1 if event.x_root < self.x + SIZE // 2 else 1

    def on_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)
        self.menu.grab_release()

    def start_next_activity(self):
        self.activity = "signature"
        self.activity_tick = 0
        self.activity_data = {}
        self.signature_bubble = ""
        self._start_signature()

    def _start_signature(self):
        self.signature_bubble = random.choice(
            CHARACTER_LINES.get(self.name, ("Hello!",))
        )
        self._set_bubble(self.signature_bubble)
        if self.name == "Sasuke":
            self._start_dash()
        elif self.name == "Zoro":
            self.activity_data["duration"] = 36
        elif self.name == "Zenitsu":
            self.activity_data.update(phase="sleep", duration=38)
            self.angle = 90
            self.signature_bubble = "Zzz"
            self._set_bubble(self.signature_bubble)
        elif self.name == "Asta":
            self.activity_data["duration"] = 60
        elif self.name == "Mikasa":
            jump_distance = self.app.screen_width / 3
            right_edge = max(0, self.app.screen_width - SIZE)
            directions = [
                direction
                for direction in (-1, 1)
                if 0 <= self.x + direction * jump_distance <= right_edge
            ]
            self.activity_data.update(
                start_x=self.x,
                start_y=self.y,
                start_direction=random.choice(directions) if directions else self.direction,
                duration=60,
            )
        elif self.name == "RinNohara":
            self.activity_data["duration"] = 50
        elif self.name == "Eren":
            self._start_eren()
        elif self.name == "Ash":
            self.activity_data["duration"] = 80
        elif self.name == "Cha":
            self._start_peek()
        elif self.name == "Nezuko":
            self.activity_data["duration"] = 72

    def _start_dash(self):
        self.direction = random.choice((-1, 1))
        self.x = 0 if self.direction > 0 else max(0, self.app.screen_width - SIZE)
        self.activity_data["phase"] = "dash"

    def _start_eren(self):
        edge = 0 if abs(self.x) < abs(self.x - (self.app.screen_width - SIZE)) else max(
            0, self.app.screen_width - SIZE
        )
        self.activity_data.update(phase="approach", edge=edge)
        self.direction = 1 if edge > self.x else -1

    def _start_peek(self):
        edge_left = 0
        edge_right = max(0, self.app.screen_width - SIZE)
        edge = edge_left if abs(self.x - edge_left) < abs(self.x - edge_right) else edge_right
        self.activity_data.update(phase="approach", edge=edge)
        self.direction = 1 if edge > self.x else -1

    def _finish_activity(self):
        self.angle = 0
        self.y = self.ground_y
        self.signature_bubble = ""
        self._set_bubble("")
        self.start_next_activity()

    def _advance_signature(self):
        name = self.name
        tick = self.activity_tick
        data = self.activity_data
        if name == "Sasuke":
            self.x += self.direction * 32
            return self.x >= self.app.screen_width - SIZE or self.x <= 0
        if name == "Zoro":
            self.angle = (tick * 30) % 360
            return tick >= data["duration"]
        if name == "Zenitsu":
            if data["phase"] == "sleep":
                self.angle = 90
                if tick >= data["duration"]:
                    data["phase"] = "dash"
                    self.angle = 0
                    self.signature_bubble = random.choice(CHARACTER_LINES["Zenitsu"])
                    self._set_bubble(self.signature_bubble)
                    self.direction = random.choice((-1, 1))
            else:
                self.x += self.direction * 30
                if self.x >= self.app.screen_width - SIZE or self.x <= 0:
                    return True
            return False
        if name == "Asta":
            self.activity_data["vertical_offset"] = -105 * abs(
                math.sin(math.pi * (tick % 20) / 20)
            )
            return tick >= data["duration"]
        if name == "Mikasa":
            progress = min(1.0, tick / data["duration"])
            self.x = data["start_x"] + data["start_direction"] * (
                self.app.screen_width / 3
            ) * progress
            self.activity_data["vertical_offset"] = -130 * math.sin(math.pi * progress)
            return progress >= 1.0
        if name == "RinNohara":
            self.activity_data["vertical_offset"] = -4 if tick % 10 < 5 else 0
            return tick >= data["duration"]
        if name == "Eren":
            phase = data["phase"]
            edge = data["edge"]
            if phase == "approach":
                self.x += self.direction * max(
                    10.0, self.app.screen_width / 100.0
                )
                if (self.direction < 0 and self.x <= edge) or (
                    self.direction > 0 and self.x >= edge
                ):
                    self.x = edge
                    data["phase"] = "up"
            elif phase == "up":
                self.y -= max(8, self.app.screen_height / 80)
                if self.y <= -BUBBLE_HEIGHT:
                    self.y = -BUBBLE_HEIGHT
                    data["phase"] = "hang"
                    data["hang_tick"] = 0
                    self.angle = 180
            elif phase == "hang":
                data["hang_tick"] += 1
                if data["hang_tick"] >= 125:
                    data["phase"] = "down"
                    self.angle = 270
            else:
                self.y += max(8, self.app.screen_height / 80)
                if self.y >= self.ground_y:
                    self.y = self.ground_y
                    return True
            return False
        if name == "Ash":
            self.activity_data["vertical_offset"] = -30 * abs(
                math.sin(math.pi * (tick % 16) / 16)
            )
            return tick >= data["duration"]
        if name == "Cha":
            phase = data["phase"]
            edge = data["edge"]
            if phase == "approach":
                self.x += self.direction * max(
                    10.0, self.app.screen_width / 100.0
                )
                if (self.direction < 0 and self.x <= edge) or (
                    self.direction > 0 and self.x >= edge
                ):
                    self.x = edge
                    data["phase"] = "peek"
                    data["phase_tick"] = 0
            elif phase == "peek":
                data["phase_tick"] += 1
                self.x = edge - SIZE // 2 if edge == 0 else edge + SIZE // 2
                if data["phase_tick"] >= 20:
                    data["phase"] = "slide"
                    data["phase_tick"] = 0
            else:
                data["phase_tick"] += 1
                self.x += (edge - self.x) / max(1, 20 - data["phase_tick"] + 1)
                if data["phase_tick"] >= 20:
                    self.x = edge
                    return True
            return False
        if name == "Nezuko":
            start_x = data.setdefault("start_x", self.x)
            self.x = min(
                max(0, start_x + 38 * math.sin(tick / 24)),
                max(0, self.app.screen_width - SIZE),
            )
            self.activity_data["vertical_offset"] = -26 - 14 * math.sin(tick / 10)
            return tick >= data["duration"]
        return tick >= 50

    def _advance_activity(self):
        self.activity_tick += 1
        self.frame_tick += 1
        if self.frame_tick % FRAME_INTERVAL == 0:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
        if self._advance_signature():
            self._finish_activity()

    def step(self):
        if not self.alive or self.poofing:
            return
        self._advance_activity()
        self.click_jump_tick = min(25, self.click_jump_tick + 1)
        if self.click_bubble_tick > 0:
            if self.click_bubble_tick == 50:
                self._set_bubble(random.choice(CLICK_LINES))
            self.click_bubble_tick -= 1
            if self.click_bubble_tick == 0:
                self._set_bubble(self.signature_bubble)
        elif self.signature_bubble:
            self._set_bubble(self.signature_bubble)
        else:
            self._set_bubble("")
        self.render()

    def render(self):
        self.flipped = self.direction < 0 and self.angle == 0
        angle = self.angle % 360
        if self.name == "Zoro":
            angle = int(round(angle / 30.0) * 30) % 360
        image_key = (self.frame_index, angle, self.flipped)
        waving = (
            self.name == "RinNohara"
            and self.activity == "signature"
            and self.activity_tick % 10 < 5
        )
        shown_key = image_key + (waving,)
        if shown_key != self._shown_image:
            image = (
                self.wave_photos[self.frame_index * 2 + int(self.flipped)]
                if waving
                else self.photo_cache[image_key]
            )
            self.image_label.configure(image=image)
            self._shown_image = shown_key
        vertical_offset = self.activity_data.get("vertical_offset", 0)
        jump_offset = 0
        if self.click_jump_tick < 25:
            progress = self.click_jump_tick / 25
            jump_offset = -42 * math.sin(math.pi * progress)
        self.window.geometry(
            f"{SIZE}x{self.window_height}{int(self.x):+d}"
            f"{int(self.y + vertical_offset + jump_offset):+d}"
        )

    def begin_poof(self):
        if self.poofing:
            return
        self.poofing = True
        self.bubble.place_forget()
        frame = self.frames[self.frame_index]
        if self.angle:
            frame = frame.rotate(self.angle, resample=Image.Resampling.BICUBIC)
        if self.direction < 0 and self.angle == 0:
            frame = frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        for size in (96, 64, 32, 1):
            shrunk = frame.resize((size, size), Image.Resampling.LANCZOS)
            self.poof_images.append(ImageTk.PhotoImage(shrunk, master=self.app.root))

    def poof_step(self):
        if self.poof_index >= len(self.poof_images):
            return True
        size = (96, 64, 32, 1)[self.poof_index]
        image = self.poof_images[self.poof_index]
        offset = (SIZE - size) // 2
        self.image_label.configure(image=image, width=size, height=size)
        self.image_label.place(
            x=0,
            y=BUBBLE_HEIGHT,
            width=size,
            height=size,
        )
        x = self.x + offset
        y = self.y + offset
        self.window.geometry(
            f"{size}x{size + BUBBLE_HEIGHT}{int(x):+d}{int(y):+d}"
        )
        self.poof_index += 1
        return False

    def destroy(self):
        if not self.alive:
            return
        self.alive = False
        self.window.destroy()
        self.photo_cache.clear()
        self.wave_photos.clear()
        self.poof_images.clear()
        self.frames.clear()


class DesktopPets:
    def __init__(self, test_mode=False):
        self.root = tk.Tk()
        self.root.withdraw()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.test_mode = test_mode
        self.appear_every_sec = 30 if test_mode else APPEAR_EVERY_SEC
        self.characters = discover_characters()
        if not self.characters:
            self.characters = {"Pet": None}
        self.character_order = []
        self.last_character = None
        self.pets = []
        self.timer_id = None
        self.closing = False
        self.show_next_batch()

    def _next_character(self):
        if not self.character_order:
            self.character_order = list(self.characters)
            random.shuffle(self.character_order)
            if (
                len(self.character_order) > 1
                and self.character_order[0] == self.last_character
            ):
                self.character_order[0], self.character_order[1] = (
                    self.character_order[1],
                    self.character_order[0],
                )
        return self.character_order.pop(0)

    def show_next_batch(self):
        self.timer_id = None
        if self.closing:
            return
        count = min(max(1, MAX_PETS), len(self.characters))
        while len(self.pets) < count and self.characters:
            name = self._next_character()
            frames = load_frames(name, self.characters[name])
            if not frames:
                print(
                    f"desktop_pets: no usable walk frames for {name}; skipping it",
                    file=sys.stderr,
                )
                self.characters.pop(name, None)
                self.character_order = [
                    queued for queued in self.character_order if queued in self.characters
                ]
                if not self.characters:
                    self.characters = {"Pet": None}
                    self.character_order = []
                continue
            self.last_character = name
            self.pets.append(Pet(self, name, frames))
        if self.pets:
            self._schedule_tick()
        else:
            self._schedule_appearance()

    def _schedule_tick(self):
        if not self.closing and self.timer_id is None:
            self.timer_id = self.root.after(TICK_MS, self.tick)

    def _schedule_appearance(self):
        if not self.closing:
            self.timer_id = self.root.after(
                self.appear_every_sec * 1000, self.show_next_batch
            )

    def tick(self):
        self.timer_id = None
        if self.closing:
            return
        now = time.monotonic()
        survivors = []
        for pet in self.pets:
            if not pet.poofing and now - pet.born_at >= STAY_SEC:
                pet.begin_poof()
            if pet.poofing:
                if pet.poof_step():
                    pet.destroy()
                    continue
            else:
                pet.step()
            survivors.append(pet)
        self.pets = survivors
        if self.pets:
            self._schedule_tick()
        else:
            self._schedule_appearance()

    def vanish_all(self):
        for pet in self.pets:
            pet.begin_poof()
        self._schedule_tick()

    def quit(self):
        if self.closing:
            return
        self.closing = True
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        for pet in self.pets:
            pet.destroy()
        self.pets.clear()
        self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description="A lightweight Windows desktop pet.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="wait 30 seconds between appearances instead of 10 minutes",
    )
    options = parser.parse_args(argv)
    try:
        app = DesktopPets(test_mode=options.test)
        app.root.mainloop()
    except (OSError, tk.TclError, ValueError) as error:
        print(f"desktop_pets: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
