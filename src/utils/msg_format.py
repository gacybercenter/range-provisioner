from colorama import Fore

def error_msg(error):
    if '\n' in error:
        # If error contains multiple lines, split it and print each line separately
        error_lines = error.split('\n')
        print(Fore.RED + "ERROR: " + Fore.RESET)
        for line in error_lines:
            print(line)
    else:
        # If error is a single line, print it as is
        print(Fore.RED + "ERROR: " + Fore.RESET + error)


def info_msg(text):
    if '\n' in text:
        # If text contains multiple lines, split it and print each line separately
        text_lines = text.split('\n')
        print(Fore.BLUE + "INFO: " + Fore.RESET)
        for line in text_lines:
            print(line)
    else:
        # If text is a single line, print it as is
        print(Fore.BLUE + "INFO: " + Fore.RESET + text)


def success_msg(text):
    if '\n' in text:
        # If text contains multiple lines, split it and print each line separately
        text_lines = text.split('\n')
        print(Fore.GREEN + "SUCCESS: " + Fore.RESET)
        for line in text_lines:
            print(line)
    else:
        # If text is a single line, print it as is
        print(Fore.GREEN + "SUCCESS: " + Fore.RESET + text)