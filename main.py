import csv
import json
import psutil
import time
import signal
import sys
import requests
import urllib.parse
from pathlib import Path
from USER_API_KEY import USER_API_KEY

CHANNEL_ID = 0
WRITE_API_KEY = ''


def createChannel():
    # Request channel list from ThinkSpeak
    method = 'GET'
    uri = 'https://api.thingspeak.com/channels.json'
    headers = {'Host': 'api.thingspeak.com',
               'Content-Type': 'application/x-www-form-urlencoded'}

    content = {'api_key': USER_API_KEY}
    content_encoded = urllib.parse.urlencode(content)
    headers['Content-Length'] = str(len(content_encoded))

    response = requests.request(method, uri, data=content_encoded,
                                headers=headers, allow_redirects=False)

    # Test if a channel already exist or not
    isChannel = False

    channelInfo = Path('channelInfo.txt')
    if channelInfo.is_file():

        with open(channelInfo, 'r', encoding='utf8') as file:
            channel_id = int(file.readline())

        channels = json.loads(response.content)

        for i in range(channels.__len__()):
            if channels[i]['id'] == int(channel_id):
                isChannel = True

    if isChannel:
        print('YOU ALREDY HAVE A CHANNEL CREATED, SO THAT ONE IS GONNA BE USED NOW')
        print('-------------------------------------------------------------------')

    else:
        # If not a channel alredy created, a new channel would be created
        print('YOU DONT HAVE A CHANNEL CREATED, SO A NEW ONE IS BEING CREATED FOR YOU')
        print('----------------------------------------------------------------------')
        method = 'POST'
        uri = 'https://api.thingspeak.com/channels.json'
        headers = {'Host': 'api.thingspeak.com',
                   'Content-Type': 'application/x-www-form-urlencoded'}

        content = {'api_key': USER_API_KEY,
                   'name': 'Nire Kanala',
                   'field1': "%CPU",
                   'field2': "%RAM"}

        content_encoded = urllib.parse.urlencode(content)
        headers['Content-Length'] = str(len(content_encoded))

        response = requests.request(method, uri, data=content_encoded,
                                    headers=headers, allow_redirects=False)

        code = response.status_code
        content = response.content

        if code == 402:
            print('YOU HAVE REACHED THE MAXIMUM CHANNEL QUANTITY, PLEASE REMOVE ONE BEFORE CREATING A NEW ONE')
            print('------------------------------------------------------------------------------------------')

        else:
            json_parsed = json.loads(content)
            channel_id = json_parsed['id']
            key = ''

            # Get WRITE_API_KEY
            for api in json_parsed['api_keys']:
                if api['write_flag']:
                    key = api['api_key']

            # Save on apiKey.txt file the channel id and the write key
            with open('channelInfo.txt', 'w') as file:
                file.write(str(channel_id) + '\n')
                file.write(key)


def cpuRam():
    time.sleep(2)
    time.sleep(2)
    while True:
        # Get CPU and RAM stats by using psutil library
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent

        # Post the stats on ThinkSpeak
        method = "POST"
        uri = 'https://api.thingspeak.com/update.json'
        headers = {'Host': 'api.thingspeak.com',
                   'Content-Type': 'application/x-www-form-urlencoded'}

        content = {'api_key': WRITE_API_KEY,
                   'name': 'Nire kanala',
                   'field1': cpu,
                   'field2': ram}

        content_encoded = urllib.parse.urlencode(content)
        headers['Content-Length'] = str(len(content_encoded))

        response = requests.request(method, uri, data=content_encoded,
                                    headers=headers, allow_redirects=False)

        print('NEW DATA HAS BEEN SENT TO THINKSPEAK CHANNEL (NEXT DATA SENDING IN 15s)')

        # Repeat the process every 15s
        time.sleep(15)


def cleanChannel():
    # Delete channel from ThinkSpeak
    method = "DELETE"
    uri = 'https://api.thingspeak.com/channels/' + str(CHANNEL_ID) + '/feeds.json'
    headers = {'Host': 'api.thingspeak.com',
               'Content-Type': 'application/x-www-form-urlencoded'}

    content = {'api_key': USER_API_KEY}
    content_encoded = urllib.parse.urlencode(content)
    headers['Content-Length'] = str(len(content_encoded))

    response = requests.request(method, uri, data=content_encoded,
                                headers=headers, allow_redirects=False)

    print('YOUR CHANNEL HAS BEEN CLEANED UP')
    print('--------------------------------')


def dataDownload():
    # Get data from ThinkSpeak channel
    method = 'GET'
    uri = 'https://api.thingspeak.com/channels/' + str(CHANNEL_ID) + '/feeds.json'
    headers = {'Host': 'api.thingspeak.com',
               'Content-Type': 'application/x-www-form-urlencoded'}

    content = {'api_key': WRITE_API_KEY, 'results': 100}
    content_encoded = urllib.parse.urlencode(content)
    response = requests.request(method, uri, data=content_encoded,
                                headers=headers, allow_redirects=False)

    print('---------------------------------------------------------------')
    print('DATA IS GOING TO BE DOWNLOADED, IT WOULD APPEAR AT data.csv')
    print('---------------------------------------------------------------')
    return response.content


def CSVFileCreate(data):

    with open('data.csv', 'w', newline='', encoding='utf8') as csvfile:
        csvfile = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        feedsParam = []
        if data['feeds'].__len__() == 0:
            print('NO DATA TO DOWNLOAD')
        else:
            print('DATA DOWNLOADED CORRECTLY')
            for param in data['feeds'][0]:
                if not param.__eq__('entry_id'):
                    feedsParam.append(param)
            csvfile.writerow(feedsParam)

            for param in data['feeds']:
                timestamp = param[feedsParam[0]]
                cpu = param[feedsParam[1]]
                ram = param[feedsParam[2]]
                csvfile.writerow([str(timestamp), str(cpu), str(ram)])


def handler(sig_num, frame):
    print('\nSIGNAL HANDLER CALLED WITH SIGNAL ' + str(sig_num))
    print('\nEXITING GRACEFULLY')
    data = json.loads(dataDownload())
    CSVFileCreate(data)
    cleanChannel()
    sys.exit(0)


if __name__ == "__main__":
    #  When SIGINT is received handler gets executed
    signal.signal(signal.SIGINT, handler)
    print('---------------------------------------------------------------')
    print('THE PROGRAM IS BEING EXECUTED, PRESS CTRL + C TO STOP EXECUTION')
    print('---------------------------------------------------------------')
    createChannel()
    channelInfo = Path('channelInfo.txt')
    if channelInfo.is_file():
        with open(channelInfo, 'r', encoding='utf8') as file:
            CHANNEL_ID = int(file.readline())
            WRITE_API_KEY = file.readline()
    cpuRam()
