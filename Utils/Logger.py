import os
import json
from datetime import datetime

class Logger:
    _instance = None
    _log_file_location = None 

    def __new__(cls):
        """ Default Logfile location: logs/log_ """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
   

    @classmethod
    def _initialize_logger(cls, log_file_location: str = None):
        
        # Generate a unique log file name with a timestamp
        timestamp = datetime.now().strftime('%d.%m.%Y_%H-%M-%S')
        
        if log_file_location:
            cls._log_file_location = f"{log_file_location}{timestamp}.log"
        else:
            cls._log_file_location = f"logs/log_{timestamp}.log"
        
        # Ensure the log directory exists (optional)
        log_dir = os.path.dirname(cls._log_file_location)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # # Create the log file
        # with open(cls._log_file_location, 'w') as f:
        #     pass  # Create an empty log file

        print(f"Logger initialized. Log file: {cls._log_file_location}")    

    @staticmethod
    def _get_timestamp():
        """ %d : Day of the month (zero-padded)
            %m : Month (zero-padded)
            %Y : Year (4 digits)
            %H : Hour (24-hour format, zero-padded)
            %M : Minutes (zero-padded)
            %S : Seconds (zero-padded)
            %f : Microseconds (6 digits, zero-padded)
            """
        return datetime.now().strftime('%d.%m.%Y %H:%M:%S.%f')[:-3]

    @classmethod
    def Set_log_file_location(cls, new_log_file_location: str):
        """Sets a new log file location."""        
        cls._initialize_logger(new_log_file_location)                
        print(f"Logger storage location changed. New log file: {cls._log_file_location}")

    @staticmethod
    def LogMessage(message: str, instance:object = None):
        # Get the current timestamp
        class_name = instance.__class__.__name__ if instance else "Default"
        timestamp = Logger._get_timestamp()
        log_message = {"time": timestamp, "Module": class_name, "Message": message}
        
        # Print the message to console
        print(f"{timestamp} Module: {class_name} Message: {message}")
        
        # Write the message to the log file in JSON format
        Logger._write_Logmessage_to_file(log_message)
        

    @staticmethod
    def LogException(exception: Exception, message: str = "processing failed", instance:object = None):
        # Get the current timestamp
        class_name = instance.__class__.__name__ if instance else "Default"
        timestamp = Logger._get_timestamp()
        try:
            exception_message = str(exception).encode('latin1').decode('unicode_escape')                                
            utf8_message = exception_message.encode('utf-8').decode('utf-8')            
        except Exception as exc:            
            exception_message = str(exception)
            Logger._write_Logmessage_to_file({"time": timestamp, "Module": "Logger", "Error": f"Encoding error of exception: >>{exception_message}<< failed", "Exception": str(exc)})
        
        log_message = {"time": timestamp, "Module": class_name, "Error": message, "Exception": utf8_message}
        
        # Print the error to console
        print(f"{timestamp} Module: {class_name} Error: {message}. Exception: {exception_message}")
        
        # Write the error message to the log file in JSON format
        Logger._write_Logmessage_to_file(log_message)
        

    @staticmethod
    def _write_Logmessage_to_file(log_message):
        with open(Logger._log_file_location, 'a', encoding="utf-8") as f:
            f.write(json.dumps(log_message, ensure_ascii=False) + ',\n')