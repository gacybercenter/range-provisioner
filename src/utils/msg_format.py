from colorama import Fore


def error_msg(error):
    print(Fore.RED + "ERROR:  " + Fore.RESET + error)


def info_msg(text):
    print(Fore.BLUE + "INFO:  " + Fore.RESET + text)


def success_msg(text):
    print(Fore.GREEN + "SUCCESS:  " + Fore.RESET + text)