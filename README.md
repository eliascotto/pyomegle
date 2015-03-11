Pyomegle
==================
Python API for Omegle webchat.
Inspired by [brianewing](https://github.com/brianewing/pyomegle).

Installation
==================
```sh
$ pip install pyomegle
```
pyomegle depends on [mechanize](http://wwwsearch.sourceforge.net/mechanize/). For this reason Python 3 is not currently supported.

Usage
==================
``` python
from pyomegle import OmegleClient, OmegleHandler

"""
    Omegle inteface for python

    /next
        starts a new conversation
    /exit
        exits chat session
"""

h = OmegleHandler(loop=True)            # session loop
c = OmegleClient(h, wpm=47, lang='en')  # 47 words per minute
c.start()

while 1:
    input_str = raw_input('')           # string input

    if input_str.strip() == '/next':
        c.next()                        # new conversation
    elif input_str.strip() == '/exit':
        c.disconnect()                  # disconnect chat session
        break
    else:
        c.send(input_str)               # send string
```

Events
----------
List of events accessible by ``OmegleHandler``. Note that ``OmegleHandler`` uses a ``loop`` optional initial parameter, valid for reconnect with a new stranger when ``disconnected()`` event is called from the server.

* **waiting()** Called when we are waiting for a stranger to connect
* **connected()**  Called when we are connected with a stranger
* **typing()** Called when the user is typing a message
* **stopped_typing()** Called when the user stop typing a message
* **message(message)** Called when a message is received from the connected stranger
* **common_likes(likes)** Called when you and stranger likes the same thing
* **disconnected()** Called when a stranger disconnects 
* **captcha_required()** Called when the server asks for captcha
* **captcha_rejected()** Called when server reject captcha
* **server_message(message)** Called when the server report a message
* **status_info(status)** Status info received from server
* **ident_digest(digests)** Identity digest received from server

Inherit ``OmegleHandler`` class for implement your custom events.

``` python
class MyCustomHandler(OmegleHandler):

    def connected(self):
        super(MyCustomHandler, self).connected()

        self.omegle.send('Hi!')
```

Client
----------
``OmegleClient`` uses some optional initial parameters, the most useful

* **lang='en'** for set a default chat language
* **wpm=42** set the ``words per minutes`` typing speed
* **topics=[]** list of interests
* **event_delay=3** server polling delay in seconds


List of client methods

* **start()** Start a new conversation
* **status()** Return connection status
* **write(message)** Simulates a message completely written whit typing time
* **typing()** Emulates typing in the conversation
* **stopped_typing()** Emulates stopped typing into the conversation
* **send(message)** Sends a message
* **recaptcha(challenge, response)** Captcha validation
* **next()** Starts with a new conversation
* **disconnect()**  Disconnect from the current conversation