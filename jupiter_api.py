# Minimal Jupiter interaction helpers.
# This module calls Jupiter public quote & swap endpoints to build and send swaps.
# At runtime the code will make HTTP requests to the configured Jupiter endpoint.
import requests, json
from solana_client import SolanaClient
from solana.keypair import Keypair
import base58

class JupiterAPI:
    def __init__(self, endpoint='https://quote-api.jup.ag'):
        self.endpoint = endpoint.rstrip('/')

    def get_quote(self, in_amount_sol, out_mint):
        # Query Jupiter quote API for a SOL->token route
        params = {
            'amount': int(in_amount_sol * 1_000_000_000), # lamports
            'inputMint': 'So11111111111111111111111111111111111111112', # SOL wrapped
            'outputMint': out_mint,
            'slippageBps': 1000
        }
        r = requests.get(self.endpoint + '/v4/quote', params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def swap_sol_to_token(self, private_key_base58, out_mint, sol_amount):
        # 1) get quote
        q = self.get_quote(sol_amount, out_mint)
        if not q or 'data' not in q or not q['data']:
            raise Exception('No route found')
        route = q['data'][0]
        # 2) Prepare swap payload
        payload = {
            'route': route,
            'userPublicKey': Keypair.from_secret_key(base58.b58decode(private_key_base58)).public_key.__str__(),
            'wrapUnwrapSOL': True
        }
        # 3) Ask Jupiter to build transaction
        r = requests.post(self.endpoint + '/v4/swap', json=payload, timeout=20)
        r.raise_for_status()
        swap_res = r.json()
        # 4) The response may contain serialized transactions to sign & send — leave this as an exercise for the integrator.
        # For prototype, we'll return the swap response for inspection.
        return json.dumps(swap_res)

    def swap_token_to_sol(self, private_key_base58, in_mint, token_amount):
        # NOTE: Implementing token->SOL swap mirrors above but uses inputMint/outMint swapped.
        # This prototype returns a stub response.
        return 'prototype-sell-tx-placeholder'
