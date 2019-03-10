from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

bot = ChatBot('chatterbot.corpus.english')
trainer = ListTrainer(bot)

trainer.train([
    'How are you?',
    'I am good.',
    'That is good to hear.',
    'Thank you',
    'You are welcome.',
])

while True:
    try:
        bot_input = bot.get_response(input())
        print(bot_input)

    except(KeyboardInterrupt, EOFError, SystemExit):
        break

		


import sys
import yaml
import rethinkdb as r
from rethinkdb.errors import RqlDriverError, RqlRuntimeError
import socket
import time



if len(sys.argv) < 2:
    print("Hello,whatspp ???")
    print("%s <config file>") % sys.argv[0]
    sys.exit(1)


configfile = sys.argv[1]
cfh = open(configfile, "r")
config = yaml.safe_load(cfh)
cfh.close()

def callSaltRestart(config):
    ''' Call Saltstack to restart a service '''
    import requests
    url = config['salt_url'] + "/services/restart"
    headers = {
        "Accept:" : "application/json"
    }
    postdata = {
        "tgt" : "db*",
        "matcher" : "glob",
        "args" : "rethinkdb",
        "secretkey" : config['salt_key']
    }
    try:
        req = requests.post(url=url, headers=headers, data=postdata, verify=False)
        print("Called for help and got response code: %d") % req.status_code
        if req.status_code == 200:
            return True
        else:
            return False
    except (requests.exceptions.RequestException) as e:
        print("Error calling for help: %s") % e.message
        return False

def callSaltHighstate(config):
    ''' Call Saltstack to initiate a highstate '''
    import requests
    url = config['salt_url'] + "/states/highstate"
    headers = {
        "Accept:" : "application/json"
    }
    postdata = {
        "tgt" : "db*",
        "matcher" : "glob",
        "secretkey" : config['salt_key']
    }
    try:
        req = requests.post(url=url, headers=headers, data=postdata, verify=False)
        print("Called for help and got response code: %d") % req.status_code
        if req.status_code == 200:
            return True
        else:
            return False
    except (requests.exceptions.RequestException) as e:
        print("Error calling for help: %s") % e.message
        return False


connection_attempts = 0
first_connect = 0.00
last_restart = 0.00
last_highstate = 0.00
connected = False
called = None


while connected == False:
    if first_connect == 0.00:
        first_connect = time.time()
    # RethinkDB Server
    try:
        rdb_server = r.connect(
            host=config['rethink_host'], port=config['rethink_port'],
            auth_key=config['rethink_authkey'], db=config['rethink_db'])
        connected = True
        print("Connected to RethinkDB")
    except (RqlDriverError, socket.error) as e:
        print("Cannot connect to rethinkdb")
        print("RethinkDB Error: %s") % e.message
        timediff = time.time() - first_connect
        if timediff > 300.00:
            last_timediff = time.time() - last_restart
            if last_timediff > 600.00 or last_restart == 0.00:
                if timediff > 600:
                    callSaltRestart(config)
                last_restart = time.time()
            last_timediff = time.time() - last_highstate
            if last_timediff > 300.00 or last_highstate == 0.00:
                callSaltHighstate(config)
                last_highstate = time.time()
    connection_attempts = connection_attempts + 1
    print("RethinkDB connection attempts: %d") % connection_attempts
    time.sleep(60)



try:
    result = r.table('users').count().run(rdb_server)
except (RqlDriverError, RqlRuntimeError) as e:
    print("Got error while performing query: %s") % e.message
    print("Exiting...")
    sys.exit(1)




