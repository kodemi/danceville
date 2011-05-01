#-*- coding: utf-8 -*-

from suds import WebFault
from suds.client import Client
import logging

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

#logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').addHandler(NullHandler())
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

# Статусы сообщений
DEVINO_STATE_NOT_SENDED = -1                # Отправлено
DEVINO_STATE_LOCAL_QUEUED = -2              # В очереди 
DEVINO_STATE_DELETED = -97                  # Удалено
DEVINO_STATE_PARKED = -98                   # Остановлено
DEVINO_STATE_QUEUED = -40                   # Ожидание
DEVINO_STATE_SENDING_TO_GATEWAY = -30       # Отправлено в шлюз
DEVINO_STATE_SENDING_TO_RECIPIENT = -20     # Отправлено получателю
DEVINO_STATE_SENT = -10                     # Отправлено
DEVINO_STATE_DELIVERED_TO_RECIPIENT = 0     # Доставлено

# Ошибочные статусы
DEVINO_STATE_ERROR_INVALID_DESTINATION_ADDRESS = 11     # Неверно введен адрес получателя
DEVINO_STATE_ERROR_INVALID_SOURCE_ADDRESS = 10          # Неверно введен адрес отправителя
DEVINO_STATE_ERROR_INCOMPATIBLE_DESTINATION = 41        # Недопустимый адрес получателя
DEVINO_STATE_ERROR_REJECTED = 42                        # Отклонено
DEVINO_STATE_EXPIRED = 46                               # Просрочено
DEVINO_STATE_UNKNOWN = 255                              # Неизвестно

class DevinoSmsClientException(Exception):
    def __init__(self, value):
        self.value = value
           
    def __unicode__(self):
        return self.value
    
    def __str__(self):
        return unicode(self.value).encode('utf-8')
    
