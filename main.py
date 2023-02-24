import csv
import json
import psutil
import time
import signal
import sys
import requests
import urllib.parse
from pathlib import Path


USER_API_KEY = "DPERKBVPXLT9ADDL"
CHANNEL_ID = 0
WRITE_API_KEY = ""



def kanalaSortu(): # ONDO

    # KANALEN ZERRENDA LORTZEKO ESKARIA EGIN
    metodoa = 'GET'
    uria = "https://api.thingspeak.com/channels.json"
    goiburuak = {'Host': 'api.thingspeak.com', 'Content-Type': 'application/x-www-form-urlencoded'}
    edukia = {'api_key': USER_API_KEY}
    edukia_encoded = urllib.parse.urlencode(edukia)
    goiburuak['Content-Length'] = str(len(edukia_encoded))

    erantzuna = requests.request(metodoa, uria, headers=goiburuak,
                                 data=edukia_encoded, allow_redirects=False)

    # KANALEN BAT EXISTITZEN DEN EDO EZ KONPROBATU
    apiKey_file = Path('apiKey.txt')
    kanalaDago = False
    if apiKey_file.is_file():

        with open(apiKey_file, 'r', encoding='utf8') as file:
            channel_id = int(file.readline())

        kanalak = json.loads(erantzuna.content)

        for i in range(kanalak.__len__()):
            if kanalak[i]['id'] == int(channel_id):
                kanalaDago = True

    if (kanalaDago):
        print("KANALEN BAT SORTUTA DAGO, BERAZ, HORI ERABILIKO DA. EZ DA BERRIRIK SORTUKO")

    else:
        # KANAL BERRIA SORTU
        metodoa = 'POST'
        uria = "https://api.thingspeak.com/channels.json"
        goiburuak = {'Host': 'api.thingspeak.com', 'Content-Type': 'application/x-www-form-urlencoded'}
        edukia = {'api_key': USER_API_KEY, 'name': 'Nire Kanala', 'field1': "%CPU", 'field2': "%RAM"}
        edukia_encoded = urllib.parse.urlencode(edukia)
        goiburuak['Content-Length'] = str(len(edukia_encoded))

        # ESKARIA EGIKARITU
        erantzuna = requests.request(metodoa, uria, headers=goiburuak,
                                     data=edukia_encoded, allow_redirects=False)

        # ESKAERAREN KODEA JASO
        kodea = erantzuna.status_code

        # KANALAREN ID LORTU
        edukia = erantzuna.content
        if kodea == 402:
            print('KANAL KOP MAX')

        else:
            json_parsed = json.loads(edukia)
            kanal_id = json_parsed['id']
            key=""

            # IDAZKETA PASAHITZA LORTU
            for api in json_parsed['api_keys']:
                if api['write_flag']:
                    key = api['api_key']

            # TESTU FITXATEGIAN ID ETA WRITE-KEY GORDE
            with open('apiKey.txt', 'w') as fitx:
                fitx.write(str(kanal_id) + '\n')
                fitx.write(key)

def cpu_ram(): # ONDO
    time.sleep(2)
    time.sleep(2)
    while True:
        # BALIOAK LORTU PSUTIL LIBURUTEGIA ERABILIZ
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent

        # ESKAERAREN PARAMETROAK DEFINITU
        metodoa = "POST"
        uria = "https://api.thingspeak.com/update.json"
        goiburuak = {'Host': 'api.thingspeak.com', 'Content-Type': 'application/x-www-form-urlencoded'}
        edukia = {'api_key': WRITE_API_KEY,
                  'name': 'Nire kanala',
                  'field1': cpu,
                  'field2': ram}
        edukia_encoded = urllib.parse.urlencode(edukia)
        goiburuak['Content-Length'] = str(len(edukia_encoded))

        # ESKAERA EGIKARITU
        erantzuna = requests.request(metodoa, uria, data=edukia_encoded,
                                  headers=goiburuak, allow_redirects=False)

        # ERANTZUNAREN KODEA JASO
        kodea = erantzuna.status_code
        deskribapena = erantzuna.reason
        print(str(kodea) + " " + deskribapena)

        # 15s-RO EXEKUTATU
        time.sleep(15)



def kanalaGarbitu(): # ONDO
    # ESKARIAREN PARAMETROAK DEFINITU
    metodoa = "DELETE"
    uria = "https://api.thingspeak.com/channels/" + str(CHANNEL_ID) + "/feeds.json"
    goiburuak = {'Host': 'api.thingspeak.com',
                 'Content-Type': 'application/x-www-form-urlencoded'}
    edukia = {'api_key': USER_API_KEY}
    edukia_encoded = urllib.parse.urlencode(edukia)
    goiburuak['Content-Length'] = str(len(edukia_encoded))

    # ESKARIA EGIKARITU
    erantzuna = requests.request(metodoa, uria, data=edukia_encoded,
                                headers=goiburuak, allow_redirects=False)

    # ESKARIAREN KODEA JASO
    kodea = erantzuna.status_code
    deskribapena = erantzuna.reason
    print(str(kodea) + " " + deskribapena)


def datuenDeskarga(): # ONDO
    metodoa = 'GET'
    uria = 'https://api.thingspeak.com/channels/' + str(CHANNEL_ID) + '/feeds.json'
    goiburua = {'Host': 'api.thingspeak.com', 'Content-Type': 'application/x-www-form-urlencoded'}
    edukia = {'api_key': WRITE_API_KEY, 'results': 100}
    edukia_encoded = urllib.parse.urlencode(edukia)

    erantzuna = requests.request(metodoa, uria, headers=goiburua, data=edukia_encoded, allow_redirects=False)

    print(str(erantzuna.status_code) + " " + erantzuna.reason)
    return erantzuna.content


def fitxategiaCSV(hiztegia): # ONDO
    with open('csv_fitx.csv', 'w', newline='') as csvfile:
        csvfile = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        feedsParam = []
        if hiztegia['feeds'].__len__() == 0:
            print("Ez dago daturik")
        else:
            for param in hiztegia['feeds'][0]:
                if not param.__eq__('entry_id'):
                    feedsParam.append(param)
            csvfile.writerow(feedsParam)

            for param in hiztegia['feeds']:
                timestamp = param[feedsParam[0]]
                cpu = param[feedsParam[1]]
                ram = param[feedsParam[2]]
                csvfile.writerow([str(timestamp), str(cpu), str(ram)])


def kudeatzailea(sig_num, frame): #ONDO
    print('\nSignal handler called with signal ' + str(sig_num))
    print('Check signal number on ''https://en.wikipedia.org/wiki/Signal_%28IPC%29#Default_action')
    print('\nExiting gracefully')
    hiztegia = json.loads(datuenDeskarga())
    fitxategiaCSV(hiztegia)
    kanalaGarbitu()
    sys.exit(0)


if __name__ == "__main__":
    # SIGINT JASOTZEN DENEAN, "KUDEATZAILEA" METODOA EXEKUTATUKO DA
    signal.signal(signal.SIGINT, kudeatzailea)
    print('EXEKUZIOAN DAGO PROGRAMA, SAKATU CTRL + C EXEKUZIOA GELDITZEKO')
    kanalaSortu()
    with open('apiKey.txt', 'r') as file:
        CHANNEL_ID = int(file.readline())
        WRITE_API_KEY = file.readline()
    cpu_ram()

