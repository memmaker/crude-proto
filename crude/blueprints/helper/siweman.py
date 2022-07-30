import json
import string
import random
import datetime
from datetime import timedelta
import pytz

from siwe.siwe import SiweMessage, VerificationError


# SIWE Flow
# 1. Create SiweMessage and send it to the client (needs wallet)
# 2. Client signs the message and sends it back to the server
# 3. Server verifies the signature and authenticates the client


class SignInManager:
    def __init__(self, db):
        self.authCounter = 0
        self.db = db  # db is a mongodb collection
        self.db.create_index("wallet", unique=True)

    def getRandomString(self):
        letters = string.ascii_letters + string.digits + string.punctuation
        randomEnough = ''.join(random.choice(letters) for i in range(16))
        return randomEnough

    def createSiweMessage(self, domain, uri, wallet, custom_statement):
        utc = pytz.UTC
        expirationTime = (datetime.datetime.utcnow() + timedelta(hours=2)).replace(tzinfo=utc)
        issueTime = datetime.datetime.utcnow().replace(tzinfo=utc)
        message = {
            "domain": domain,
            "address": wallet, 
            "statement": "Please sign this message to authenticate.\n\n{}".format(custom_statement),
            "uri": uri,
            "version": "%s" % self.authCounter,
            "chain_id": 137,  # 137 = polygon mainnet, # 80001 = mumbai testnet
            "nonce": self.getRandomString(),
            "issued_at": issueTime.isoformat(),
            "expiration_time": expirationTime.isoformat()
        }
        self.authCounter += 1

        self.addSiweMessage(wallet, message)

        siweMessage = SiweMessage(message)
        return siweMessage.prepare_message()

    def addSiweMessage(self, wallet, message):
        # convert message dict to json string
        json_message = json.dumps(message)
        self.db.replace_one({'wallet': wallet}, {
            'wallet': wallet,
            'message': json_message
        }, upsert=True)

    def getSiweMessage(self, wallet):
        entry = self.db.find_one({'wallet': wallet})
        return json.loads(entry['message']) if entry else None

    def delSiweMessage(self, wallet):
        self.db.delete_one({'wallet': wallet})

    def validate_signature_message(self, message):
        return self.validate(message['address'], message['signature'])

    def validate(self, address, signature):
        siweData = self.getSiweMessage(address)
        if not siweData:
            print('No Siwe data found for {}'.format(address))
            return False

        siweMessage = SiweMessage(siweData)
        try:
            siweMessage.verify(signature)
        except VerificationError:
            # no dice..
            print('Invalid signature for {}'.format(address))
            return False

        return True