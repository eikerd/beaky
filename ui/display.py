"""Tkinter conversation display for Beaky kiosk."""

import logging
import queue
import tkinter as tk
from tkinter import font as tkfont

import config

log = logging.getLogger(__name__)

# Event types for the UI queue
MSG_USER = "user"
MSG_BEAKY = "beaky"
MSG_BEAKY_STREAM = "beaky_stream"  # streaming token append
MSG_BEAKY_DONE = "beaky_done"     # end of streamed response
MSG_STATUS = "status"
MSG_VOLUME = "volume"  # audio input level (0.0 to 1.0)
MSG_LOG = "log"  # system log message
MSG_VIDEO = "video"  # video frame (BGR numpy array as bytes)
MSG_VISION_TEXT = "vision_text"  # vision description overlay


class Display:
    """Full-screen Tkinter display for the Beaky kiosk.

    Must be created and run on the main thread (Tk requirement).
    Other threads post messages via `post(event_type, text)`.
    """

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self.root: tk.Tk | None = None

    # --- public API (thread-safe) ---

    def post(self, event_type: str, text: str = ""):
        """Enqueue a display event from any thread."""
        self._queue.put((event_type, text))

    def run(self, on_close=None):
        """Build the window and enter the Tk main loop. Blocks until closed."""
        self.root = tk.Tk()
        self.root.title(config.UI_TITLE)
        self.root.configure(bg=config.UI_BG_COLOR)

        if config.UI_FULLSCREEN:
            self.root.attributes("-fullscreen", True)
        else:
            self.root.geometry("900x700")

        self.root.bind("<Escape>", lambda e: self._close(on_close))
        self.root.protocol("WM_DELETE_WINDOW", lambda: self._close(on_close))

        # -- header --
        header = tk.Label(
            self.root,
            text="~ BEAKY ~",
            bg=config.UI_BG_COLOR,
            fg=config.UI_USER_COLOR,
            font=(config.UI_FONT_FAMILY, 28, "bold"),
            pady=12,
        )
        header.pack(fill=tk.X)

        # -- main content area (video + chat) --
        main_container = tk.Frame(self.root, bg=config.UI_BG_COLOR)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # -- video feed panel (right side) --
        video_panel = tk.Frame(main_container, bg="#0a0a0a", width=320)
        video_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        video_panel.pack_propagate(False)

        tk.Label(
            video_panel,
            text="📹 CAMERA",
            bg="#0a0a0a",
            fg="#888888",
            font=(config.UI_FONT_FAMILY, 10, "bold"),
            pady=5,
        ).pack()

        self._video_label = tk.Label(video_panel, bg="#000000")
        self._video_label.pack(pady=5)

        self._vision_text_label = tk.Label(
            video_panel,
            text="",
            bg="#0a0a0a",
            fg="#60a5fa",
            font=(config.UI_FONT_FAMILY, 9),
            wraplength=300,
            justify=tk.LEFT,
            padx=10,
            pady=5,
        )
        self._vision_text_label.pack()

        # -- scrollable conversation area (left side) --
        container = tk.Frame(main_container, bg=config.UI_BG_COLOR)
        container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(container, bg=config.UI_BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=self._canvas.yview)
        self._scroll_frame = tk.Frame(self._canvas, bg=config.UI_BG_COLOR)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # -- volume meter --
        volume_frame = tk.Frame(self.root, bg="#0d0d1a", height=30)
        volume_frame.pack(fill=tk.X, side=tk.BOTTOM)
        volume_frame.pack_propagate(False)

        tk.Label(
            volume_frame,
            text="🎤",
            bg="#0d0d1a",
            fg="#888888",
            font=(config.UI_FONT_FAMILY, 12),
        ).pack(side=tk.LEFT, padx=(20, 5))

        self._volume_canvas = tk.Canvas(
            volume_frame,
            bg="#1a1a2e",
            height=16,
            highlightthickness=0,
        )
        self._volume_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20), pady=7)
        self._volume_bar = self._volume_canvas.create_rectangle(
            0, 0, 0, 16, fill="#4ade80", outline=""
        )

        # -- status bar --
        self._status_var = tk.StringVar(value="Waiting for speech...")
        self._status_bar = tk.Label(
            self.root,
            textvariable=self._status_var,
            bg="#0d0d1a",
            fg="#888888",
            font=(config.UI_FONT_FAMILY, 11),
            anchor="w",
            padx=20,
            pady=6,
        )
        self._status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Kick off the queue poll
        self.root.after(50, self._poll_queue)
        self.root.mainloop()

    # --- internal ---

    def _poll_queue(self):
        """Process pending UI events."""
        try:
            while True:
                event_type, text = self._queue.get_nowait()
                if event_type == MSG_USER:
                    self._add_bubble(text, is_user=True)
                elif event_type == MSG_BEAKY:
                    self._add_bubble(text, is_user=False)
                elif event_type == MSG_BEAKY_STREAM:
                    self._append_stream(text)
                elif event_type == MSG_BEAKY_DONE:
                    self._finalize_stream()
                elif event_type == MSG_STATUS:
                    self._status_var.set(text)
                    # Change color based on status
                    if "Voice detected" in text or "🎤" in text:
                        self._status_bar.configure(bg="#1a4d1a", fg="#4ade80")  # Green when hearing
                    elif "Processing" in text or "Thinking" in text:
                        self._status_bar.configure(bg="#1a1a4d", fg="#60a5fa")  # Blue when processing
                    elif "speaking" in text.lower():
                        self._status_bar.configure(bg="#4d1a4d", fg="#c084fc")  # Purple when Beaky speaks
                        self._start_speaking_animation()
                    else:
                        self._status_bar.configure(bg="#0d0d1a", fg="#888888")  # Default gray
                        self._stop_speaking_animation()
                elif event_type == MSG_VOLUME:
                    self._update_volume(float(text))
                elif event_type == MSG_VIDEO:
                    self._update_video(text)
                elif event_type == MSG_VISION_TEXT:
                    self._update_vision_text(text)
        except queue.Empty:
            pass

        if self.root:
            self.root.after(50, self._poll_queue)

    def _add_bubble(self, text: str, is_user: bool):
        """Add a full message bubble to the conversation."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Create container frame for the message
        container = tk.Frame(self._scroll_frame, bg=config.UI_BG_COLOR)
        container.pack(fill=tk.X, padx=10, pady=4)

        if is_user:
            # User messages on the RIGHT
            # Timestamp
            tk.Label(
                container,
                text=timestamp,
                bg=config.UI_BG_COLOR,
                fg="#666666",
                font=(config.UI_FONT_FAMILY, 9),
            ).pack(side=tk.RIGHT, padx=(5, 0))

            # Message bubble
            bubble = tk.Label(
                container,
                text=text,
                bg=config.UI_USER_COLOR,
                fg=config.UI_TEXT_COLOR,
                font=(config.UI_FONT_FAMILY, config.UI_FONT_SIZE),
                wraplength=500,
                justify=tk.LEFT,
                padx=12,
                pady=8,
                relief=tk.FLAT,
            )
            bubble.pack(side=tk.RIGHT, padx=(0, 5))

            # Label
            tk.Label(
                container,
                text="You",
                bg=config.UI_BG_COLOR,
                fg=config.UI_USER_COLOR,
                font=(config.UI_FONT_FAMILY, 10, "bold"),
            ).pack(side=tk.RIGHT, padx=(0, 8))
        else:
            # Beaky messages on the LEFT
            # Label
            tk.Label(
                container,
                text="Beaky",
                bg=config.UI_BG_COLOR,
                fg=config.UI_BEAKY_COLOR,
                font=(config.UI_FONT_FAMILY, 10, "bold"),
            ).pack(side=tk.LEFT, padx=(0, 8))

            # Message bubble
            bubble = tk.Label(
                container,
                text=text,
                bg=config.UI_BEAKY_COLOR,
                fg=config.UI_TEXT_COLOR,
                font=(config.UI_FONT_FAMILY, config.UI_FONT_SIZE),
                wraplength=500,
                justify=tk.LEFT,
                padx=12,
                pady=8,
                relief=tk.FLAT,
            )
            bubble.pack(side=tk.LEFT, padx=(0, 5))

            # Timestamp
            tk.Label(
                container,
                text=timestamp,
                bg=config.UI_BG_COLOR,
                fg="#666666",
                font=(config.UI_FONT_FAMILY, 9),
            ).pack(side=tk.LEFT, padx=(5, 0))

        self._auto_scroll()

    def _append_stream(self, token: str):
        """Append a token to the current streaming bubble."""
        if not hasattr(self, "_stream_bubble") or self._stream_bubble is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            # Create container for streaming message
            self._stream_container = tk.Frame(self._scroll_frame, bg=config.UI_BG_COLOR)
            self._stream_container.pack(fill=tk.X, padx=10, pady=4)

            # Beaky label (left side)
            tk.Label(
                self._stream_container,
                text="Beaky",
                bg=config.UI_BG_COLOR,
                fg=config.UI_BEAKY_COLOR,
                font=(config.UI_FONT_FAMILY, 10, "bold"),
            ).pack(side=tk.LEFT, padx=(0, 8))

            # Message bubble
            self._stream_text = ""
            self._stream_bubble = tk.Label(
                self._stream_container,
                text=self._stream_text,
                bg=config.UI_BEAKY_COLOR,
                fg=config.UI_TEXT_COLOR,
                font=(config.UI_FONT_FAMILY, config.UI_FONT_SIZE),
                wraplength=500,
                justify=tk.LEFT,
                padx=12,
                pady=8,
                relief=tk.FLAT,
            )
            self._stream_bubble.pack(side=tk.LEFT, padx=(0, 5))

            # Timestamp
            tk.Label(
                self._stream_container,
                text=timestamp,
                bg=config.UI_BG_COLOR,
                fg="#666666",
                font=(config.UI_FONT_FAMILY, 9),
            ).pack(side=tk.LEFT, padx=(5, 0))

        self._stream_text += token
        self._stream_bubble.configure(text=self._stream_text)
        self._auto_scroll()

    def _finalize_stream(self):
        """Mark the current streaming bubble as complete."""
        self._stream_bubble = None
        self._stream_text = ""

    def _auto_scroll(self):
        """Scroll to the bottom of the conversation."""
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def _update_volume(self, level: float):
        """Update the volume meter bar (level from 0.0 to 1.0)."""
        if not hasattr(self, '_volume_canvas'):
            return
        width = self._volume_canvas.winfo_width()
        bar_width = int(width * min(level, 1.0))

        # Color based on level
        if level > 0.5:
            color = "#4ade80"  # Green - good level
        elif level > 0.1:
            color = "#facc15"  # Yellow - okay level
        else:
            color = "#64748b"  # Gray - quiet

        self._volume_canvas.coords(self._volume_bar, 0, 0, bar_width, 16)
        self._volume_canvas.itemconfig(self._volume_bar, fill=color)

    def _start_speaking_animation(self):
        """Start pulsing animation when Beaky speaks."""
        self._speaking = True
        self._pulse_count = 0
        self._animate_speaking()

    def _stop_speaking_animation(self):
        """Stop speaking animation."""
        self._speaking = False

    def _animate_speaking(self):
        """Pulse the volume bar when Beaky is speaking."""
        if not self._speaking or not hasattr(self, '_volume_canvas'):
            return

        # Create a pulsing effect
        import math
        pulse = (math.sin(self._pulse_count * 0.3) + 1) / 2  # 0 to 1
        width = self._volume_canvas.winfo_width()
        bar_width = int(width * (0.3 + pulse * 0.4))  # Pulse between 30% and 70%

        self._volume_canvas.coords(self._volume_bar, 0, 0, bar_width, 16)
        self._volume_canvas.itemconfig(self._volume_bar, fill="#c084fc")  # Purple

        self._pulse_count += 1
        if self.root:
            self.root.after(50, self._animate_speaking)

    def _update_video(self, frame_bytes: bytes):
        """Update the video feed with a new frame."""
        import io
        import pickle
        import numpy as np
        from PIL import Image, ImageTk

        # Deserialize the frame
        frame = pickle.loads(frame_bytes)

        # Convert BGR to RGB
        rgb = frame[:, :, ::-1]

        # Resize to fit panel (maintain aspect ratio)
        height, width = rgb.shape[:2]
        max_width = 300
        scale = max_width / width
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Convert to PIL Image and resize
        img = Image.fromarray(rgb)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)

        # Update label
        self._video_label.configure(image=photo)
        self._video_label.image = photo  # Keep a reference

    def _update_vision_text(self, text: str):
        """Update the vision description text."""
        self._vision_text_label.configure(text=f"👁️ {text}")

    def _close(self, on_close=None):
        if on_close:
            on_close()
        if self.root:
            self.root.destroy()
            self.root = None
