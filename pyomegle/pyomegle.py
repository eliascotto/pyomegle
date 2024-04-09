from __future__ import division
import mechanize
import threading
import urllib
import random
import time
import json
import re


class EventThread(threading.Thread):

    def __init__(self, instance, start_url):
        threading.Thread.__init__(self)
        self.instance = instance
        self.start_url = start_url
        self._stop = threading.Event()

    def run(self):
        try:    
            response = self.instance.browser.open(self.start_url)
        except Exception as ex:
            print (str(ex))
            return

        try:
            data = json.load(response)
        except ValueError as ex:
            print (str(ex))

        try:
            self.instance.client_id = data['clientID']
            self.instance._handle_events(data['events'])
        except KeyError:
            if not len(response.read()):
                print("(Blank server response) Error connecting to server. Please try again.")
                print("If problem persists then your IP may be soft banned, try using a VPN.")

        while not self.instance.connected:
            self.instance._events_manager()
            if self._stop.isSet():
                self.instance.disconnect()
                return
            time.sleep(self.instance.event_delay)

        while self.instance.connected:
            self.instance._events_manager()
            if self._stop.isSet():
                self.instance.disconnect()
                return
            time.sleep(self.instance.event_delay)

    def stop(self):
        self._stop.set()


class Omegle(object):
    SERVER_LIST = [f'front{n}.omegle.com' for n in range(1, 33)]

    STATUS_URL =            'http://%s/status?nocache=%s&randid=%s'
    START_URL =             'http://%s/start?caps=recaptcha2,t3&firstevents=%s&spid=%s&randid=%s&cc=%s&lang=%s'
    RECAPTCHA_URL =         'http://%s/recaptcha'
    EVENTS_URL =            'http://%s/events'
    TYPING_URL =            'http://%s/typing'
    STOPPED_TYPING_URL =    'http://%s/stoppedtyping'
    DISCONNECT_URL =        'http://%s/disconnect'
    SEND_URL =              'http://%s/send'

    CHECK_URL = [f'http://waw{n}.omegle.com/check' for n in range(1, 4)]

    def __init__(self, events_handler, firstevents=1, spid='', random_id=None, topics=[], lang='en', event_delay=3):
        self.events_handler = events_handler
        self.firstevents = firstevents
        self.spid = spid
        self.topics = topics
        self.lang = lang
        self.event_delay = event_delay
        self.random_id = random_id or self._randID(8)

        self.connected = False

        self.server = random.choice(self.SERVER_LIST)
        self.client_id = None
        self.connected = False
        self.browser = mechanize.Browser()
        self.browser.addheaders = []

        self.check_id = self._checkID()

        # Call additional setup
        self.events_handler._setup(self)

    def _checkID(self):
        """ Retrive check ID for verification """
        url = random.choice(self.CHECK_URL)

        response = self._request(url, '')
        data = response.get_data().decode('UTF-8')

        return data

    def _randID(self, length):
        """ Generates a random ID for chat session """
        return ''.join([random.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ')
                        for _ in range(length)])

    def _handle_events(self, events):
        """ Handle the chat events """
        for event in events:
            try:
                self._event_selector(event)
            except TypeError as e:
                print (e)
                print ('DEBUG', event)
            continue

    def _event_selector(self, event):
        """ Select the correct events and call the handler """
        event_type = event[0]
        if event_type == 'waiting':
            self.events_handler.waiting()
        elif event_type == 'typing':
            self.events_handler.typing()
        elif event_type == 'connected':
            self.connected = True
            self.events_handler.connected()
        elif event_type == 'gotMessage':
            message = event[1]
            self.events_handler.message(message)
        elif event_type == 'commonLikes':
            likes = event[1]
            self.events_handler.common_likes(likes)
        elif event_type == 'stoppedTyping':
            self.events_handler.stopped_typing()
        elif event_type == 'strangerDisconnected':
            self.disconnect()
            self.events_handler.disconnected()
        elif event_type == 'recaptchaRequired':
            self.events_handler.captcha_required()
        elif event_type == 'recaptchaRejected':
            self.events_handler.captcha_rejected()
        elif event_type == 'serverMessage':
            message = event[1]
            self.events_handler.server_message(message)
        elif event_type == 'statusInfo':
            status = event[1]
            self.events_handler.status_info(status)
        elif event_type == 'identDigests':
            digests = event[1]
            self.events_handler.ident_digest(digests)
        else:
            print ('Unhandled event: %s' % event)

    def _request(self, url, data=None):
        """ Opens the url with data info """
        if not url:
            assert 'URL not valid for request'

        if data:
            data = urllib.parse.urlencode(data)

        response = self.browser.open(url, data)

        return response

    def _events_manager(self):
        """ Event manager class """
        url = self.EVENTS_URL % self.server
        data = {'id': self.client_id}
        try:
            response = self._request(url, data)
            data = json.load(response)
        except Exception:
            return False
        if data:
            self._handle_events(data)
        return True

    def status(self):
        """ Return connection status """
        nocache = '%r' % random.random()
        url = self.STATUS_URL % (self.server, nocache, self.random_id)

        response = self._request(url)
        data = json.load(response)

        return data

    def start(self):
        """ Start a new conversation """
        url = self.START_URL % (self.server, self.firstevents,
                                self.spid, self.random_id, self.check_id, self.lang)

        if self.topics:
            # Add custom topic to the url
            url += '&' + urllib.parse.urlencode({'topics': json.dumps(self.topics)})

        thread = EventThread(self, url)
        thread.start()
        self.thread = thread

        return thread

    def recaptcha(self, challenge, response):
        """ Captcha validation """
        url = self.RECAPTCHA_URL % self.server
        data = {'id': self.client_id, 'challenge':
                challenge, 'response': response}
        try:
            self._request(url, data)
            return True
        except Exception:
            return False

    def typing(self):
        """ Emulates typing in the conversation """
        url = self.TYPING_URL % self.server
        data = {'id': self.client_id}
        try:
            self._request(url, data)
            return True
        except Exception:
            return False

    def stopped_typing(self):
        """ Emulates stopped typing into the conversation """
        url = self.STOPPED_TYPING_URL % self.server
        data = {'id': self.client_id}
        try:
            self._request(url, data)
            return True
        except Exception:
            return False

    def send(self, message):
        """ Send a message """
        url = self.SEND_URL % self.server
        data = {'msg': message, 'id': self.client_id}
        try:
            self._request(url, data)
            return True
        except Exception:
            return False

    def disconnect(self):
        """ Disconnect from the current conversation """
        self.connected = False
        url = self.DISCONNECT_URL % self.server
        data = {'id': self.client_id}
        try:
            self.thread.stop()
            self._request(url, data)
            return True
        except Exception:
            return False


