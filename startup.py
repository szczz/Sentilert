import database
import classes

def fetchUser():
    user = database.r.hget("User", "email")

    if user is None:
        print("\n#####################################################################################################################")
        print("#####################################################################################################################")
        print("Welcome to Sentilert! Please enter your contact details in the following prompt so that you can recieve notifications")
        print("#####################################################################################################################")
        print("#####################################################################################################################\n")

        confirmed = False
        while(not confirmed):
            phone = input("\nPhone Number: ")
            email = input("\nEmail Address: ")
            smsAlerts = input("\nRecieve SMS alerts? (y/n): ")
            emailAlerts = input("\nRecieve email alerts? (y/n): ")

            alertPreferences = {
                'phone': smsAlerts,
                'email': emailAlerts
            }

            user = classes.User(email, phone,alertPreferences, {})

            print("\nPlease confirm that these details are correct")
            print(user)
            option = input("\nConfirm (y/n): ")

            if option == 'y': 
                database.r.hset("User", "email", email)
                database.r.hset("User", "phone", phone)
                database.r.hset("User", "smsAlerts", smsAlerts)
                database.r.hset("User", "emailAlerts", emailAlerts)
                confirmed = True
    else:
        alertPreferences = {
            'phone': database.r.hget("User", "smsAlerts"),
            'email': database.r.hget("User", "emailAlerts")
        }

        tickers = database.r.hgetall("UserTickers")
        observers = {}
        for ticker in tickers: 
            observer = classes.TickerObserver(ticker, database.r.hget(ticker, "lowerSentiment"), database.r.hget(ticker, "upperSentiment"), database.r.hget(ticker, "WSBAlerts"))
            observers[ticker] = (observer)

        user = classes.User(database.r.hget("User", "email"),
                            database.r.hget("User", "phone"),
                            alertPreferences,
                            observers)
    return user