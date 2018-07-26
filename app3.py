#!/usr/bin/python
import json
import time
import sys
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
import re
import threading
import RPi.GPIO as GPIO
import logging
from logging.handlers import TimedRotatingFileHandler
#TIMEOUT = 241000
#TIMER_LOCK = 5
#MINIMUM_POLLING_TIME = 9
#MESSAGE_TIMEOUT = 10000

MESSAGE_COUNT = 0
MESSAGE_STATUS = False
MESSAGE_LASTWILL = False


PROTOCOL = IoTHubTransportProvider.MQTT
MSG_STATUS = "{\"DeviceID\": \"%s\", \"Status\": %s}"
MSG_LASTWILL = "{\"DeviceID\": \"%s\", \"Still alive\"}"
CONNECTION_STRING = "HostName=scf-test.azure-devices.net;DeviceId=3;SharedAccessKey=GF6qdxaqPPIrlEqKkzwu2qEftxy4cnZbm/Y6XEHhqkE="
prev_will_msg = time.time()
auto_lock_timer = 7 
OPEN = "OPEN"
CLOSED = "CLOSED"
locks = {1:7, 2:11, 3:12, 4:15, 5:16, 6:18, 7:19, 8:21, 9:22, 10:23, 11:24}
lock_timer_array = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0}
lock_input = {2:16, 3:18, 4:19}
lock_status = {1:CLOSED, 2:CLOSED, 3:CLOSED, 4:CLOSED, 5:CLOSED, 6:CLOSED, 7:CLOSED, 8:CLOSED, 9:CLOSED, 10:CLOSED, 11:CLOSED}


myID = 1   # "b9baebb5-bb66-41d0-af73-35e76063af80"

# Map of GPIO pins to lock number
#   P7  = Lock 1
#   P11 = Lock 2
#   P12 = Lock 3
#   P15 = Lock 4
#   P16 = Lock 5
#   P18 = Lock 6
#   P19 = Lock 7
#   P21 = Lock 8
#   P22 = Lock 9
#   P23 = Lock 10
#   P24 = Lock 11
def locks_init():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(7, GPIO.OUT)
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(12, GPIO.OUT)
    GPIO.setup(15, GPIO.OUT)
    GPIO.setup(16, GPIO.OUT)
    GPIO.setup(18, GPIO.OUT)
    GPIO.setup(19, GPIO.OUT)
    GPIO.setup(21, GPIO.OUT)
    GPIO.setup(22, GPIO.OUT)
    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(24, GPIO.OUT)
    GPIO.output(7, GPIO.LOW)
    GPIO.output(11, GPIO.LOW)
    GPIO.output(12, GPIO.LOW)
    GPIO.output(15, GPIO.LOW)
    GPIO.output(16, GPIO.LOW)
    GPIO.output(18, GPIO.LOW)
    GPIO.output(19, GPIO.LOW)
    GPIO.output(21, GPIO.LOW)
    GPIO.output(22, GPIO.LOW)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(24, GPIO.LOW)


def lock_open(number):
    global lock_timer_array, lock_status
    GPIO.output(locks[number], 1)
    lock_timer_array[number] = time.time()
    lock_status[number] = OPEN
    time.sleep(0.01)
    logger.debug("Opened door %d", number)
    return OPEN

def lock_close(number):
    global lock_timer_array, lock_status
    GPIO.output(locks[number], 0)
    lock_timer_array[number] = 0
    lock_status[number] = CLOSED
    time.sleep(0.01)
    logger.debug("Closed door %d", number)
    return CLOSED

def lock_manager():
    global MESSAGE_LASTWILL, prev_will_msg, lock_status
    while True:
        end = time.time()
        for key in locks:
            if(lock_timer_array[key] != 0 and (end-lock_timer_array[key]) > auto_lock_timer):
                lock_close(key)
        if(time.time()-prev_will_msg > 60):
            MESSAGE_LASTWILL = True
            prev_will_msg = time.time()
        time.sleep(1)
            
