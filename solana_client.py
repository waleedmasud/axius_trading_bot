from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.publickey import PublicKey
import base58, json

class SolanaClient:
    def __init__(self, rpc_url):
        self.rpc = Client(rpc_url)

    def keypair_from_base58(self, b58str):
        raw = base58.b58decode(b58str)
        return Keypair.from_secret_key(raw)

    def get_balance(self, pubkey):
        res = self.rpc.get_balance(PublicKey(pubkey))
        return res.get('result',{}).get('value',0)/1e9

    def send_signed_transaction(self, signed_tx):
        # signed_tx should be base58-encoded transaction bytes
        return self.rpc.send_raw_transaction(signed_tx)
