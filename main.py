import classes
import startup
from apscheduler.schedulers.background import BackgroundScheduler

options = ["1. User Management",
           "2. Ticker Management",
           "3. Alert Preferences",
           "4. Generate Report"]

tickerOptions = [ "1. Add a ticker",
                  "2. Modify a ticker",
                  "3. Delete a ticker"]

user = startup.fetchUser()

communicator = classes.APICommunicator(user.tickers, user) 
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
                user.UpdateUser()
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
                    if len(user.tickers) > 10:
                        print("\nYou've exceeded the limit of tracked tickers. Please delete a ticker if you wish to add a new one\n")
                        break

                    symbol = input("\nTicker symbol: ")
                    lowerSentiment = input("\nLower sentiment tolerance: ")
                    upperSentiment = input("\nUpper sentiment tolerance: ")
                    WSBAlerts = input("\nEnable Wall Street Bets emergency notifications for this ticker? (y/n): ")

                    ticker = classes.TickerObserver(symbol, lowerSentiment, upperSentiment, WSBAlerts)

                    print("\nPlease confirm that these details are correct")
                    print(ticker)
                    option = input("\nConfirm (y/n): ")

                    if option == 'y': 
                        ticker.SaveTicker()
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
                        confirmed = True

            elif option == "3":
                confirmed = False
                while(not confirmed):
                    symbol = input("\nEnter the ticker symbol you wish to delete: ")
                    ticker = user.tickers[symbol] 
                    print("\nPlease confirm that this is the ticker you wish to delete")
                    print(ticker)
                    option = input("\nConfirm (y/n): ")

                    if option == 'y': 
                        user.DeleteTicker(ticker) 
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
                user.UpdateUser()
                confirmed = True
    
    elif option == "4": 
        symbol = input("\nEnter the ticker symbol you wish to generate a report for: ")
        ticker = user.tickers[symbol] 
        ticker.GenerateReport()