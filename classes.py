import database
import requests
from datetime import date

class APICommunicator:
    def __init__(self,marketAuxAPIKey, twilioSMSAPIKey, twilioSendGridAPIKey, tickerObservers):
        self.marketAuxAPIKey = marketAuxAPIKey
        self.twilioSMSAPIKey = twilioSMSAPIKey
        self.twilioSendGridAPIKey = twilioSendGridAPIKey
        self.tickerObservers = tickerObservers

    def FetchSentiment(self):
        for ticker in self.tickerObservers:
            request = requests.get("https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&language=en&api_token={key}".format(symbol = ticker, key = self.marketAuxAPIKey)).json()
            total = 0 
            count = 0
            for data in request['data']:
                for entity in data['entities']:
                    if entity['symbol'] == ticker:
                        total += entity['sentiment_score'] 
                        count += 1
        
            overallSentiment = total / count
            openingSentiment = database.r.hget(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Open")
            if openingSentiment is None:
                database.r.hset(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Open", overallSentiment)
            else:
                database.r.hset(ticker + "_History", date.today().strftime("%d/%m/%Y") + " Close", overallSentiment)
            
            if self.tickerObservers[ticker].ReceiveSentiment(overallSentiment):
                self.SendSMSAlert(ticker)
                self.SendEmailAlert(ticker)

    def FetchWSBList(self):
        pass

    def SendSMSAlert(self,observer):
        pass

    def SendEmailAlert(self,observer):
        pass


class TickerObserver:
    def __init__(self,tickerSymbol, lowerSentiment, upperSentiment, wsbAlerts):
        self.tickerSymbol = tickerSymbol
        self.lowerSentiment = lowerSentiment
        self.upperSentiment = upperSentiment
        self.wsbAlerts = wsbAlerts

    def ReceiveSentiment(self, sentiment):
        if sentiment < float(self.lowerSentiment): return True
        elif sentiment > float(self.upperSentiment): return True
        
    def ModifySentiment(self):
        database.r.hset(self.tickerSymbol, "lowerSentiment", self.lowerSentiment)
        database.r.hset(self.tickerSymbol, "upperSentiment", self.upperSentiment)
       
    def UpdateAlerts(self):
        database.r.hset(self.tickerSymbol, "WSBAlerts", self.wsbAlerts)

    def GenerateReport(self):
        pass

    def __repr__(self):
        return "Ticker: " + self.tickerSymbol + "\nLower Sentiment: " + self.lowerSentiment + "\nUpper Sentiment: " + self.upperSentiment + "\nWSB Alerts: " + self.wsbAlerts

class User:
    def __init__(self, userEmail, userPhoneNumber, alertPreferences, tickers):
        self.userEmail = userEmail
        self.userPhoneNumber = userPhoneNumber
        self.alertPreferences = alertPreferences
        self.tickers = tickers

    def AddTicker(self, ticker):
        self.tickers[ticker.tickerSymbol] = ticker

    def DeleteTicker(self, ticker):
        self.tickers.pop(ticker.tickerSymbol)

    def UpdateTicker(self, symbol):
        pass
    
    def __repr__(self):
        return "Email: " + self.userEmail + "\nPhone: " + self.userPhoneNumber + "\nSMS Alerts: " + self.alertPreferences['phone'] + "\nEmail Alerts: " + self.alertPreferences['email']