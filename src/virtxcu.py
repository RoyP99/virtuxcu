'''
Created on Feb 23, 2023

@author: robert
'''

import sys
import time
import json
import platform
import subprocess
import requests

class virtXcu():
    def __init__(self):
        self.cameras = []
    
    def ping(self, host):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        WARNING: ping is not a reliable method on Windows
        """
    
        # Option for the number of packets as a function of
        if platform.system().lower()=='windows':
            command = ['ping', '-n', '1', '-w', '100', host]
        else:
            command = ['fping', '-c', '1', '-t', '100', host]
        
        return subprocess.call(command) == 0

    def testIp(self, host):
        """
        Returns True if host (str) responds to a http request
        Will wait for 0.5 seconds
        """
        url = 'http://' + host + ':8008/api/v1/'
        #response = requests.get(url + 'cameranumber')
        #print(response.json())
        try:
            response = requests.get(url + 'cameranumber', timeout=0.5)
            return response.status_code == 200
        except:
            pass
        return 0
        
    def setupCamera(self, camera):
        print(f"Setup {camera['ip']}")
        # first set camera number
        url = 'http://' + camera['ip'] + ':8008/api/v1/'
        #response = requests.get(url + 'cameranumber')
        #print(response.json())
        response = requests.put(url + 'cameranumber', json={"camnr": camera['camnr']})
        #print(response.status_code)
        
        # next get info of senders
        url = 'http://' + camera['ip'] + ':8601/x-nmos/node/v1.3/senders'
        response = requests.get(url)
        jsResp = response.json()
        senderIds = {}
        for senderInfo in jsResp:
            senderIds[senderInfo['label']] = senderInfo['id']
        # and get info of receivers
        url = 'http://' + camera['ip'] + ':8601/x-nmos/node/v1.3/receivers'
        response = requests.get(url)
        jsResp = response.json()
        receiverIds = {}
        for receiverInfo in jsResp:
            receiverIds[receiverInfo['label']] = receiverInfo['id']
        #print(senderIds)
        #print(receiverIds)
        
        # set the senders
        for sender in camera['senders']:
            if sender['label'] in senderIds:
                uuid = senderIds[sender['label']]
                url = 'http://' + camera['ip'] + ':8601/x-nmos/connection/v1.1/single/senders/' + uuid + '/staged'
                patchInfo = sender['request']
                patchInfo['activation'] = {'mode': 'activate_immediate'}
                response = requests.patch(url, json=patchInfo)
                if response.status_code == 200:
                    print(f"Sender {sender['label']} updated")
                else:
                    print(f"Sender {sender['label']} code {response.status_code} url {url} patch {patchInfo}")
                
        # set the receivers
        for receiver in camera['receivers']:
            if receiver['label'] in receiverIds:
                uuid = receiverIds[receiver['label']]
                url = 'http://' + camera['ip'] + ':8601/x-nmos/connection/v1.1/single/receivers/' + uuid + '/staged'
                patchInfo = receiver['request']
                patchInfo['activation'] = {'mode': 'activate_immediate'}
                response = requests.patch(url, json=patchInfo)
                if response.status_code == 200:
                    print(f"Receiver {receiver['label']} updated")
                else:
                    print(f"Receiver {receiver['label']} code {response.status_code} url {url} patch {patchInfo}")
            
    def loop(self):
        while True:
            for camera in self.cameras:
                # status = self.ping(camera['ip'])
                status = self.testIp(camera['ip'])
                if status:
                    print(f"Found {camera['ip']}")
                    if camera['found'] == False:
                        camera['found'] = True
                        self.setupCamera(camera)                    
                else:
                    print(f"Not found {camera['ip']}")
                    camera['found'] = False                    
            time.sleep(5)
        
    def getInit(self):
        # Opening JSON file
        try:
            f = open('data/data.json')
          
            # returns JSON object as a dictionary
            data = json.load(f)
              
            # Closing file
            f.close()
        except:
            print("Can't open input file data/data.json or is corrupt. Exiting")
            sys.exit(1)
        
        self.cameras = data['cameras']
          
        # Iterating through the json list        
        for i in self.cameras:
            i['found'] = False
            print(i)
        
    def doVirtXcu(self):
        self.getInit()
        self.loop()
    
if __name__ == '__main__':
    myVirtXcu = virtXcu()
    myVirtXcu.doVirtXcu()