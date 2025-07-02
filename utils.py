from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init()
current_state = None

def log_with_time(message: str, color: str = Fore.WHITE):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    if current_state:
        print(f"{Fore.CYAN}[{timestamp}][{current_state}]{Style.RESET_ALL} {color}{message}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL} {color}{message}{Style.RESET_ALL}")

def log_error(message: str):
    log_with_time(message, Fore.RED)

def log_warning(message: str):
    log_with_time(message, Fore.YELLOW)

def log_success(message: str):
    log_with_time(message, Fore.GREEN)

def log_info(message: str):
    log_with_time(message, Fore.CYAN)

def log_state(message: str):
    log_with_time(message, Fore.BLUE)

def log(message: str):
    log_with_time(message, Fore.WHITE)

def set_current_state(state: str):
    global current_state
    current_state = state
