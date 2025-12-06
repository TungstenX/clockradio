import time

import event_emitter as events

print(str(time.time()))

class T1:
    def __init__(self, em):
        super().__init__()
        self.em = em
        self.em.on('hello', self.hello)

    def hello(self, x:int, y:int):
        print('Hello {},{}'.format(x,y))



class T2:
    def __init__(self):
        super().__init__()
        self.x = 10
        self.y = 20
        self.em = events.EventEmitter()

    def fire(self):
        # em = events.EventEmitter()
        self.em.emit('hello', x=self.x, y=self.y)

if __name__ == "__main__":

    t2 = T2()
    t1 = T1(t2.em)
    t2.fire()