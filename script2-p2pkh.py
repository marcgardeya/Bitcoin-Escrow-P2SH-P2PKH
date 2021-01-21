#
# The program should:
#  1) accept a future time, expressed either in block height or in UNIX Epoch time, 
#     and a private key (to recreate the redeem script as above and also use to unlock the P2PKH part)
#  2) accept a P2SH address to get the funds from (the one created by the first script)
#  3) check if the P2SH address has any UTXOs to get funds from
#  4) accept a P2PKH address to send the funds to
#  5) calculate the appropriate fees with respect to the size of the transaction
#  6) send all funds that the P2SH address received to the P2PKH address provided 
#  7) display the raw unsigned transaction
#  8) sign the transaction
#  9) display the raw signed transaction
# 10) display the transaction id
# 11) verify that the transaction is valid and will be accepted by the Bitcoin nodes 
# 12) if the transaction is valid, send it to the blockchain
#
# The program should:
# - use testnet (or regtest)
# - assume a local Bitcoin testnet/regtest node is running
#
# Requirements:
# - Setup Python environment as described in setup_python.txt
# - Install bitcoinutils 0.4.7 for Satoshi denomination
# - Setup BitcoinCore for testnet with username=test and password=test or edit username and password in top section of this script
#
# How to run:
# - Run bitcoin-assignment-1.py to create P2SH address for some future time expressed in block height
# - Send multiple funding transactions to P2SH address, you can use Bitcoin Core for this
# - Bitcoin Core import P2SH address so this script can request received transactions, wait for blockchain rescan
# - Enter bitcoin node username and password in top section of this script (or use prepopulated username=test, password=test)
# - Enter private key and blockheight from first script bitcoin-assignment-1.py into top section of this script
# - Check testnet block height is equal or greater than block height from first script (otherwise locktime requirement won't be met)
# - Run this script
#

import json
import requests

from decimal import *

from bitcoinutils.utils import to_satoshis
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey, PublicKey
from bitcoinutils.script import Script

from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy


#
# Enter private key and bitcoin node username and password here
#

USERNAME      = 'test'
PASSWORD_HASH = 'ti8KMfu1Afeh8UZYYN32Lqo5NfBIN6tC-pnSW-OBp7A='
PRIVATE_KEY   = 'cSyZjejfhK5gaVYoG9pgfdMrZzw7rXufpiG4oDaYShanJhwpqGcE'
BLOCKHEIGHT   = 1747851


#
# Connect to testnet
#

setup( 'testnet' )
proxy = NodeProxy( USERNAME, PASSWORD_HASH ).get_proxy()


#
#  1) accept a future time, expressed either in block height or in UNIX Epoch time, 
#     and a private key (to recreate the redeem script as above and also use to unlock the P2PKH part)
#

from_privkey    = PrivateKey( 'cSyZjejfhK5gaVYoG9pgfdMrZzw7rXufpiG4oDaYShanJhwpqGcE' )
from_pubkey     = from_privkey.get_public_key()
from_address    = from_pubkey.get_address()
from_hash       = from_address.to_hash160()
redeem_script   = Script( [BLOCKHEIGHT, 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', from_hash, 'OP_EQUALVERIFY', 'OP_CHECKSIG'] )

#
#  2) accept a P2SH address to get the funds from (the one created by the first script)
#

from_p2sh       = P2shAddress.from_script( redeem_script )
print( "     source: " + from_p2sh.to_string() )


#
#  3) check if the P2SH address has any UTXOs to get funds from
#

# support multiple unknown funding transactions

utxos = {}
funds = Decimal(0)
txids = proxy.listreceivedbyaddress( 0, True, True, from_p2sh.to_string() )[0]['txids']

for txid in txids:
	tx = proxy.gettransaction( txid )
	utxos[txid] = tx
	amount = tx['amount']
	funds -= amount

	print( " utxo tx id: " + str(txid) )
	print( tx )
	print( "utxo amount: " + str(amount) )

funds = int(to_satoshis( funds ))
if funds == 0:
	print( "no funds" )
	exit
print( "      funds: " + str(funds) + " satoshis" )


#
#  4) accept a P2PKH address to send the funds to
#

to_privkey = PrivateKey()
to_pubkey  = to_privkey.get_public_key()
to_address = to_pubkey.get_address()

print( "destination: " + to_address.to_string() )


#
#  5) calculate the appropriate fees with respect to the size of the transaction
#

#
# Fee is proportional to the number of bytes sent over the network
# For simple transactions it is feasible to precompute the transaction size
# In this case however I create the signed transaction with zero fee first, then compute 
# the size and fee and create the transaction again with the real fee included
# We support a satoshi-per-byte price tag and get a price estimate from blockcypher
#

data = requests.get("https://api.blockcypher.com/v1/btc/test3").json()
satoshi_per_byte = data['high_fee_per_kb'] / 1024.0
print( "      price: " + str(satoshi_per_byte) + " satoshi per byte" )

fee = int(0)
for i in range(2):


#
#  6) send all funds that the P2SH address received to the P2PKH address provided 
#

	# transaction inputs with absolute locktime
	txins = []
	for txid in txids:
		txins.append( TxInput( txid, utxos[txid]['details'][0]['vout'], sequence=b'\xfe\xff\xff\xff' ) )

	# transaction output
	amount = funds - fee
	txout = TxOutput( amount, to_address.to_script_pub_key() )

	# create transaction
	tx = Transaction( txins, [txout], BLOCKHEIGHT.to_bytes(4, byteorder='little') )

	if i:
		print( "     amount: " + str(amount) + " satoshis" )
		print( "        fee: " + str(fee) + " satoshis" )


#
#  7) display the raw unsigned transaction
#

	if i:
		print( "raw unsigned transaction:\n" + tx.serialize() )


#
#  8) sign the transaction
#

	j = 0
	for txin in txins:
		signature = from_privkey.sign_input( tx, j, redeem_script )
		txin.script_sig = Script( [signature, from_pubkey.to_hex(), redeem_script.to_hex()] )
		j += 1


#
#  9) display the raw signed transaction
#

	if i:
		print( "raw signed transaction:\n" + tx.serialize() )

	fee = int(tx.get_size() * satoshi_per_byte)


#
# 10) display the transaction id
#

print( "   transaction id: " + tx.get_txid() )


#
# 11) verify that the transaction is valid and will be accepted by the Bitcoin nodes 
#

isvalid = proxy.testmempoolaccept( [tx.serialize()] )[0]['allowed']
print( "transaction valid: " + str(isvalid) )


#
# 12) if the transaction is valid, send it to the blockchain
#

if isvalid:
	proxy.sendrawtransaction( tx.serialize() )
	print( "transaction sent" )
else:
	print( "transaction not sent" )