def repairman(error):
    
    print("repairman")
    return 0

def event_handler(event, data):
    global MESSAGE_STATUS, lock_status, auto_lock_timer
    if(event == "GetStatus"):
        response = json.dumps(lock_status)
        return response
    if(event == "Open"): 
        if (data["timer"] != auto_lock_timer):
            auto_lock_timer = data["timer"]
        lock_nr = int(data["lock"])
        if(lock_nr < 5 and lock_nr > 1):
            lock_status[lock_nr] = lock_open(lock_nr)
            return ( "{\"Response\": \"%s\" }" % lock_status[lock_nr] )
        else:
            return ( "{\"Response\": \"Not valid lock\" }" )
    return "OK"

    


def device_method_callback(method_name, payload, user_context):
    global MESSAGE_STATUS, myTimer, status_msg
    device_method_return_value = DeviceMethodReturnValue()
    device_method_return_value.response = "{\"Response\": \"OK\" }"
    device_method_return_value.status = 200
    data = json.loads(payload)
    logger.info("Received event: %s", method_name)
    device_method_return_value.response = event_handler(method_name,data)
    logger.debug("Ending callback with event: %s, and response: %s", method_name, device_method_return_value.response)
    return device_method_return_value

def send_confirmation_callback(message, result, user_context):
    logger.info ( "Message call confirmed\n " )

def iothub_client_init():
    logger.info("Initializing iothub_client")
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)
    if client.protocol == IoTHubTransportProvider.MQTT:
        client.set_option("logtrace", 0)
    client.set_device_method_callback(device_method_callback, 0)
    return client

def print_last_message_time(client):
    try:
        last_message = client.get_last_message_receive_time()
        logger.debug ( "Last Message: %s\n" , time.asctime(time.localtime(last_message)) )
        logger.debug ( "Actual time : %s\n" , time.asctime() )
    except IoTHubClientError as iothub_client_error:
        if iothub_client_error.args[0].result == IoTHubClientResult.INDEFINITE_TIME:
            logger.debug ( "No message received\n" )
        else:
            print ( iothub_client_error )
OKAY = "OKAY"
def safebikely_run():
    try:
        logger.info("Starting main thread")
        client = iothub_client_init()
        while True:
            global MESSAGE_STATUS, MESSAGE_LASTWILL
            if MESSAGE_STATUS:
                msg_formatted = MSG_STATUS % (myID,OKAY)
                message = IoTHubMessage(msg_formatted)

                logger.info ("Sending msg: %s", msg_formatted)

                client.send_event_async(message, send_confirmation_callback, MESSAGE_COUNT)
                MESSAGE_STATUS = False
            if MESSAGE_LASTWILL:
                msg_formatted = MSG_LASTWILL % myID
                message = IoTHubMessage(msg_formatted)
                message.message_id = "message_%d" % MESSAGE_COUNT
                message.correlation_id = "correlation_%d" % MESSAGE_COUNT
                logger.info("Sending LastWill message")
                client.send_event_async(message, send_confirmation_callback, MESSAGE_COUNT)
                MESSAGE_LASTWILL = False
            time.sleep(0.1)
    except KeyboardInterrupt as error:
        logger.debug("Error %s",error)
        print_last_message_time(client)
    except Exception as error:
        logger.debug("Error %s", error)

def parse_iot_hub_name():
    m = re.search("HostName=(.*?)\.", CONNECTION_STRING)
    return m.group(1)

if __name__ == "__main__":
    logHandler = TimedRotatingFileHandler("/var/log/safebikely.log", when="midnight",backupCount=7)
    logFormatter = logging.Formatter('%(asctime)s %(message)s')
    logHandler.setFormatter(logFormatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)

    locks_init()
    try:
        logger.info("Trying to create second thread")
        thread = threading.Thread(target=lock_manager)
        thread.daemon = True
        thread.start()
    except Exception as error:
        logger.debug("Failed starting second thread with error: %s", error) 
    safebikely_run()
