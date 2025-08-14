# Telegram Store Bot

## Deployment Instructions (Phone-Friendly)
1. Upload all files to a GitHub repo (mobile app or browser).
2. Create a new app on Heroku.
3. Connect your GitHub repo to Heroku and deploy the main branch.
4. Add config vars in Heroku:
   - BOT_TOKEN = <your bot token>
   - ADMIN_ID = 6872063705
   - BINANCE_API_KEY = <your Binance Pay API key>
   - BINANCE_API_SECRET = <your Binance Pay API secret>
5. Turn on the worker dyno in Heroku.
6. Bot is live. Users can buy products; payments are verified automatically, products delivered, stock updated, and admin notified.
