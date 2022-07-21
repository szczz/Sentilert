import os
import database
import requests
import matplotlib.pyplot as plt 
import math
from datetime import date
from twilio.rest import Client 
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class APICommunicator:
    marketAuxAPIKey = ''
    twilioSMSAccountSid = ''
    twilioSMSAuthToken = ''
    twilioSendGridAPIKey = ''

    def __init__(self, tickerObservers, user):
        self.tickerObservers = tickerObservers
        self.User = user

    def FetchSentiment(self):
        for ticker in self.tickerObservers:
            request = requests.get("https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&language=en&api_token={key}".format(symbol = ticker, key = APICommunicator.marketAuxAPIKey)).json()
            total = 0 
            count = 0
            for data in request['data']:
                for entity in data['entities']:
                    if entity['symbol'] == ticker:
                        total += entity['sentiment_score'] 
                        count += 1
        
            overallSentiment = round(total / count, 4)
            openingSentiment = database.r.hget(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Open")
            if openingSentiment is None:
                database.r.hset(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Open", overallSentiment)
            else:
                database.r.hset(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Close", overallSentiment)
            
            trigger = self.tickerObservers[ticker].ReceiveSentiment(overallSentiment)
            if trigger is not None:
                bound = 0
                if trigger == "lower": bound = self.tickerObservers[ticker].lowerSentiment
                else: bound = self.tickerObservers[ticker].upperSentiment

                if self.User.alertPreferences['phone'] == 'y':
                    self.SendSMSAlert('This is a Sentilert! {symbol} sentiment has exceeded your {trigger} threshold of {bound} with a sentiment of {sentiment}!'.format(symbol = self.tickerObservers[ticker].tickerSymbol, trigger = trigger, bound = bound, sentiment = overallSentiment))
                
                if self.User.alertPreferences['email'] == 'y':
                    subject = 'Sentiment has shifted on {symbol}!'.format(symbol = self.tickerObservers[ticker].tickerSymbol)
                    htmlContent = '<strong>Sentilert Notification!</strong><br><br>{symbol} sentiment has exceeded your {trigger} threshold of {bound} with a sentiment of {sentiment}!'.format(symbol = self.tickerObservers[ticker].tickerSymbol, trigger = trigger, bound = bound, sentiment = overallSentiment)
                    self.SendEmailAlert(subject, htmlContent)

    def FetchWSBList(self):
        request = requests.get("https://tradestie.com/api/v1/apps/reddit").json()
        for ticker in request:
            if ticker['ticker'] in self.tickerObservers and self.tickerObservers[ticker['ticker']].wsbAlerts == 'y':
                if self.User.alertPreferences['phone'] == 'y':
                    self.SendSMSAlert('This is a Sentilert! {symbol} has appeared in R/WallStreetBets top 50 discussed!'.format(symbol = self.tickerObservers[ticker['ticker']].tickerSymbol))
                
                if self.User.alertPreferences['email'] == 'y':
                    subject = '{symbol} has appeared in R/WallStreetBets top 50 discussed!'.format(symbol = self.tickerObservers[ticker['ticker']].tickerSymbol)
                    htmlContent = '<strong>Sentilert Notification!</strong><br><br>{symbol} has appeared in R/WallStreetBets top 50 discussed!'.format(symbol = self.tickerObservers[ticker['ticker']].tickerSymbol)
                    self.SendEmailAlert(subject, htmlContent)

    def SendSMSAlert(self, body):
        client = Client(APICommunicator.twilioSMSAccountSid, APICommunicator.twilioSMSAuthToken) 
        client.messages.create(   
                                messaging_service_sid='MGc0b32f1eca4dd4599b070d0daaa70279',
                                body=body,      
                                to=self.User.userPhoneNumber) 

    def SendEmailAlert(self,subject, htmlContent ):
        message = Mail(
                    from_email='szczermw@mcmaster.ca',
                    to_emails=self.User.userEmail,
                    subject=subject,
                    html_content=htmlContent)

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
        if sentiment < float(self.lowerSentiment): return "lower"
        elif sentiment > float(self.upperSentiment): return "upper"
        
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
        history = database.r.hgetall(self.tickerSymbol + "_History")
        x = []
        y = []

        for sentiment in history:
            x.append(sentiment)
            y.append(float(history[sentiment]))

        plt.figure(figsize=(10,10))
        plt.plot(x, y) 
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
