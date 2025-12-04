class RadioClient:
    def __init__(self):
        super().__init__()

        self.play = False
        self.station = 1

    def toggle_play(self):
        self.play = not self.play
        return self.play
