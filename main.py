import classes
import database
import startup

#database.r.delete("User")

options = ["1. User Management",
           "2. Ticker Management",
           "3. Alert Prefrences"]

user = startup.fetchUser()

app_running = True
while(app_running):
    print("\nChoose from the following options: ")
    for o in options:
            print(o)

    option = input("\nEnter your choice here or press f to disable Sentilert: ")
    if option == "f": 
        option = input("\nAre you sure? This will disable alerts and sentiment checks (y/n): ")
        if option == "y": app_running = False


