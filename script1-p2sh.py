#
# Create a P2SH Bitcoin address where all funds sent to it should be locked until 
# a specific time specified either by block height or UNIX Epoch time.
# 
# Other than the time locking the redeem script should be equivalent to P2PKH.
#
# The program should:
# 1) accept a public (or optionally a private) key for the P2PKH part of the redeem script
# 2) accept a future time expressed either in block height or in UNIX Epoch time
# 3) display the P2SH address
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
# - Enter bitcoin node username and password in top section of this script (or use prepopulated username=test, password=test)
# - Enter private key into top section of this script
#
# Example output from June, 6, 2020
# future time in absolute block height: 1747851
# redeem script: [1747851, 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', '8880768c36754fd2ff1954f213303a680ba67c28', 'OP_EQUALVERIFY', 'OP_CHECKSIG']
# p2sh address: 2MwbgHJBG9mSp54CCG4zaLFyg3yGkZovAAE
#


from bitcoinutils.setup import setup
from bitcoinutils.keys import P2shAddress, PrivateKey, PublicKey
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.script import Script


#
# Enter private key and bitcoin node username and password here
#

USERNAME      = 'test'
PASSWORD_HASH = 'ti8KMfu1Afeh8UZYYN32Lqo5NfBIN6tC-pnSW-OBp7A='
PRIVATE_KEY   = 'cSyZjejfhK5gaVYoG9pgfdMrZzw7rXufpiG4oDaYShanJhwpqGcE'


#
# Connect to testnet
#

setup( 'testnet' )
proxy = NodeProxy( USERNAME, PASSWORD_HASH ).get_proxy()


#
# 1) accept a public (or optionally a private) key for the P2PKH part of the redeem script
#

privkey = PrivateKey( PRIVATE_KEY )
pubkey  = privkey.get_public_key()


#
# 2) accept a future time expressed either in block height or in UNIX Epoch time
#

blockheight = proxy.getblockcount() + 1
print( "future time in absolute block height: " + str(blockheight) )


# get address from public key
address = pubkey.get_address()

# get hash of address
hash = address.to_hash160()

# create redeem script
script = Script( [blockheight, 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', hash, 'OP_EQUALVERIFY', 'OP_CHECKSIG'] )
print( "redeem script: " + str(script.get_script()) )

# get P2SH address
P2SHaddress = P2shAddress.from_script( script )


#
# 3) display the P2SH address
#

print( "p2sh address: " + P2SHaddress.to_string() )
