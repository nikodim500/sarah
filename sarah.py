import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from bottle import default_app, route, request, run, view, static_file
import telegram
import json
import datetime as dt

APPNAME = 'sarah'
PAPAID = os.environ['PAPAID']
sarahTOKEN = os.environ['SARAH_TOKEN']
app_location = os.environ.get('APP_LOCATION')

this_path = os.path.dirname(os.path.abspath(__file__))
sarah_log_file = os.path.join(this_path, 'logs', 'sarah.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler(sarah_log_file, maxBytes=4194304, backupCount=3)
handler.setFormatter(formatter)
sarah_logger = logging.getLogger('Sarah')
sarah_logger.setLevel(logging.DEBUG)
sarah_logger.addHandler(handler)

sarah_stat_file_name = os.path.join(this_path, 'stat', 'sarah.stat')

sarah_logger.info('Start logging into {}'.format(sarah_log_file))
sarah_logger.info('Env vars: PAPAID={}, SARAH_TOKEN={}, APP_LOCATION={}'.format(PAPAID, sarahTOKEN, app_location))

@route('/')
@route('/home')
@view('home')
def home():
    """Renders the home page."""
    return dict(
        year=dt.date.today().year
    )

@route('/log')
def log():
    return static_file(sarah_log_file)


@route('/setSarahWebhook')
def setSarahWebhook():
    bot = telegram.Bot(sarahTOKEN)
    botWebhookResult = bot.setWebhook(webhook_url='https://{}.pythonanywhere.com/botSarahHook'.format(APPNAME))
    return str(botWebhookResult)

@route('/botSarahHook', method='POST')
def botSarahHook():
    sarah_logger.info('SARAH hook')
    bot = telegram.Bot(sarahTOKEN)
    update = telegram.update.Update.de_json(request.json, bot)
    if update.message is not None:
        sarah_logger.info('MSG2SARAH. %s', update.message.text)
    return 'OK'

def to_stat(stat):
    try:
        f = open(sarah_stat_file_name, 'a')
        f.write(stat + '\n')
        f.close
    except Exception:
        sarah_logger.info("Save to stat file error: %s", sys.exc_info()[0]);

@route('/m2p', method = ['POST', 'GET'])   # {"typ": "INFO","src": "Gates","msg": "Openning..."}
def m2p():
    postdata = request.body.read()
    postdata = postdata.decode('utf-8')
    postdata = json.loads(postdata)
    sarah_logger.info('M2P. %s', postdata);
    if postdata['typ'] == 'STAT':
        to_stat(postdata['src'] + ' ' + postdata['msg'])
    else:
        bot = telegram.Bot(sarahTOKEN)
        bot.sendMessage(chat_id = PAPAID, text = '[' + postdata['typ'] + '] ' + postdata['src'] + ': ' + postdata['msg'])

application = default_app()

if app_location == 'OCI':
    sarah_logger.info('Running on OCI')
    print('Running on oracle cloud')
    run(host="0.0.0.0")
else:
    run(host='localhost', port=8080, debug=True)
    sarah_logger.info('Running locally')
    print('Running locally')
