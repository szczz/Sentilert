import database
import classes

def fetchUser():
    user = database.r.exists("User")

    # If the user is not found in the database, collect their details and create a user profile
    if user == 0:
        print("\n######################################################################################################################")
        print("######################################################################################################################")
        print("Welcome to Sentilert! Please enter your contact details in the following prompts so that you can recieve notifications")
        print("######################################################################################################################")
        print("######################################################################################################################\n")

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
                user.UpdateUser()
                confirmed = True
    else:
        # Otherwise, fetch the user's profile and tickers
        print("\n#####################################################################################################################")
        print("Fetching your profile. Please wait.")
        print("#####################################################################################################################\n")

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