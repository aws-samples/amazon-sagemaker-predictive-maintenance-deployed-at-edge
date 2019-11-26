#
# Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This Greengrass example simulates an IoT Sensor sending data to Greengrass at a fixed interval.
# In addition the IoT device also sends a message to update the thing shadow.

# Please refer to the AWS Greengrass Getting Started Guide, Module 5 for more information.
#

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient, AWSIoTMQTTClient
import sys
import logging
import time
import json
import argparse
import os
import re
from itertools import cycle
import random
from gg_discovery_api import GGDiscovery


from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException

MAX_DISCOVERY_RETRIES = 10    # MAX tries at discovery before giving up
GROUP_PATH = "./groupCA/"     # directory storing discovery info
CA_NAME = "root-ca.crt"       # stores GGC CA cert
GGC_ADDR_NAME = "ggc-host"    # stores GGC host address



# Custom Shadow callback for updating the desired state in the shadow
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~Shadow Update Accepted~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]["desired"]["property"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        shadow_update_topic = '$aws/things/' + clientId + '/shadow/update'
        logger.info("reporting state to shadow: " + shadow_update_topic)
        myAWSIoTMQTTClient.publish(shadow_update_topic, json.dumps(str(payloadDict["state"]["desired"]["property"]), indent=4), 0)
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

# function does basic regex check to see if value might be an ip address
def isIpAddress(value):
    match = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}', value)
    if match:
        return True
    return False
    
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
print("--------------\n\n")

AllowedActions = ['both', 'publish', 'subscribe']

# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="Iot-Sensor",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sensor/test/python", help="Targeted topic")
parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("--connect-to", action="store", dest="connectTo", default="greengrass", help="Where to connect to. Can be either awsiot or greengrass")

                    
args = parser.parse_args()
host = args.host
iotCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
thingName = args.thingName
clientId = args.clientId
port = args.port
useWebsocket = args.useWebsocket
topic = args.topic
connectTo = args.connectTo
coreCAFile = "core-CAs.crt"


# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)   # set to logging.DEBUG for additional logging
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


rootCAPath = iotCAPath
if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
    port = 443
if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
    port = 8883
    

if connectTo == "greengrass":
    CAFile = coreCAFile
    logger.info("connecting to GREENGRASS: starting discover")
    print("starting discover")
    discovery = GGDiscovery(clientId, host, 8443, rootCAPath, certificatePath, privateKeyPath)

myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5) # 5 sec


myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)


#myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
#myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
#myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
#myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
#myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
#myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
#myAWSIoTMQTTShadowClient.connect()
#deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

# This loop simulates an IoT sensor generating a random number corresponding to the reading of a piece of equipment.
# This data will be fed into a lambda function which will generate a response after invoking an ML model.
shadow_topics = '$aws/things/' + clientId + '/shadow/update'
loopCount = 0
do = True
while do: 
    JSONPayload = '{"state":{"desired":{"property":' + '"' + str(random.random()) + '"}}}'
    print(JSONPayload)
    myAWSIoTMQTTClient.publish(topic, JSONPayload, 1)
    logger.info("subscribe and set sdwCallback: topic: " + shadow_topics)
    myAWSIoTMQTTClient.subscribe(shadow_topics, 0, customShadowCallback_Update)
    logger.info("reporting state to shadow: " + shadow_topics)
    myAWSIoTMQTTClient.publish(shadow_topics, JSONPayload, 0)
 #   myAWSIoTMQTTClient.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)
    loopCount += 1
    time.sleep(20)
    