class DevinoSmsClient:
    def __init__(self, login, password):
        url = 'http://ws.devinosms.com/SmsService.asmx?wsdl'
        self.client = Client(url)
        self._session_id = self.GetSessionID(login, password)
                
    def GetMessagesStateDescription(self, state):
        states = {
            DEVINO_STATE_NOT_SENDED: "Отправлено",
            DEVINO_STATE_LOCAL_QUEUED: "В очереди",
            DEVINO_STATE_DELETED: "Удалено",
            DEVINO_STATE_PARKED: "Остановлено",
            DEVINO_STATE_QUEUED: "Ожидание",
            DEVINO_STATE_SENDING_TO_GATEWAY: "Отправлено в шлюз",
            DEVINO_STATE_SENDING_TO_RECIPIENT: "Отправлено получателю",
            DEVINO_STATE_SENT: "Отправлено",
            DEVINO_STATE_DELIVERED_TO_RECIPIENT: "Доставлено",
            DEVINO_STATE_ERROR_INVALID_DESTINATION_ADDRESS: "Неверно введен адрес получателя",
            DEVINO_STATE_ERROR_INVALID_SOURCE_ADDRESS: "Неверно введен адрес отправителя",
            DEVINO_STATE_ERROR_INCOMPATIBLE_DESTINATION: "Недопустимый адрес получателя",
            DEVINO_STATE_ERROR_REJECTED: "Отклонено",
            DEVINO_STATE_EXPIRED: "Просрочено",
            DEVINO_STATE_UNKNOWN: "Неизвестно",
        }
        default = "Неизвестный статус"
        return states.get(state, default)

    def SendMessage(self, source_address, destination_addresses, text, delay_until_utc=None):
        """
        Передача простого текстового SMS-сообщения
        
        source_address: Адрес отправителя сообщения. 
            До 11 латинских символов или до 15 цифровых. 
            Тип данных: str (или unicode).
        destination_addresses: Мобильный телефонный номер получателя сообщения, 
            в международном формате: код страны + код сети + номер телефона. 
            Тип данных: str (или unicode) или [str] (или [unicode]).
        text: Текст сообщения. Тип данных: unicode (или str для латиницы).
        delay_until_utc: Дата и время отправки. 
            Если не требуется отложенная отправка, то передавать данный параметр не нужно. 
            Тип данных: datetime.datetime.
        Возвращаемое значение: Идентификаторы сообщений. 
            Тип данных: [suds.sax.text.Text] (suds.sax.text.Text - наследник str).
                 
        """
        if isinstance(destination_addresses, str):
            destination_addresses = [destination_addresses]
        dest = { 'string': destination_addresses }
        message = {
            'Data': text,
            'DelayUntilUtc': delay_until_utc,
            'DestinationAddresses': dest,
            'SourceAddress': source_address,
            'ReceiptRequested': True
        }
        try:
            return self.client.service.SendMessage(self._session_id, message).string   
        except WebFault as e:
            raise  DevinoSmsClientException(e.fault.faultstring)
            
    def SendMessageByTimeZone(self, source_address, destination_address, text, send_date):
        """
        Передача простого текстового SMS-сообщения с учётом часового пояса адресата.
        
        source_address: Адрес отправителя сообщения. 
            До 11 латинских символов или до 15 цифровых. 
            Тип данных: str (или unicode).
        destination_address: Мобильный телефонный номер получателя сообщения, 
            в международном формате: код страны + код сети + номер телефона. 
            Тип данных: str (или unicode).
        text: Текст сообщения. Тип данных: unicode (или str для латиницы).
        send_date: Дата и время отправки (локальное время абонента). 
            Тип данных: datetime.datetime.
        Возвращаемое значение: Идентификатор сообщения. 
            Тип данных: [suds.sax.text.Text] (suds.sax.text.Text - наследник str).
        
        """
        message = {
            'data': text,
            'destinationAddress': destination_address,
            'sourceAddress': source_address,
            'sendDate': send_date.isoformat()
        }
        try:
            return self.client.service.SendMessageByTimeZone(self._session_id, **message).string     
        except WebFault as e:
            raise  DevinoSmsClientException(e.fault.faultstring)
            
    def GetMessageState(self, message_id):
        """
        Запрос на получение статуса отправленного SMS-сообщения.
        
        message_id: Идентификатор сообщения. Тип данных: str.
        Возвращаемое значение: Статус сообщения. Тип данных: int.
        
        """
        try:
            return self.client.service.GetMessageState(self._session_id, message_id).State
        except WebFault as e:
            raise  DevinoSmsClientException(e.fault.faultstring)
            
    def GetIncomingMessages(self, min_date_utc, max_date_utc):
        """
        Запрос на получение входящих сообщений.
        
        min_date_utc: Минимальное значение периода за который происходит выборка входящих сообщений. 
            Тип данных: datetime.datetime.
        max_date_utc: Максимальное значение периода за который происходит выборка входящих сообщений. 
            Тип данных: datetime.datetime.
        Возвращаемое значение: Полученные сообщения. 
            Тип данных: [suds.sax.text.Text] (suds.sax.text.Text - наследник str).
        
        """
        try:
            return self.client.service.GetIncomingMessages(self._session_id, max_date_utc.isoformat(),
                                                          min_date_utc.isoformat())
        except WebFault as e:
            raise  DevinoSmsClientException(e.fault.faultstring)
            
    def GetBalance(self):
        """
        Запрос на получение состояния счета.
        
        Возвращаемое значение: Состояние счета. Тип данных: float.
        
        """
        try:
            return self.client.service.GetBalance(self._session_id)  
        except WebFault as e:
            raise  DevinoSmsClientException(e.fault.faultstring)
          
    def GetSessionID(self, user_login, password):
        """
        Запрос на получение идентификатора сессии.
        
        user_login: Логин пользователя. Тип данных: str (или unicode)
        password: Пароль пользователя. Тип данных: str (или unicode)
        Возвращаемое значение: Идентификатор сессии. 
            Тип данных: suds.sax.text.Text (suds.sax.text.Text - наследник str).
        
        """
        try:
            return self.client.service.GetSessionID(user_login, password)
        except WebFault as e:
            raise  DevinoSmsClientException(e.fault.faultstring)
        
