"""
Background worker threads for Ollama API operations
"""

import json
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class OllamaWorker(QThread):
    """Worker thread for streaming chat responses from Ollama"""

    token_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model, prompt, system_prompt="", temp=0.7, max_tokens=2000):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.temp = temp
        self.max_tokens = max_tokens
        self.is_running = True

    def run(self):
        """Execute the API request in background thread"""
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": self.model,
                "prompt": self.prompt,
                "stream": True,
                "options": {
                    "temperature": self.temp,
                    "num_predict": self.max_tokens
                }
            }

            if self.system_prompt:
                payload["system"] = self.system_prompt

            response = requests.post(url, json=payload, stream=True)

            for line in response.iter_lines():
                if not self.is_running:
                    break
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        self.token_received.emit(data["response"])
                    if data.get("done", False):
                        break

            self.finished.emit()

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
                if line:
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

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Stop the download"""
        self.is_running = False