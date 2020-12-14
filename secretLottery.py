import json
import subprocess
import time
import random
import pexpect
import os
from cosmospy import BIP32DerivationError, seed_to_privkey, Transaction
import requests

env={}
with open("private.json") as json_file:
    env = json.load(json_file)

seed = env["seed"]
privkey = ""

try:
    privkey = seed_to_privkey(seed, path="m/44'/529'/0'/0/0")
except BIP32DerivationError:
    print("No valid private key")

time.sleep(86400)
while True :
    getListOfDelegators = subprocess.run(["secretcli", "q", "staking", "delegations-to", "secretvaloper19qq99fyzrx3wsrxj894uhahy3s3tlaqs68a34s"], shell=False, capture_output=True)
    decodedLisOfDelegators = getListOfDelegators.stdout.decode()
    lisOfDelegators = json.loads(decodedLisOfDelegators)
    delegators = []
    totalAmountInStaking = 0
    for delegator in lisOfDelegators:
        totalAmountInStaking = totalAmountInStaking + int(delegator['balance']['amount']) 
        if int(delegator['balance']['amount']) >= 1000000000:
            data = {
                'address': delegator['delegator_address'],
                'share': int(delegator['balance']['amount'])
            }
            delegators.append(data)


    sort = 0 if len(delegators) == 1 else random.randint(0,len(delegators))
    print(f'winner is the index: {sort}')  
    getComissionFromValidator = subprocess.Popen("./commission.sh", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=0)
    getComissionFromValidator.stdin.write(f'{env['walletPass']}\n')
    getComissionFromValidator.stdin.close()
    data = ""
    for line in getComissionFromValidator.stdout:
        print(line.strip())
        data = data + line.strip()
    
    jsonData = json.loads(data)
    #We have to get the commission
    lastComission = {}
    with open('commission.txt') as json_file:
        lastComission = json.load(json_file)

    print(f'total amount in staking: {totalAmountInStaking}')
    amountDeserve = delegators[sort]['share'] * 100 / totalAmountInStaking
    print(f"last commission: {lastComission}")
    print(f"commission from validator: {jsonData[0]['amount']}")
    amountAvailableToSend = int((float(jsonData[0]["amount"]) - float(lastComission["amount"])) / 2 + float(lastComission['pot']))
    print(f'amount available to send: {amountAvailableToSend}')
    amountToSend = int(float(amountAvailableToSend * amountDeserve / 100))
    print(f'amount to send: {amountToSend}')
    commonPot = amountAvailableToSend - amountToSend

    print(f'winner address: {delegators[sort]}')
    
    #Get the sequence
    urlSequence = "https://api.secretapi.io/auth/accounts/secret1efhca6jr0xhwyms66p44gkhss0gd87khhczajy"
    getSequence = requests.get(urlSequence)
    parseSequence = getSequence.json()
    sequenceDefault = parseSequence["result"]["value"]["sequence"]
    accountNumber = parseSequence["result"]["value"]["account_number"]

    #Write in the file the commission calculation
    commissionAmount = {'amount' : int(float(jsonData[0]['amount'])), 'pot': int(commonPot)}
    with open('commission.txt', 'w') as outfile:
        json.dump(commissionAmount, outfile)

    if amountToSend > 0 :
        
        tx = Transaction(
            privkey=privkey,
            account_num=accountNumber,
            sequence=sequenceDefault,
            fee=50000,
            gas=200000,
            memo="lottery-chimere.io",
            chain_id="secret-2",
            sync_mode="sync",
        )
        tx.add_transfer(recipient=delegators[sort]['address'], amount=amountToSend)
        tx_broadcast = tx.get_pushable()
        print(tx_broadcast)

        url = "https://api.secretapi.io/txs"
        x = requests.post(url, data = tx_broadcast)
        print(x.text)

        url_chimere = f"https://chimere.io/api/lottery-pot-update/{env['apikeychimere']}"
        y = requests.post(url_chimere, json={'pot':int(commonPot)} )
        print(y.text)

    time.sleep(86400)


#3890630