import json
import time
import random
from cosmospy import BIP32DerivationError, seed_to_privkey, Transaction
import requests

env = {}
with open("private.json") as json_file:
    env = json.load(json_file)

seed = env["seed"]
privkey = ""

try:
    privkey = seed_to_privkey(seed, path="m/44'/529'/0'/0/0")
except BIP32DerivationError:
    print("No valid private key")
# security lock wait 24 hours
time.sleep(86400)
while True:
    getListOfDelegators = requests.get(
        'https://api.secretapi.io/staking/validators/secretvaloper19qq99fyzrx3wsrxj894uhahy3s3tlaqs68a34s/delegations')
    lisOfDelegators = getListOfDelegators.json()
    delegators = []
    totalAmountInStaking = 0
    for delegator in lisOfDelegators['result']:
        totalAmountInStaking = totalAmountInStaking + \
            int(delegator['balance']['amount'])
        if int(delegator['balance']['amount']) >= 1000000000:
            data = {
                'address': delegator['delegator_address'],
                'share': int(delegator['balance']['amount'])
            }
            delegators.append(data)

    sort = 0 if len(delegators) == 1 else random.randint(
        0, len(delegators) - 1)
    print(f'winner is the index: {sort}')
    getComissionFromValidator = requests.get(
        'https://api.secretapi.io/distribution/validators/secretvaloper19qq99fyzrx3wsrxj894uhahy3s3tlaqs68a34s')
    parseComissionFromValidator = getComissionFromValidator.json()

    # We have to get the commission
    lastComission = {}
    with open('commission.txt') as json_file:
        lastComission = json.load(json_file)

    print(f'total amount in staking: {totalAmountInStaking}')
    amountDeserve = delegators[sort]['share'] * 100 / totalAmountInStaking
    print(f"last commission: {lastComission}")
    print(
        f"commission from validator: {parseComissionFromValidator['result']['val_commission'][0]['amount']}")
    amountAvailableToSend = int((float(parseComissionFromValidator["result"]["val_commission"][0]["amount"]) - float(
        lastComission["amount"])) / 2 + float(lastComission['pot']))
    print(f'amount available to send: {amountAvailableToSend}')
    amountToSend = int(float(amountAvailableToSend * amountDeserve / 100))
    print(f'amount to send: {amountToSend}')
    commonPot = amountAvailableToSend - amountToSend

    print(f'winner address: {delegators[sort]}')

    # Get the sequence
    urlSequence = "https://api.secretapi.io/auth/accounts/secret1efhca6jr0xhwyms66p44gkhss0gd87khhczajy"
    getSequence = requests.get(urlSequence)
    parseSequence = getSequence.json()
    sequenceDefault = parseSequence["result"]["value"]["sequence"]
    accountNumber = parseSequence["result"]["value"]["account_number"]

    # Write in the file the commission calculation
    commissionAmount = {'amount': int(float(
        parseComissionFromValidator["result"]["val_commission"][0]["amount"])), 'pot': int(commonPot)}
    with open('commission.txt', 'w') as outfile:
        json.dump(commissionAmount, outfile)

    if amountToSend > 0:

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
        tx.add_transfer(
            recipient=delegators[sort]['address'], amount=amountToSend)
        tx_broadcast = tx.get_pushable()
        print(tx_broadcast)

        url = "https://api.secretapi.io/txs"
        x = requests.post(url, data=tx_broadcast)
        print(x.text)

        url_chimere = f"https://chimere.io/api/lottery-pot-update/{env['apikeychimere']}"
        y = requests.post(url_chimere, json={
            'pot': int(commonPot),
            'past_commission': int(float(parseComissionFromValidator['result']['val_commission'][0]['amount'])),
            'jackpot': amountAvailableToSend
        })
        print(y.text)

    time.sleep(86400)


# 3890630
