import os
import json
from datetime import datetime

class Logger:
    _instance = None
    _log_file = 'logs/log.txt'  # Default log file name

    def __new__(cls, log_file='logs/log.txt'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._log_file = log_file
            cls._ensure_log_file_exists(cls._log_file)
        return cls._instance

    @classmethod
    def _ensure_log_file_exists(cls, log_file):
        # Create an empty log file if it does not exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                pass

    @staticmethod
    def _get_timestamp():
        return datetime.now().strftime('%d.%m.%Y %H:%M')

    @staticmethod
    def LogMessage(message: str):
        # Get the current timestamp
        timestamp = Logger._get_timestamp()
        log_message = {"time": timestamp, "Message": message}
        
        # Print the message to console
        print(f"{timestamp} Message: {message}")
        
        # Write the message to the log file in JSON format
        with open(Logger._log_file, 'a') as f:
            f.write(json.dumps(log_message) + ',\n')

    @staticmethod
    def LogException(exception: Exception, message: str = "processing failed"):
        # Get the current timestamp
        timestamp = Logger._get_timestamp()
        exception_message = str(exception)
        log_message = {"time": timestamp, "Message": message, "Exception": exception_message}
        
        # Print the error to console
        print(f"{timestamp} Error: {message}. Exception: {exception_message}")
        
        # Write the error message to the log file in JSON format
        with open(Logger._log_file, 'a') as f:
            f.write(json.dumps(log_message) + ',\n')
