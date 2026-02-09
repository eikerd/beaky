"""People memory — face recognition and name storage using a JSON file."""

import json
import logging
import os
from pathlib import Path

import numpy as np

import config

log = logging.getLogger(__name__)

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    log.warning("face_recognition not installed — people memory disabled")


class PeopleMemory:
    """Detect and recognise faces, associate them with names, persist to JSON."""

    def __init__(self, db_path: str = config.PEOPLE_DB_PATH):
        self.db_path = Path(db_path)
        self.tolerance = config.FACE_TOLERANCE
        self._people: list[dict] = []  # [{"name": str, "encoding": list[float]}, ...]
        self._load()

    # --- persistence ---

    def _load(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, "r") as f:
                    self._people = json.load(f)
                log.info("Loaded %d known people", len(self._people))
            except (json.JSONDecodeError, OSError) as e:
                log.error("Failed to load people DB: %s", e)
                self._people = []
        else:
            self._people = []

    def _save(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w") as f:
            json.dump(self._people, f, indent=2)
        log.info("Saved %d people to %s", len(self._people), self.db_path)

    # --- face operations ---

    def detect_faces(self, bgr_frame) -> list:
        """Return a list of face encodings found in a BGR OpenCV frame."""
        if not FACE_RECOGNITION_AVAILABLE:
            return []
        rgb = bgr_frame[:, :, ::-1]  # BGR → RGB
        locations = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, locations)
        log.info("Detected %d face(s)", len(encodings))
        return encodings

    def recognise(self, bgr_frame) -> str | None:
        """Try to recognise a person in the frame. Returns name or None."""
        encodings = self.detect_faces(bgr_frame)
        if not encodings:
            return None

        # Use the first (largest / most prominent) face
        target = encodings[0]
        return self._match(target)

    def _match(self, encoding) -> str | None:
        """Match an encoding against known people."""
        if not self._people:
            return None

        known_encodings = [np.array(p["encoding"]) for p in self._people]
        distances = face_recognition.face_distance(known_encodings, np.array(encoding))
        best_idx = int(np.argmin(distances))

        if distances[best_idx] <= self.tolerance:
            name = self._people[best_idx]["name"]
            log.info("Recognised: %s (distance=%.3f)", name, distances[best_idx])
            return name

        log.info("Unknown face (best distance=%.3f)", distances[best_idx])
        return None

    def remember(self, name: str, bgr_frame) -> bool:
        """Detect a face in the frame and store it with the given name. Returns True on success."""
        encodings = self.detect_faces(bgr_frame)
        if not encodings:
            log.warning("No face found to remember")
            return False

        encoding = encodings[0]

        # Update existing or add new
        existing = self._match(encoding)
        if existing:
            # Update the encoding for the existing person
            for p in self._people:
                if p["name"] == existing:
                    p["encoding"] = encoding.tolist()
                    p["name"] = name  # allow renaming
                    break
            log.info("Updated encoding for %s", name)
        else:
            self._people.append({
                "name": name,
                "encoding": encoding.tolist(),
            })
            log.info("Remembered new person: %s", name)

        self._save()
        return True

    @property
    def known_names(self) -> list[str]:
        return [p["name"] for p in self._people]
