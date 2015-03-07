# Pyomegle
Python API for Omegle webchat.
Inspired by [brianewing](https://github.com/brianewing/pyomegle)

# Usage
``` python
from pyomegle import OmegleBot, OmegleHandler

"""
    Omegle inteface for python

    /next
        starts a new conversation
    /exit
        exits chat session
"""

h = OmegleHandler(loop=True)
c = OmegleBot(h, wpm=47, lang='it')
c.start()

while 1:
    input_str = raw_input('') #string input

    if input_str.strip() == '/next':
        c.next()
    elif input_str.strip() == '/exit':
        c.disconnect()
        break
    else:
        c.send(input_str)
```