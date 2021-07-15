from time import sleep
from vk_api import VkApi
from vk_api.audio import VkAudio
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.exceptions import *
from collections import Counter
from random import randint

TOKEN = "6507145f0504cc1452f0fa3fe5abc50399f176fe62784c731fe6e3f951e9f6911d39d20aa7386fefa71a9"
VKTOKEN = "44661ee5ea59fefb7283b476c8c76ad4963ab29d1dff2419e70ae5ca0d34c4b8060e9bd76d86d1fe28b90"
TOPCOUNT = 10

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
api = VkApi(login="89091416029", password="tralauron1337", app_id=6121396, captcha_handler=captcha)
api.auth()
longpoll = VkBotLongPoll(gapi, '149861818')

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        rawuid = event.object['message']['text']
        def printPerson(*text):
            gapi.method("messages.send", {"peer_id": event.object['message']['peer_id'], "message": " ".join(map(str, text)), "random_id": randint(0, 1000)})
        if rawuid == "killbot":
            exit(0)
        if 'setup' in rawuid:
            try:
                TOPCOUNT = int(rawuid.split(' ')[1])
            except:
                printPerson("Число может быть только положительным")
                TOPCOUNT = 10
                continue
            if TOPCOUNT <= 0:
                printPerson("Число может быть только положительным")
                TOPCOUNT = 10
            continue
        if not "vk.com" in rawuid:
            printPerson("Скинь мне ссылку на страницу чела!!!")
            continue
        uid = rawuid.split("/")[-1]
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
