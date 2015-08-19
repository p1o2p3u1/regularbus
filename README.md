python coverage test tool in real time. 

## Install

```
python setup.py install
```

## How to use

```python
# before the project start

from regularbus import regularbus
r = regularbus.RegularBus('0.0.0.0', '9000')
r.lets_go()

# then the source code
...
```

## Attention

Because it will start a websocket server and it is started in a single thread, then if your project also need to listen to a port, you need to run your project with thread too.

For example in Flask
```python
from regularbus import regularbus
import threading
from flask import Flask


app = Flask(__name__)

if __name__ == '__main__':
    bus = RegularBus('localhost', 9000)
    bus.lets_go()
    threading.Thread(
        target=app.run,
        args=('0.0.0.0', 8888,),
        kwargs={
            'threaded': True
        }).start()
```

And in some game server
```python
if __name__ == '__main__':
    bus = RegularBus('localhost', 9000)
    bus.lets_go()
    threading.Thread(target=gameserver.run).start()
```