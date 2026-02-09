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

        # -- scrollable conversation area --
        container = tk.Frame(self.root, bg=config.UI_BG_COLOR)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

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
                    else:
                        self._status_bar.configure(bg="#0d0d1a", fg="#888888")  # Default gray
        except queue.Empty:
            pass

        if self.root:
            self.root.after(50, self._poll_queue)

    def _add_bubble(self, text: str, is_user: bool):
        """Add a full message bubble to the conversation."""
        anchor = "e" if is_user else "w"
        bg = config.UI_USER_COLOR if is_user else config.UI_BEAKY_COLOR
        label_text = f"You: {text}" if is_user else f"Beaky: {text}"

        bubble = tk.Label(
            self._scroll_frame,
            text=label_text,
            bg=bg,
            fg=config.UI_TEXT_COLOR,
            font=(config.UI_FONT_FAMILY, config.UI_FONT_SIZE),
            wraplength=700,
            justify=tk.LEFT,
            padx=14,
            pady=10,
            anchor="w",
        )
        bubble.pack(anchor=anchor, padx=10, pady=4, fill=tk.X if not is_user else tk.NONE)
        self._auto_scroll()

    def _append_stream(self, token: str):
        """Append a token to the current streaming bubble."""
        if not hasattr(self, "_stream_bubble") or self._stream_bubble is None:
            # Create a new bubble for streaming
            self._stream_text = "Beaky: "
            self._stream_bubble = tk.Label(
                self._scroll_frame,
                text=self._stream_text,
                bg=config.UI_BEAKY_COLOR,
                fg=config.UI_TEXT_COLOR,
                font=(config.UI_FONT_FAMILY, config.UI_FONT_SIZE),
                wraplength=700,
                justify=tk.LEFT,
                padx=14,
                pady=10,
                anchor="w",
            )
            self._stream_bubble.pack(anchor="w", padx=10, pady=4)

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

    def _close(self, on_close=None):
        if on_close:
            on_close()
        if self.root:
            self.root.destroy()
            self.root = None
