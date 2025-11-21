# Axius Trading Bot (Telegram) - Prototype
**Warning & Important:** This project is a **prototype** educational implementation provided at user's request. It mimics many high-level features commonly found in Telegram Solana trading bots (sniper, DCA, copy-trade, limit orders) but **is not production-ready**. Running real trades requires careful security review, on-chain testing, and responsibility for private keys. Use at your own risk.

## What's included
- Telegram bot code (`bot.py`) implementing basic commands: /start, /setkey, /buy, /sell, /dca, /follow, /status
- Solana helper (`solana_client.py`) using `solana` Python library for wallet & RPC interaction
- Jupiter API helper (`jupiter_api.py`) to prepare/route swaps through Jupiter aggregator (uses public HTTP endpoints at runtime)
- Utilities and simple background worker for DCA and copy-trade simulation
- `config_example.json` with configuration template
- `requirements.txt` listing Python dependencies

## Key features (prototype)
- Buy / Sell tokens (via Jupiter swap API)
- Dollar-Cost Averaging (DCA) scheduler
- Copy-trade: follow a wallet and optionally mirror its SOL->token swaps
- Simple limit / stop-loss logic (polling-based)
- Multi-wallet support (store private keys in-memory / file — **not safe** for production)

## Notable limitations & safety
- **Security:** Private keys are handled in cleartext in this prototype. DO NOT store real funds unless you fully secure the environment.
- **Speed/MEV:** This implementation is not optimized for low-latency sniping or MEV protection.
- **Auditing & Testing:** No audits. Thoroughly test on devnets before mainnet use.
- **Legality & Ethics:** Automating trades to front-run, manipulate markets, or perform abusive strategies may be illegal or unethical. Use responsibly.

## How to use (quick)
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `config_example.json` to `config.json` and fill your Telegram bot token and RPC settings.
3. Run: `python bot.py`
4. Use Telegram chat with your bot to send commands (`/setkey`, `/buy <mint> <sol_amount>`, ...)

## References
This prototype was created by synthesizing features commonly found in several Solana Telegram trading bots (sniper, DCA, copy-trade). For reference reading about popular bots and their features see public writeups and repositories (e.g. Trojan On Solana).

