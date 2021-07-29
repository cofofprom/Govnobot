from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.exceptions import *
from collections import Counter
from random import randint
from os import environ

TOPCOUNT = 10
try:
    with open("topcount.dat", "rb") as f:
        TOPCOUNT = f.read(1)
except:
    pass
TOKEN = environ["TOKEN"]
VKTOKEN = environ.get('VKTOKEN')
print(f"token = {TOKEN}")
print(f"topcount = {TOPCOUNT}")
print(f"login = {environ.get('LOGIN', 'NO VALUE')}")
print(f"password = {environ.get('PASSWORD', 'NO VALUE')}")
print(f"VKTOKEN = {environ.get('VKTOKEN', 'NO VALUE')}")

def parseRawArtists(astr):
    clearnames = []
    dnames = list(map(lambda x: x.strip(), astr.upper().split(',')))
    for n in dnames:
        clearnames.extend(list(map(lambda x: x.strip(), n.split("FEAT."))))
    return clearnames

def captcha(c):
    print('CAPTCHA:', c.get_url())
    return c.try_again(input("Ans: "))

def parseAudioInfo(audio_item):
    result = {}
    artists = []
    if 'main_artists' in audio_item.keys():
        artists.extend([artist['name'].upper() for artist in audio_item['main_artists']])
    if 'featured_artists' in audio_item.keys():
        artists.extend([artist['name'].upper() for artist in audio_item['featured_artists']])
    if len(artists) == 0:
        artists = parseRawArtists(audio_item['artist'])
    if 'genre_id' in audio_item.keys():
        result['genre'] = audio_item['genre_id']
    result['artists'] = artists
    result['raw'] = audio_item
    return result

def getAllAudioList(api, id):
    result = {}
    audio = api.method("audio.get", {"owner_id": id})
    result['count'] = audio['count']
    result['items'] = audio['items']
    offset = 200
    got = len(result['items'])
    while got < result['count']:
        audio = api.method("audio.get", {"owner_id": id, "offset": offset})
        result['items'].extend(audio['items'])
        got += len(audio['items'])
        offset = got
    return result

def processUser(api, user):
    printPerson("analysing audios of %s" % user['first_name'])
    try:
        audios = getAllAudioList(api, user['id'])
    except ApiError as e:
        if e.code == 201:
            printPerson("Чета не могу открыть аудио...")
        else:
            printPerson("Хз че за ошибка с кодом {}...".format(e.code))
        return

    count = audios['count']
    curr = 0
    artists = []

    for au in audios['items']:
        audio = parseAudioInfo(au)
        artists.extend(audio['artists'])
        curr += 1
    print("All {}, analysed {}".format(count, curr))
    c = Counter(artists)
    printPerson("Top %d artists of %s:" % (TOPCOUNT, user['first_name']))
    printstring = ""
    for i, item in enumerate(c.most_common(TOPCOUNT)):
        printstring += " ".join(map(str, (i+1, item[0], '->', item[1], 'audios'))) + '\n'
    printPerson(printstring)
    print("DONE")

gapi = VkApi(token=TOKEN, app_id=6626402)
api = VkApi(token=VKTOKEN, app_id=6121396, captcha_handler=captcha)
#api.auth()
print("LOGGED IN")
longpoll = VkBotLongPoll(gapi, '149861818')

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        rawtext = event.object['message']['text']
        def printPerson(*text):
            gapi.method("messages.send", {"peer_id": event.object['message']['peer_id'], "message": " ".join(map(str, text)), "random_id": randint(0, 1000)})
        if rawtext == "killbot":
            print("Shutting down...")
            exit(0)
        if 'setup' in rawtext.lower():
            try:
                TOPCOUNT = int(rawtext.split(' ')[1])
                with open('topcount.dat', 'wb') as f:
                    f.write(TOPCOUNT)
            except:
                printPerson("Число может быть только положительным")
                TOPCOUNT = 10
                with open('topcount.dat', 'wb') as f:
                    f.write(TOPCOUNT)
                continue
            if TOPCOUNT <= 0:
                printPerson("Число может быть только положительным")
                TOPCOUNT = 10
                with open('topcount.dat', 'wb') as f:
                    f.write(TOPCOUNT)
            continue
        if not "vk.com" in rawtext:
            printPerson("Скинь мне ссылку на страницу чела!!!")
            continue
        uid = rawtext.split("/")[-1]
        print("Requesting...", uid)
        uidlist = list(map(lambda x: x.strip(), uid.split(',')))
        try:
            users = api.method("users.get", {"user_ids": ','.join(uidlist)})
        except ApiError as e:
            if e.code == 113:
                printPerson("Неправильная ссылка бля...")
            else:
                printPerson("Хз че за ошибка с кодом {}...".format(e.code))
            continue
        for user in users:
            processUser(api, user)
