import os
import database
import requests
import math
import matplotlib.pyplot as plt 
from datetime import date
from twilio.rest import Client 
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class APICommunicator:
    __instance = None
    marketAuxAPIKey = os.getenv('MARKET_AUX_API_KEY')
    twilioSMSAccountSid = os.getenv('TWILIO_SMS_ACCOUNT_SID')
    twilioSMSAuthToken = os.getenv('TWILI_SMS_AUTH_TOKEN')
    twilioMessagingServiceSid = os.getenv('TWILIO_MESSAGING_SERVICE_SID')
    twilioSendGridAPIKey = os.getenv('TWILIO_SEND_GRID_API_KEY')
    
    # Used to pass in the TickerObservers and User. As discussed in the proposal, I want to explicitly unsubscribe observers through the menu to avoid the Observer pattern performance pitfall.
    # Singleton example inspired from https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_singleton.htm
    def __init__(self, tickerObservers, user):
        # This is a Singleton class. It should only be instantiated once. Throw an exception if an attempt to instantiate it occurs again.
        if APICommunicator.__instance is not None:
            raise Exception("This is a singleton class. It can only be instantiated once!")
        else:
            APICommunicator.__instance = self

        self.tickerObservers = tickerObservers
        self.User = user
    
    # Unused in this system, however if the application were to grow, it would be useful for fetching the Singleton instance.
    @staticmethod
    def GetInstance(tickerObservers, user):
        if APICommunicator.__instance is None:
            APICommunicator(tickerObservers, user)
        return APICommunicator.__instance

    def FetchSentiment(self):
        for ticker in self.tickerObservers:
            request = requests.get("https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&language=en&api_token={key}" \
                                    .format(symbol = ticker, key = APICommunicator.marketAuxAPIKey)).json()
            
            # The free version of the MarketAux API does not give me access to directly fetch the aggregated sentiment score. Instead I can access the sentiment score of each news piece that mentions the ticker symbol.
            # From here I'm simply looping over the fetched data and calculating the aggregated score myself.
            sentiment = []
            for data in request['data']:
                for entity in data['entities']:
                    if entity['symbol'] == ticker:
                        sentiment.append(entity['sentiment_score'])
        
            overallSentiment = round(sum(sentiment) / len(sentiment), 4)
            
            # Check whether this is the opening or closing sentiment and store it in the database accordingly.
            openingSentiment = database.r.hget(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Open")
            if openingSentiment is None:
                database.r.hset(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Open", overallSentiment)
            else:
                database.r.hset(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Close", overallSentiment)
            
            # Notify the Observer with the new sentiment data.
            trigger = self.tickerObservers[ticker].ReceiveSentiment(overallSentiment)
            if trigger is not None:
                bound = 0
                if trigger == "lower": bound = self.tickerObservers[ticker].lowerSentiment
                else: bound = self.tickerObservers[ticker].upperSentiment

                # Check the User's alert preference and call the required notification methods
                if self.User.alertPreferences['phone'] == 'y':
                    self.SendSMSAlert('This is a Sentilert! {symbol} sentiment has exceeded your {trigger} threshold of {bound} with a sentiment of {sentiment}!' \
                                       .format(symbol = self.tickerObservers[ticker].tickerSymbol, trigger = trigger, bound = bound, sentiment = overallSentiment))
                
                if self.User.alertPreferences['email'] == 'y':
                    subject = 'Sentiment has shifted on {symbol}!'.format(symbol = self.tickerObservers[ticker].tickerSymbol)
                    htmlContent = '<strong>Sentilert Notification!</strong><br><br>{symbol} sentiment has exceeded your {trigger} threshold of {bound} with a sentiment of {sentiment}!' \
                                   .format(symbol = self.tickerObservers[ticker].tickerSymbol, trigger = trigger, bound = bound, sentiment = overallSentiment)
                    self.SendEmailAlert(subject, htmlContent)

    def FetchWSBList(self):
        request = requests.get("https://tradestie.com/api/v1/apps/reddit").json()
        for ticker in request:

            # Check to see if the ticker is found in the list of observers then notify the correct Observer object
            if ticker['ticker'] in self.tickerObservers and self.tickerObservers[ticker['ticker']].ReceiveWSBAlert(ticker['ticker']):

                # Check the User's alert preference and call the required notification methods
                if self.User.alertPreferences['phone'] == 'y':
                    self.SendSMSAlert('This is a Sentilert! {symbol} has appeared in R/WallStreetBets top 50 discussed!' \
                                       .format(symbol = self.tickerObservers[ticker['ticker']].tickerSymbol))
                
                if self.User.alertPreferences['email'] == 'y':
                    subject = '{symbol} has appeared in R/WallStreetBets top 50 discussed!'.format(symbol = self.tickerObservers[ticker['ticker']].tickerSymbol)
                    htmlContent = '<strong>Sentilert Notification!</strong><br><br>{symbol} has appeared in R/WallStreetBets top 50 discussed!' \
                                   .format(symbol = self.tickerObservers[ticker['ticker']].tickerSymbol)
                    self.SendEmailAlert(subject, htmlContent)

    def SendSMSAlert(self, body):
        # Initializes the Twilio SMS client and sends the alert
        client = Client(APICommunicator.twilioSMSAccountSid, APICommunicator.twilioSMSAuthToken) 
        client.messages.create(   
                                messaging_service_sid=APICommunicator.twilioMessagingServiceSid,
                                body=body,      
                                to=self.User.userPhoneNumber) 

    def SendEmailAlert(self,subject, htmlContent):
        # Form the email message
        message = Mail(
                    from_email='szczermw@mcmaster.ca',
                    to_emails=self.User.userEmail,
                    subject=subject,
                    html_content=htmlContent)

        # Initialize the Sendgrid client and send the alert
        try:
            sg = SendGridAPIClient(APICommunicator.twilioSendGridAPIKey)
            sg.send(message)
        except Exception as e:
            print(e)

class TickerObserver:
    def __init__(self,tickerSymbol, lowerSentiment, upperSentiment, wsbAlerts):
        self.tickerSymbol = tickerSymbol
        self.lowerSentiment = lowerSentiment
        self.upperSentiment = upperSentiment
        self.wsbAlerts = wsbAlerts
    
    def __repr__(self):
        return "Ticker: " + self.tickerSymbol + "\nLower Sentiment: " + self.lowerSentiment + "\nUpper Sentiment: " + self.upperSentiment + "\nWSB Alerts: " + self.wsbAlerts

    def ReceiveSentiment(self, sentiment):
        # Check to see if the sentiment is above or under the defined thresholds
        if sentiment < float(self.lowerSentiment): return "lower"
        elif sentiment > float(self.upperSentiment): return "upper"

    def ReceiveWSBAlert(self, ticker):
        # Check if WallStreetBets alerts are enabled for this ticker
        if self.tickerSymbol == ticker and self.wsbAlerts == "y": return True
    
    def ModifySentiment(self):
        database.r.hset(self.tickerSymbol, "lowerSentiment", self.lowerSentiment)
        database.r.hset(self.tickerSymbol, "upperSentiment", self.upperSentiment)
       
    def UpdateAlerts(self):
        database.r.hset(self.tickerSymbol, "WSBAlerts", self.wsbAlerts)

    def SaveTicker(self):
        database.r.hset(self.tickerSymbol, "symbol", self.tickerSymbol)
        database.r.hset(self.tickerSymbol, "lowerSentiment", self.lowerSentiment)
        database.r.hset(self.tickerSymbol, "upperSentiment", self.upperSentiment)
        database.r.hset(self.tickerSymbol, "WSBAlerts", self.wsbAlerts)
        database.r.hset("UserTickers", self.tickerSymbol, self.tickerSymbol)

    def GenerateReport(self):
        # Fetch the ticker history
        history = database.r.hgetall(self.tickerSymbol + "_History")
        
        x = []
        y = []
        for sentiment in history:
            x.append(sentiment)
            y.append(float(history[sentiment]))

        # Plot and display the sentiment data

        plt.figure(figsize=(20,20))
        plt.plot(x, y) 
        plt.xticks(rotation=90)
        plt.xlabel('Open / Close history') 
        plt.ylabel('Sentiment') 

        plt.title('{symbol} Sentiment History'.format(symbol = self.tickerSymbol))

        plt.show()

class User:
    def __init__(self, userEmail, userPhoneNumber, alertPreferences, tickers):
        self.userEmail = userEmail
        self.userPhoneNumber = userPhoneNumber
        self.alertPreferences = alertPreferences
        self.tickers = tickers

    def __repr__(self):
        return "Email: " + self.userEmail + "\nPhone: " + self.userPhoneNumber + "\nSMS Alerts: " + self.alertPreferences['phone'] + "\nEmail Alerts: " + self.alertPreferences['email']

    def AddTicker(self, ticker):
        self.tickers[ticker.tickerSymbol] = ticker

    def DeleteTicker(self, ticker):
        self.tickers.pop(ticker.tickerSymbol)
        database.r.hdel("UserTickers", ticker.tickerSymbol)
        database.r.delete(ticker.tickerSymbol)         
        database.r.delete(ticker.tickerSymbol + "_History")             

    def UpdateUser(self):
        database.r.hset("User", "email", self.userEmail)
        database.r.hset("User", "phone", self.userPhoneNumber)
        database.r.hset("User", "smsAlerts", self.alertPreferences['phone'])
        database.r.hset("User", "emailAlerts", self.alertPreferences['email'])
