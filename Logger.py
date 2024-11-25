import os
import json
from datetime import datetime

class Logger:
    _instance = None
    _log_file = None 

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
   

    @classmethod
    def _initialize_logger(cls):
        # Generate a unique log file name with a timestamp
        timestamp = datetime.now().strftime('%d.%m.%Y_%H-%M-%S')
        cls._log_file = f"logs/log_{timestamp}.txt"
        
        # Ensure the log directory exists (optional)
        log_dir = os.path.dirname(cls._log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create the log file
        with open(cls._log_file, 'w') as f:
            pass  # Create an empty log file

        print(f"Logger initialized. Log file: {cls._log_file}")


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