class OmegleHandler(object):
    """ Abstract class for defining Omegle event handlers """

    RECAPTCHA_CHALLENGE_URL = 'http://www.google.com/recaptcha/api/challenge?k=%s'
    RECAPTCHA_IMAGE_URL = 'http://www.google.com/recaptcha/api/image?c=%s'
    recaptcha_challenge_regex = re.compile(r"challenge\s*:\s*'(.+)'")

    def __init__(self, loop=False):
        self.loop = loop
    
    def _setup(self, omegle):
        """ Called by the Omegle class for initial additional settings """
        self.omegle = omegle
    
    def waiting(self):
        """ Called when we are waiting for a stranger to connect """
        print ('Looking for someone you can chat with...')

    def connected(self):
        """ Called when we are connected with a stranger """
        print ('You\'re now chatting with a random stranger. Say hi!')

    def typing(self):
        """ Called when the user is typing a message """
        print ('Stranger is typing...')

    def stopped_typing(self):
        """ Called when the user stop typing a message """
        print ('Stranger has stopped typing.')
    
    def message(self, message):
        """ Called when a message is received from the connected stranger """
        print ('Stranger: %s' % message)

    def common_likes(self, likes):
        """ Called when you and stranger likes the same thing """
        print ('You both like %s.' % ', '.join(likes))
    
    def disconnected(self):
        """ Called when a stranger disconnects """
        print ('Stranger has disconnected.')

        if self.loop:   # new session
            self.omegle.start()
    
    def captcha_required(self):
        """ Called when the server asks for captcha """
        url = self.RECAPTCHA_CHALLENGE_URL % challenge
        source = self.browser.open(url).read()
        challenge = recaptcha_challenge_regex.search(source).groups()[0]
        url = self.RECAPTCHA_IMAGE_URL % challenge

        print ('Recaptcha required: %s' % url)
        response = raw_input('Response: ')

        self.omegle.recaptcha(challenge, response)

    def captcha_rejected(self):
        """ Called when server reject captcha """
        pass

    def server_message(self, message):
        """ Called when the server report a message """
        print (message)

    def status_info(self, status):
        """ Status info received from server """
        pass

    def ident_digest(self, digests):
        """ Identity digest received from server """
        pass


class OmegleClient(Omegle):

    def __init__(self, events_handler, wpm=42,
                firstevents=1, spid='', random_id=None, topics=[], lang='en', event_delay=3):
        super(OmegleClient, self).__init__(
            events_handler, firstevents, spid,
            random_id, topics, lang, event_delay)
        self.wpm = wpm

    def _typingtime(self, msglen):
        """ Calculates typing time in WPM """
        return (60 / self.wpm) * (msglen / 5)

    def write(self, message):
        """ Simulates a message completely written """
        msglen = len(message)
        typingtime = self._typingtime(msglen)

        self.typing()
        time.sleep(typingtime)
        self.send(message)

    def typing(self):
        """ Emulates typing in the conversation """
        super(OmegleClient, self).typing()
        print ('You currently typing...')

    def send(self, message):
        """ Sends a message """
        super(OmegleClient, self).send(message)
        print ('You: %s' % message)

    def next(self):
        """ Starts with a new conversation """
        self.disconnect()
        self.start()
