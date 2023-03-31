from colorama import Fore

def error_msg(error):
    if isinstance(error, list):
        # If error is a list, print each item separately
        print(Fore.RED + "[ERROR]   " + Fore.RESET)
        for item in error:
            print(item)
    elif isinstance(error, dict):
        # If error is a dict, print each item separately
        print(Fore.RED + "[ERROR]   " + Fore.RESET)
        for key, value in error.items():
            print(f"{key}: {value}")
    elif '\n' in error:
        # If error contains multiple lines, split it and print each line separately
        error_lines = error.split('\n')
        print(Fore.RED + "[ERROR]   " + Fore.RESET)
        for line in error_lines:
            print(line)
    else:
        # If error is a single line, print it as is
        print(Fore.RED + "[ERROR]   " + Fore.RESET + error)


def info_msg(text, debug=False):
    if debug:
        if isinstance(text, list):
            # If text is a list, print each item separately
            print(Fore.BLUE + "[INFO]    " + Fore.RESET)
            for item in text:
                print(item)
        elif isinstance(text, dict):
            # If text is a dict, print each item separately
            print(Fore.BLUE + "[INFO]    " + Fore.RESET)
            for key, value in text.items():
                print(f"{key}: {value}")
        elif '\n' in text:
            # If text contains multiple lines, split it and print each line separately
            text_lines = text.split('\n')
            print(Fore.BLUE + "[INFO]    " + Fore.RESET)
            for line in text_lines:
                print(line)
        else:
            # If text is a single line, print it as is
            print(Fore.BLUE + "[INFO]    " + Fore.RESET + text)


def success_msg(text):
    if isinstance(text, list):
        # If text is a list, print each item separately
        print(Fore.GREEN + "[SUCCESS] " + Fore.RESET)
        for item in text:
            print(item)
    elif isinstance(text, dict):
        # If text is a dict, print each item separately
        print(Fore.GREEN + "[SUCCESS] " + Fore.RESET)
        for key, value in text.items():
            print(f"{key}: {value}")
    elif '\n' in text:
        # If text contains multiple lines, split it and print each line separately
        text_lines = text.split('\n')
        print(Fore.GREEN + "[SUCCESS] " + Fore.RESET)
        for line in text_lines:
            print(line)
    else:
        # If text is a single line, print it as is
        print(Fore.GREEN + "[SUCCESS] " + Fore.RESET + text)

def general_msg(text):
    if isinstance(text, list):
        # If text is a list, print each item separately
        print(Fore.YELLOW + "[INFO]    " + Fore.RESET)
        for item in text:
            print(item)
    elif isinstance(text, dict):
        # If text is a dict, print each item separately
        print(Fore.YELLOW + "[INFO]    " + Fore.RESET)
        for key, value in text.items():
            print(f"{key}: {value}")
    elif '\n' in text:
        # If text contains multiple lines, split it and print each line separately
        text_lines = text.split('\n')
        print(Fore.YELLOW + "[INFO]    " + Fore.RESET)
        for line in text_lines:
            print(line)
    else:
        # If text is a single line, print it as is
        print(Fore.YELLOW + "[INFO]    " + Fore.RESET + text)
