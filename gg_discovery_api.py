#
# gg-discovery-api.py
#
# python class for the Greengrass Discovery API
# Returns the response document for a given thing.
# Can be used to get the root-ca for a GG-Core.
#
# Documentation: http://docs.aws.amazon.com/greengrass/latest/developerguide/gg-discover-api.html
#
# Create a thing with e.g. gg-discover in AWS IoT and download key/cert file
# The policy mentioned in the official documentation did not work for me but
# the following policy did the job:
#
# {
#  "Version": "2012-10-17",
#  "Statement": [
#    {
#      "Effect": "Allow",
#      "Action": [
#        "greengrass:Discover"
#      ],
#      "Resource": "*"
#    }
#  ]
# }

# usage:
# discovery = GGDiscovery(THING_NAME,
#    IOT_ENDPOINT,
#    PORT, ROOT_CA_FILE,
#    THING_CERT_FILE, THING_KEY_FILE)
# print("discovery url: " + discovery.url)
# (status, response_document) = discovery.discovery()
# print("status: " + str(status))
# print("response_document: " + json.dumps(response_document, indent=4))



import json
import logging
import urllib3
import re
import sys


class GGDiscovery:

    def __init__(self, ggad, iot_host, iot_port, ca_cert, cert, key):
        self.ggad = ggad
        self.iot_host = iot_host
        self.iot_port = iot_port
        self.ca_cert = ca_cert
        self.cert = cert
        self.key = key
        self.proxy = ""
        self.url = "https://" + iot_host + ":" + str(iot_port) + "/greengrass/discover/thing/" + ggad

    def discovery(self):
        http = ""
        if not self.proxy:
            http = urllib3.PoolManager(
                ca_certs=self.ca_cert,
                cert_reqs='CERT_REQUIRED',
                key_file=self.key,
                cert_file=self.cert)
        else:
            http = urllib3.ProxyManager(
                self.proxy,
                ca_certs=self.ca_cert,
                cert_reqs='CERT_REQUIRED',
                key_file=self.key,
                cert_file=self.cert)

        r = http.request('GET', self.url)
        self.status = str(r.status)
        self.response_document = json.loads(r.data.decode())

        return(self.status, self.response_document)

    def num_gggroups(self):
        self.num_gggroups = len(self.response_document['GGGroups'])
        return len(self.response_document['GGGroups'])

    def num_cas(self):
        end = self.num_gggroups()
        start = end - 1
        for i in range(start, end):
            print(i)
        self.num_cas = len(self.response_document['GGGroups'])
        return len(self.response_document['GGGroups'])