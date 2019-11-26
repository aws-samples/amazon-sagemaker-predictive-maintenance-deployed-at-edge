#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 22:42:10 2019

@author: stenatu

Lambda function triggered whenever anything is published to the SNS topic. Once
Lambda is triggered, it will initiate Amazon Polly speech synthesis API to generate 
an mp3 file which is uploaded to s3. 
The file can subsequently be downloaded to the on prem factory servers for 
playing over a PA system.

"""

import boto3
import os
import logging
import uuid
from contextlib import closing

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    logger.setLevel(logging.DEBUG)
    logger.debug("Event is --- %s" %event)
    #pull out the message
    speak = event["Records"][0]["Sns"]["Message"]  #extracts the message from SNS topic
    logger.debug(speak)
	
	# Converting the Subject text of the SNS message to into an mp3 audio file.
	# Calls the Polly API

    polly = boto3.client('polly')
    response = polly.synthesize_speech( OutputFormat='mp3',
                                        Text = 'ALERT !' + speak, # synthesize the alert using Polly
                                        SampleRate='22050', # TODO: experiment with different sample rates
                                        VoiceId = os.environ['VoiceId']  # TODO: experiment with different voice Ids
                                        )
    logger.debug("Polly Response is-- %s" %response)
    id = str(uuid.uuid4())
    logger.debug("ID= %s" %id)
    
    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            filename=id + ".mp3"
            output = os.path.join("/tmp/",filename)
            with open(output, "wb") as file:
                file.write(stream.read())

    s3 = boto3.client('s3')
    s3upload_response = s3.upload_file('/tmp/' + filename, os.environ['BUCKET_NAME'],filename,ExtraArgs={"ContentType": "audio/mp3"})
    logger.debug("S3 UPLOAD RESPONSE IS--- %s" %s3upload_response)
    
    
    location = s3.get_bucket_location(Bucket=os.environ['BUCKET_NAME'])
    logger.debug("Location response is -- %s" %location)
    region = location['LocationConstraint']
    
    if region is None:
    	url_begining = "https://s3.amazonaws.com/"
    else:
    	url = url_begining + str(os.environ['BUCKET_NAME']) + "/" + filename
    
    url = '{}/{}/{}'.format(s3.meta.endpoint_url, os.environ['BUCKET_NAME'], filename)
    print(url)
    return 
    
