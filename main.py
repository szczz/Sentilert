import classes
import database
import startup
from apscheduler.schedulers.background import BackgroundScheduler

# database.r.delete("User")
# database.r.delete("MSFT")
# database.r.delete("UserTickers")

marketAuxAPIKey = ''
twilioSMSAccountSid = ''
twilioSMSAuthToken = ''
twilioSendGridAPIKey = ''

options = ["1. User Management",
           "2. Ticker Management",
           "3. Alert Prefrences",
           "4. Generate Report"]

tickerOptions = [ "1. Add a ticker",
                  "2. Modify a ticker",
                  "3. Delete a ticker"]


user = startup.fetchUser()

communicator = classes.APICommunicator(marketAuxAPIKey, twilioSMSAccountSid, twilioSMSAuthToken, twilioSendGridAPIKey, user.tickers, user) 
scheduler = BackgroundScheduler(timezone="America/Toronto")
#scheduler.add_job(communicator.FetchSentiment, 'interval', hours=10)
scheduler.add_job(communicator.FetchSentiment, trigger='cron', hour='8,15', minute='30')
scheduler.add_job(communicator.FetchWSBList, trigger='cron', hour='8,15', minute='30')
scheduler.start()

# communicator.FetchSentiment()
# communicator.FetchWSBList()


app_running = True
while(app_running):
    print("\nChoose from the following options: ")
    for o in options:
            print(o)

    option = input("\nEnter your choice here or press f to disable Sentilert: ")
    if option == "f": 
        option = input("\nAre you sure? This will disable alerts and sentiment checks (y/n): ")
        if option == "y": app_running = False
    elif option == "1": 
        print("\nEnter you updated phone number and email address here.")

        confirmed = False
        while(not confirmed):
            phone = input("\nPhone Number: ")
            email = input("\nEmail Address: ")
            user.userEmail = email
            user.userPhoneNumber = phone

            print("\nPlease confirm that these details are correct")
            print(user)
            option = input("\nConfirm (y/n): ")

            if option == 'y': 
                database.r.hset("User", "email", email)
                database.r.hset("User", "phone", phone)
                confirmed = True
    elif option == '2':
        subMenu = True
        while(subMenu):
            for o in tickerOptions:
                print(o)

            option = input("\nEnter your choice here or press m to return to the main menu: ")
            if option == "m": 
                subMenu = False
            elif option == "1":
                confirmed = False
                while(not confirmed):
                    symbol = input("\nTicker symbol: ")
                    lowerSentiment = input("\nLower sentiment tolerance: ")
                    upperSentiment = input("\nUpper sentiment tolerance: ")
                    WSBAlerts = input("\nEnable Wall Street Bets emergency notifications for this ticker? (y/n): ")

     
                    ticker = classes.TickerObserver(symbol, lowerSentiment, upperSentiment, WSBAlerts)

                    print("\nPlease confirm that these details are correct")
                    print(ticker)
                    option = input("\nConfirm (y/n): ")

                    if option == 'y': 
                        database.r.hset(symbol, "symbol", symbol)
                        database.r.hset(symbol, "lowerSentiment", lowerSentiment)
                        database.r.hset(symbol, "upperSentiment", upperSentiment)
                        database.r.hset(symbol, "WSBAlerts", WSBAlerts)
                        database.r.hset("UserTickers", symbol, symbol)
                        user.AddTicker(ticker)
                        confirmed = True
            elif option == "2":
                confirmed = False
                while(not confirmed):
                    symbol = input("\nEnter the ticker symbol you wish to update: ")
                    lowerSentiment = input("\nLower sentiment tolerance: ")
                    upperSentiment = input("\nUpper sentiment tolerance: ")
                    WSBAlerts = input("\nEnable Wall Street Bets emergency notifications for this ticker? (y/n): ")
                    
                    ticker = classes.TickerObserver(symbol, lowerSentiment, upperSentiment, WSBAlerts)

                    print("\nPlease confirm that these details are correct")
                    print(ticker)
                    option = input("\nConfirm (y/n): ")

                    if option == 'y': 
                        ticker.ModifySentiment()
                        ticker.UpdateAlerts()
                        user.UpdateTicker(ticker.tickerSymbol)
                        confirmed = True
            elif option == "3":
                confirmed = False
                while(not confirmed):
                    symbol = input("\nEnter the ticker symbol you wish to delete: ")
                    ticker = classes.TickerObserver(database.r.hget(symbol, "symbol"), database.r.hget(symbol, "lowerSentiment"), database.r.hget(symbol, "upperSentiment"), database.r.hget(symbol, "WSBAlerts"))
                    print("\nPlease confirm that this is the ticker you wish to delete")
                    print(ticker)
                    option = input("\nConfirm (y/n): ")

                    if option == 'y': 
                        user.DeleteTicker(ticker)
                        database.r.hdel("UserTickers", symbol)
                        database.r.delete(symbol)         
                        database.r.delete(symbol + "_History")              
                        confirmed = True
    elif option == "3": 
        print("\nEnter your updated alert preferences here")

        confirmed = False
        while(not confirmed):
            smsAlerts = input("\nRecieve SMS alerts? (y/n): ")
            emailAlerts = input("\nRecieve email alerts? (y/n): ")

            alertPreferences = {
                'phone': smsAlerts,
                'email': emailAlerts
            }

            user.alertPreferences = alertPreferences

            print("\nPlease confirm that these details are correct")
            print(user)
            option = input("\nConfirm (y/n): ")

            if option == 'y': 
                database.r.hset("User", "smsAlerts", smsAlerts)
                database.r.hset("User", "emailAlerts", emailAlerts)
                confirmed = True
    
    elif option == "4": 
        symbol = input("\nEnter the ticker symbol you wish to generate a report for: ")
        ticker = classes.TickerObserver(database.r.hget(symbol, "symbol"), database.r.hget(symbol, "lowerSentiment"), database.r.hget(symbol, "upperSentiment"), database.r.hget(symbol, "WSBAlerts"))
        ticker.GenerateReport()