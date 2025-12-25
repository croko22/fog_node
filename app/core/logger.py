class GuiLogger:
    _instance = None
    _callback = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GuiLogger, cls).__new__(cls)
        return cls._instance

    def set_callback(self, callback):
        self._callback = callback

    def log(self, message: str):
        if self._callback:
            self._callback(message)
        else:
            print(f"[NO-GUI-LOG] {message}")

gui_logger = GuiLogger()
