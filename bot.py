import os, json, time, threading, logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher
from solana_client import SolanaClient
from jupiter_api import JupiterAPI
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('axius')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
if not os.path.exists(CONFIG_PATH):
    raise SystemExit('Please create config.json from config_example.json and set telegram_token')

with open(CONFIG_PATH,'r') as f:
    cfg = json.load(f)

TELEGRAM_TOKEN = cfg['telegram_token']
RPC = cfg.get('solana_rpc')
JUPITER = cfg.get('jupiter_endpoint')

# Very simple in-memory store of user wallets and tasks
USERS = {}  # chat_id -> { 'wallets': [private_key_base58], 'dca': [...], 'follow': {...} }

sol = SolanaClient(RPC)
jup = JupiterAPI(JUPITER)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Welcome to Axius Trading Bot. Use /setkey to set your private key (base58) and /help for commands.')

def help_cmd(update: Update, context: CallbackContext):
    msg = '/setkey <base58>
/buy <mint> <sol_amount>
/sell <mint> <token_amount>
/dca <mint> <sol_amount> <interval_seconds>
/follow <wallet_pubkey>
/status
'
    update.message.reply_text(msg)

def setkey(update: Update, context: CallbackContext):
    chat = update.effective_chat
    args = context.args
    if not args:
        update.message.reply_text('Usage: /setkey <private_key_base58>')
        return
    key = args[0].strip()
    user = USERS.setdefault(chat.id, {'wallets': [], 'dca': [], 'follow': None})
    user['wallets'].append(key)
    update.message.reply_text('Key saved (in-memory). Be careful — this prototype stores keys in plaintext.')

def buy(update: Update, context: CallbackContext):
    chat = update.effective_chat
    args = context.args
    if len(args) < 2:
        update.message.reply_text('Usage: /buy <token_mint> <amount_in_SOL>')
        return
    mint = args[0].strip()
    amount_sol = float(args[1])
    user = USERS.get(chat.id)
    if not user or not user.get('wallets'):
        update.message.reply_text('No wallet set. Use /setkey to add a private key.')
        return
    priv = user['wallets'][-1]
    update.message.reply_text(f'Placing swap: {amount_sol} SOL -> {mint} (queued)')
    try:
        tx = jup.swap_sol_to_token(priv, mint, amount_sol)
        update.message.reply_text('Swap submitted. Signature: ' + tx)
    except Exception as e:
        update.message.reply_text('Error: ' + str(e))

def sell(update: Update, context: CallbackContext):
    chat = update.effective_chat
    args = context.args
    if len(args) < 2:
        update.message.reply_text('Usage: /sell <token_mint> <token_amount>')
        return
    mint = args[0].strip()
    amount = float(args[1])
    user = USERS.get(chat.id)
    if not user or not user.get('wallets'):
        update.message.reply_text('No wallet set. Use /setkey to add a private key.')
        return
    priv = user['wallets'][-1]
    update.message.reply_text(f'Selling {amount} of {mint} (queued)')
    try:
        tx = jup.swap_token_to_sol(priv, mint, amount)
        update.message.reply_text('Swap submitted. Signature: ' + tx)
    except Exception as e:
        update.message.reply_text('Error: ' + str(e))

def dca(update: Update, context: CallbackContext):
    chat = update.effective_chat
    args = context.args
    if len(args) < 3:
        update.message.reply_text('Usage: /dca <mint> <sol_amount_each> <interval_seconds>')
        return
    mint = args[0].strip(); amt = float(args[1]); interval = int(args[2])
    user = USERS.setdefault(chat.id, {'wallets': [], 'dca': [], 'follow': None})
    user['dca'].append({'mint': mint, 'amt': amt, 'interval': interval, 'last': 0})
    update.message.reply_text(f'DCA scheduled: {amt} SOL -> {mint} every {interval} seconds')

def follow(update: Update, context: CallbackContext):
    chat = update.effective_chat
    args = context.args
    if not args:
        update.message.reply_text('Usage: /follow <wallet_pubkey>')
        return
    wallet = args[0].strip()
    user = USERS.setdefault(chat.id, {'wallets': [], 'dca': [], 'follow': None})
    user['follow'] = wallet
    update.message.reply_text(f'Now following wallet: {wallet} (copy-trade enabled)')

def status(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = USERS.get(chat.id, {})
    s = f'Wallets: {len(user.get("wallets",[]))}\nDCA tasks: {len(user.get("dca",[]))}\nFollowing: {user.get("follow")}'
    update.message.reply_text(s)

def start_scheduler(updater: Updater):
    scheduler = BackgroundScheduler()
    def dca_worker():
        for chat_id,user in list(USERS.items()):
            for task in user.get('dca',[]):
                now = time.time()
                if now - task['last'] >= task['interval']:
                    task['last'] = now
                    try:
                        priv = user['wallets'][-1]
                        jup.swap_sol_to_token(priv, task['mint'], task['amt'])
                        logger.info(f'Executed DCA for chat {chat_id}: {task["amt"]} SOL -> {task["mint"]}')
                    except Exception as e:
                        logger.exception('DCA error: %s', e)
    scheduler.add_job(dca_worker, 'interval', seconds=10)
    scheduler.start()

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help_cmd))
    dp.add_handler(CommandHandler('setkey', setkey, pass_args=True))
    dp.add_handler(CommandHandler('buy', buy, pass_args=True))
    dp.add_handler(CommandHandler('sell', sell, pass_args=True))
    dp.add_handler(CommandHandler('dca', dca, pass_args=True))
    dp.add_handler(CommandHandler('follow', follow, pass_args=True))
    dp.add_handler(CommandHandler('status', status))

    start_scheduler(updater)
    updater.start_polling()
    logger.info('Axius bot started.')
    updater.idle()

if __name__ == '__main__':
    main()
