
TL = (3800, 3900)
TR = (300, 3900)
BL = (3800, 300)
BR = (300, 300)

class MSP3520:
    def __init__(self):
        super().__init__()
        """
        BL
        |disp_x|disp_y|touch_x|touch_y|        
        | 0    | 0    | 3800  | 300   |
        
        BR
        |disp_x|disp_y|touch_x|touch_y|        
        | 0    | 480  | 300   | 300   |
        
        TL
        |disp_x|disp_y|touch_x|touch_y|        
        | 0    | 0    | 3800  | 300   |
        
        BR
        |disp_x|disp_y|touch_x|touch_y|        
        | 0    | 480  | 300   | 300   |
        """
        self.x_min = min(TL[0], BL[0])
        self.x_max = max(TR[0], BR[0])

        self.y_min = min(TR[1], TL[1])
        self.y_max = max(BR[1], BL[1])

        self.width = 320
        self.height = 480

    def map(self, raw_x, raw_y):
        # Normalize to pixel coords
        px = (raw_x - self.x_min) * self.width / (self.x_max - self.x_min)
        py = (raw_y - self.y_min) * self.height / (self.y_max - self.y_min)

        px = max(0, min(self.width - 1, int(px)))
        py = max(0, min(self.height - 1, int(py)))
        return px, py