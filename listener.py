from __future__ import print_function
import socket
import time
import docker
import json
import logging
from google.cloud import dns
import google.cloud
import urllib
import urllib.request

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    # Python 2.x fallback
    from argparse import Namespace

FIVE_MINUTES = 5 * 60

client = dns.Client.from_service_account_json('/home/tom/coding/docker_gcloud_dns/client_secrets.json')


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
        print('Changes completed')


client = docker.from_env()


with urllib.request.urlopen("http://wtfismyip.com/json") as url:
    ip = url.read()
encoding = url.info().get_content_charset('utf-8')
JSON_object = json.loads(ip.decode(encoding))
print (JSON_object['YourFuckingIPAddress'])


try:
    mfip = JSON_object['YourFuckingIPAddress']
    print (mfip)
except Exception as e:
    print (e)


for events in client.events():
    try:
        x = json.loads(events.decode(encoding))
        if x['Type'] == 'container' and (x['status'] == 'start' or x['status'] == 'create' or x['status'] == 'destroy'):
            print ('Setting ' + x['Actor']['Attributes']['name'] + '.' + domain + ' to: ' + mfip)
            updateDNS(x['Actor']['Attributes']['name'],mfip)
    except Exception as e:
        print (e)
