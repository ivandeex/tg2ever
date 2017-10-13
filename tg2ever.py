#!/usr/bin/env python3
import os
import sys
import json
import re
from pymorphy2 import MorphAnalyzer
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto


def get_ini(core_dir=None, sess_name='tg2ever'):
    if not core_dir:
        core_dir = os.path.normpath(os.path.dirname(sys.argv[0]))

    # You must get your own api_id and api_hash from
    # https://my.telegram.org, under API Development.

    with open(os.path.join(core_dir, sess_name + '.ini')) as f:
        ini = json.load(f)

    for key in 'api_id api_key phone channel'.split():
        assert key in ini

    ini['core_dir'] = core_dir
    ini['sess_name'] = sess_name
    ini['sess_file'] = os.path.join(core_dir, sess_name)
    ini['cache_file'] = os.path.join(core_dir, sess_name + '.json')
    ini['photo_dir'] = os.path.join(ini['core_dir'], 'photos')
    try:
        os.makedirs(ini['photo_dir'])
    except IOError:
        pass

    return ini


def connect_cli(ini):
    cli = TelegramClient(ini['sess_file'], ini['api_id'], ini['api_key'])
    cli.connect()
    if not cli.is_user_authorized():
        cli.send_code_request(ini['phone'])
        code = int(input("Enter the code: "))
        myself = cli.sign_in(ini['phone'], code)
        str(myself)  # verify it's ok
    return cli


def pull_channel(cli, ini):
    photo_dir = ini['photo_dir']
    for fname in os.listdir(photo_dir):
        try:
            os.unlink(os.path.join(photo_dir, fname))
        except IOError:
            pass

    channel = ini['channel']
    print('dumping channel: %s' % channel)
    result = []
    offset = 0
    iter = 0

    while True:
        iter += 1
        count, messages, _ = cli.get_message_history(channel, offset_id=offset)
        if not messages:
            break

        for msg in messages:
            if hasattr(msg, 'message'):
                obj = {
                    'id': msg.id,
                    'text': msg.message.strip(),
                    'date': msg.date.isoformat()
                }
                if isinstance(msg.media, MessageMediaPhoto):
                    path = cli.download_media(msg, photo_dir)
                    obj['photo'] = os.path.basename(path)
                result.append(obj)

        offset = min([msg.id for msg in messages])

    return result


def get_messages(ini):
    cache_file = ini['cache_file']
    try:
        with open(cache_file, 'r', encoding='utf8') as f:
            data = json.load(f)
    except Exception:
        cli = connect_cli(ini)
        data = pull_channel(cli, ini)
        cli.disconnect()
        with open(cache_file, 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False)
    data = sorted(data, key=lambda o: o['id'])
    return data


def fix_text(morph, o):
    # for form in morph.parse(word):
    # form.word, form.score
    text = o['text']
    score = o['text'].count('\u00ad')
    score = int(score / (len(text)+1) * 100)
    o['score'] = score
    if score >= 5:
        text = text.replace('\u00ad', ' ')
    if re.search('[\u0400-\u0500]', text):
        text = '! ' + text
    o['text'] = text


def main():
    ini = get_ini()
    data = get_messages(ini)
    morph = MorphAnalyzer()
    for o in data:
        fix_text(morph, o)
    data = sorted(data, key=lambda o: o['score']*1000+o['id'])
    for o in data:
        print('{:3d}: [{:2d}]  {}...'.format(
            o['id'], o['score'],
            o['text'][:80].replace('\n', '\\n'))
        )

    print('done')


if __name__ == "__main__":
    main()
