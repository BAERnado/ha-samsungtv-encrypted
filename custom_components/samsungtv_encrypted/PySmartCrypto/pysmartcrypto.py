from __future__ import print_function
from . import crypto
import logging
import re
from .command_encryption import AESCipher
import requests
import time
import websocket
import threading

_LOGGER = logging.getLogger(__name__)


class PairingError(Exception):
    """Raised when Samsung TV pairing fails."""


class PySmartCrypto():
    UserId = "654321"
    AppId = "12345"
    deviceId =  "7e509404-9d7c-46b4-8f6a-e2a9668ad184"

    def disconnectCallback(self): self.close()

    def getFullUrl(self, urlPath):
        return "http://" + self._host + ":" + self._port + urlPath

    def GetFullRequestUri(self, step, appId, deviceId):
        return self.getFullUrl("/ws/pairing?step="+str(step)+"&app_id="+appId+"&device_id="+deviceId)

    def ShowPinPageOnTv(self):
        requests.post(self.getFullUrl("/ws/apps/CloudPINPage"), "pin4")

    def CheckPinPageOnTv(self):
        full_url = self.getFullUrl("/ws/apps/CloudPINPage")
        page = requests.get(full_url).text
        output = re.search('state>([^<>]*)</state>', page, flags=re.IGNORECASE)
        if output is not None:
            state = output.group(1)
            _LOGGER.debug("Current TV PIN page state: %s", state)
            if state == "stopped":
                return True
        return False

    def FirstStepOfPairing(self):
        firstStepURL = self.GetFullRequestUri(0, self.AppId, self.deviceId)+"&type=1"
        firstStepResponse = requests.get(firstStepURL).text

    def StartPairing(self):
        self._lastRequestId=0
        if self.CheckPinPageOnTv():
            _LOGGER.debug("PIN page is not open on TV, requesting it")
            self.ShowPinPageOnTv()
        else:
            _LOGGER.debug("PIN page is already open on TV")

    def HelloExchange(self, pin):
        hello_output = crypto.generateServerHello(self.UserId,pin)
        if not hello_output:
            return False
        content = "{\"auth_Data\":{\"auth_type\":\"SPC\",\"GeneratorServerHello\":\"" + hello_output['serverHello'].hex().upper() + "\"}}"
        secondStepURL = self.GetFullRequestUri(1, self.AppId, self.deviceId)
        secondStepResponse = requests.post(secondStepURL, content).text
        _LOGGER.debug("Received Samsung TV pairing step 1 response")
        output = re.search(r'request_id.*?(\d+).*?GeneratorClientHello.*?:.*?([0-9a-f]+)', secondStepResponse, flags=re.IGNORECASE)
        if output is None:
            _LOGGER.debug("Samsung TV pairing step 1 response did not include client hello")
            return False
        requestId = output.group(1)
        clientHello = output.group(2)
        self._lastRequestId = int(requestId)
        return crypto.parseClientHello(clientHello, hello_output['hash'], hello_output['AES_key'], self.UserId)

    def AcknowledgeExchange(self, SKPrime):
        serverAckMessage = crypto.generateServerAcknowledge(SKPrime)
        content="{\"auth_Data\":{\"auth_type\":\"SPC\",\"request_id\":\"" + str(self._lastRequestId) + "\",\"ServerAckMsg\":\"" + serverAckMessage + "\"}}"
        thirdStepURL = self.GetFullRequestUri(2, self.AppId, self.deviceId)
        thirdStepResponse = requests.post(thirdStepURL, content).text
        if "secure-mode" in thirdStepResponse:
            raise PairingError("TV requested secure-mode pairing, which is not implemented")
        output = re.search(r'ClientAckMsg.*?:.*?([0-9a-f]+).*?session_id.*?(\d+)', thirdStepResponse, flags=re.IGNORECASE)
        if output is None:
            _LOGGER.debug(
                "Samsung TV pairing step 2 response did not include session id or client ack: %s",
                thirdStepResponse,
            )
            raise PairingError("TV did not return session_id and ClientAckMsg")
        clientAck = output.group(1)
        if not crypto.parseClientAcknowledge(clientAck, SKPrime):
            raise PairingError("TV returned an invalid ClientAckMsg")
        sessionId=output.group(2)
        _LOGGER.debug("Samsung TV pairing returned session id")
        return sessionId

    def ClosePinPageOnTv(self):
        full_url = self.getFullUrl("/ws/apps/CloudPINPage/run");
        requests.delete(full_url)
        return False


    def connect(self):
        millis = int(round(time.time() * 1000))
        step4_url = 'http://' + self._host + ':8000/socket.io/1/?t=' + str(millis)
        websocket_response = requests.get(step4_url)
        websocket_url = 'ws://' + self._host + ':8000/socket.io/1/websocket/' + websocket_response.text.split(':')[0]
        # pairs to this app with this command.
        connection = websocket.create_connection(websocket_url)
        connection.send('1::/com.samsung.companion')
        return connection

    def control(self, key_command):
        self._connection.send(self._aesLib.generate_command(key_command))
        # need sleeps cuz if you send commands to quick it fails
        time.sleep(0.1)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        """Close the connection."""
        if hasattr(self, "_timer"):
            self._timer.cancel()
        self._connection.close()

    @classmethod
    def start_pairing(cls, host, port):
        pairing = cls.__new__(cls)
        pairing._lastRequestId = 0
        pairing._host = host
        pairing._port = str(port)
        pairing._connection = pairing.connect()
        pairing._timer = threading.Timer(120, pairing.disconnectCallback)
        pairing._timer.start()
        pairing.StartPairing()
        return pairing

    def finish_pairing(self, pin):
        self.FirstStepOfPairing()
        output = self.HelloExchange(pin)
        if not output:
            return None

        token = output['ctx'].hex()
        sessionid = self.AcknowledgeExchange(output['SKPrime'])
        self.ClosePinPageOnTv()
        self._token = token
        self._sessionid = sessionid
        self._aesLib = AESCipher(self._token.upper(), self._sessionid)
        return {"token": token, "sessionid": str(sessionid)}

    def __init__(self, host, port, token=None, sessionid=None, command=None):
        self._lastRequestId = 0

        self._host = host
        self._port = str(port)
        self._connection = self.connect()

        self._timer = threading.Timer(10, self.disconnectCallback)
        self._timer.start()

        if token is None and sessionid is None:
            self.StartPairing()
            token = False
            SKPrime = False
            while not token:
                tvPIN = input("Please enter pin from tv: ")
                print("Got pin: '"+tvPIN+"'\n")
                self.FirstStepOfPairing()
                output = self.HelloExchange(tvPIN)
                if output:
                    token = output['ctx'].hex()
                    SKPrime = output['SKPrime']
                    print("ctx: " + token)
                    print("Pin accepted :)\n")
                else:
                    print("Pin incorrect. Please try again...\n")

            sessionid = self.AcknowledgeExchange(SKPrime)
            print("SessionID: " + str(sessionid))
            self.ClosePinPageOnTv()
            print("Authorization successfull :)\n")

        self._token = token
        self._sessionid = sessionid

        self._aesLib = AESCipher(self._token.upper(), self._sessionid)

        if command is not None:
            _LOGGER.debug("Attempting to send command to TV")
            self.control(command)
