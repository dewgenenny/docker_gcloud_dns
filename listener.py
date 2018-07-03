from __future__ import print_function
import socket
import time
import docker
import json
from google.cloud import dns
import urllib

FIVE_MINUTES = 5 * 60

client = dns.Client(project='tgcom-148316')


zone = client.zone('penberthio')

domain = 'penberth.io'

def hostname_resolves(hostname):
    try:
        socket.gethostbyname(hostname)
        return 1
    except socket.error:
        return 0

def updateDNS(record, ip):

    full_record = record + '.penberth.io.'
    
    if hostname_resolves(full_record) == 1:
        record_set = zone.resource_record_set(full_record, 'A', FIVE_MINUTES, [ip,])
        old_record_set = zone.resource_record_set(full_record, 'A', FIVE_MINUTES, [socket.gethostbyname(full_record),]) 
        changes = zone.changes()
        changes.delete_record_set(old_record_set)  # API request
        changes.add_record_set(record_set)
    else:
        record_set = zone.resource_record_set(full_record, 'A', FIVE_MINUTES, [ip,])
        changes = zone.changes()
        changes.add_record_set(record_set)

    changes.create()  # API request
    while changes.status != 'done':
        print('Waiting for changes to complete')
        time.sleep(60)     # or whatever interval is appropriate
        changes.reload()   # API request


try:
    from types import SimpleNamespace as Namespace
except ImportError:
    # Python 2.x fallback
    from argparse import Namespace

client = docker.from_env()

#print (client.containers.list)
#print ("List of running containers: ", end='\n\n')

ip = urllib.urlopen('http://wtfismyip.com/json').read()
#print (ip)

try:
    response = json.loads(ip, object_hook=lambda d: Namespace(**d))
#    print (response.YourFuckingIPAddress)
except:
    print ("Couldn't figure out your IP")


for events in client.events():
#    print (events)

    try:
        x = json.loads(events, object_hook=lambda d: Namespace(**d))
        if x.Type == 'container' and (x.status == 'start' or x.status == 'create' or x.status == 'destroy'):
            #print (x.Actor.Attributes.name, end=' status is: ')
            #print (x.status)
            print ('Setting ' + x.Actor.Attributes.name + '.' + domain + ' to: ' + response.YourFuckingIPAddress)
            updateDNS(x.Actor.Attributes.name,response.YourFuckingIPAddress)
    except Exception as e:
        print (e)
