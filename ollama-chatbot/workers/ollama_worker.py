"""
Background worker threads for Ollama API operations
"""

import json
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class OllamaWorker(QThread):
    """Worker thread for streaming chat responses from Ollama"""

    token_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model, messages, system_prompt="", temp=0.7, max_tokens=2000):
        super().__init__()
        self.model = model
        self.messages = messages
        self.system_prompt = system_prompt
        self.temp = temp
        self.max_tokens = max_tokens
        self.is_running = True

    def run(self):
        """Execute the API request in background thread"""
        try:
            url = "http://localhost:11434/api/chat"

            # Build the messages list; prepend system message if provided
            # without mutating the passed-in list
            messages_to_send = []
            if self.system_prompt:
                messages_to_send.append({"role": "system", "content": self.system_prompt})
            messages_to_send.extend(self.messages)

            payload = {
                "model": self.model,
                "messages": messages_to_send,
                "stream": True,
                "options": {
                    "temperature": self.temp,
                    "num_predict": self.max_tokens
                }
            }

            response = requests.post(url, json=payload, stream=True)

            # Flush strategy: emit a batch when ANY of these is true:
            #   • 24 ms have elapsed since the last flush (~42 fps ceiling).
            #     42 fps is imperceptible as lag but saves ~30 % of signal
            #     emissions compared with 60 fps, since Qt repaints cannot
            #     keep up with 60 fps anyway.
            #   • buffer has ≥ 3 characters (minimum meaningful chunk).
            #     3 rather than 8 so slow models don't stall visibly while
            #     waiting for the buffer to fill.
            #   • the buffer ends on a sentence boundary (`. `, `! `, `? `,
            #     `\n`) and has ≥ 3 chars — prose then appears in semantic
            #     units rather than at arbitrary timer ticks.
            #   • the stream signals done=True.
            FLUSH_INTERVAL = 0.024   # seconds (~42 fps)
            MIN_BUFFER_SIZE = 3      # characters
            SENTENCE_ENDS = (". ", "! ", "? ", "\n")

            buffer = ""
            last_flush = time.monotonic()

            for line in response.iter_lines():
                if not self.is_running:
                    break

                # iter_lines() can yield bytes on some requests versions or
                # encodings — decode defensively before any string operation.
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                if not line:
                    continue

                data = json.loads(line)

                if "message" in data:
                    token = data["message"].get("content", "")
                    # Guard against bytes leaking through the JSON deserialiser
                    if isinstance(token, bytes):
                        token = token.decode("utf-8", errors="replace")
                    buffer += token

                done = data.get("done", False)

                # Evaluate all flush conditions
                now = time.monotonic()
                elapsed = now - last_flush
                sentence_end = any(buffer.endswith(s) for s in SENTENCE_ENDS)

                if buffer and len(buffer) >= MIN_BUFFER_SIZE and (
                    elapsed >= FLUSH_INTERVAL
                    or sentence_end
                    or done
                ):
                    self.token_received.emit(buffer)
                    buffer = ""
                    last_flush = now

                if done:
                    break

            # Flush any remaining content that didn't meet the flush threshold
            if buffer:
                self.token_received.emit(buffer)

            self.finished.emit()
            # Exit the QThread event loop so the thread is immediately eligible
            # for garbage collection rather than lingering in a stopped state.
            self.quit()

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Stop the worker thread"""
        self.is_running = False


class ModelDownloadWorker(QThread):
    """Worker thread for downloading Ollama models"""

    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
        self.is_running = True

    def run(self):
        """Download the specified model"""
        try:
            url = "http://localhost:11434/api/pull"
            payload = {"name": self.model_name, "stream": True}

            response = requests.post(url, json=payload, stream=True)

            for line in response.iter_lines():
                if not self.is_running:
                    break

                # Decode bytes defensively before string operations
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                if not line:
                    continue

                data = json.loads(line)
                status = data.get("status", "")

                if "total" in data and "completed" in data:
                    total = data["total"]
                    completed = data["completed"]
                    percent = (completed / total * 100) if total > 0 else 0
                    self.progress.emit(f"{status}: {percent:.1f}%")
                else:
                    self.progress.emit(status)

            self.finished.emit()
            # Exit the QThread event loop cleanly after download completes
            self.quit()

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Stop the download"""
        self.is_running = False