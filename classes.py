class APICommunicator:
    def __init__(self,marketAuxAPIKey, twilioSMSAPIKey, twilioSendGridAPIKey, userId, tickerObservers):
        self.__marketAuxAPIKey = marketAuxAPIKey
        self.__twilioSMSAPIKey = twilioSMSAPIKey
        self.__twilioSendGridAPIKey = twilioSendGridAPIKey
        self.__userId = userId
        self.__tickerObservers = tickerObservers

    @classmethod
    def FetchSentiment(cls):
        pass

    @classmethod
    def FetchWSBList(cls):
        pass

    @classmethod
    def SendSMSAlert(cls):
        pass

    @classmethod
    def SendEmailAlert(cls):
        pass


class TickerObserver:
    def __init__(self,tickerSymbol, lowerSentiment, upperSentiment, wsbAlerts):
        self.__tickerSymbol = tickerSymbol
        self.__lowerSentiment = lowerSentiment
        self.__upperSentiment = upperSentiment
        self.__wsbAlerts = wsbAlerts

    @classmethod
    def ModifySentiment(cls):
        pass

    @classmethod
    def UpdateAlerts(cls):
        pass

    @classmethod
    def GenerateReport(cls):
        pass

class User:
    def __init__(self,userId, userEmail, userPhoneNumber, alertPreferences, tickers):
        self.__userId = userId
        self.__userEmail = userEmail
        self.__userPhoneNumber = userPhoneNumber
        self.__alertPreferences = alertPreferences
        self.__tickers = tickers

    @classmethod
    def AddTicker(cls):
        pass

    @classmethod
    def DeleteTicker(cls):
        pass

    @classmethod
    def UpdateTicker(cls):
        pass
    
    def __repr__(self):
        return "Email: " + self.__userEmail + "\nPhone: " + self.__userPhoneNumber + "\nSMS Alerts: " + self.__alertPreferences['email'] + "\nEmail Alerts: " + self.__alertPreferences['phone']