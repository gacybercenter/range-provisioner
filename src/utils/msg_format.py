from colorama import Fore

def error_msg(error):
    print(Fore.RED + "[ERROR]   " + Fore.RESET + error)


def info_msg(text, debug=False):
    if debug:
        if '\n' in text:
            # If text contains multiple lines, split it and print each line separately
            text_lines = text.split('\n')
            print(Fore.BLUE + "[INFO]    " + Fore.RESET)
            for line in text_lines:
                print(line)
        else:
            # If text is a single line, print it as is
            print(Fore.BLUE + "[INFO]    " + Fore.RESET + text)


def success_msg(text):
    if '\n' in text:
        # If text contains multiple lines, split it and print each line separately
        text_lines = text.split('\n')
        print(Fore.GREEN + "[SUCCESS] " + Fore.RESET)
        for line in text_lines:
            print(line)
    else:
        # If text is a single line, print it as is
        print(Fore.GREEN + "[SUCCESS] " + Fore.RESET + text)

def general_msg(text):
    if '\n' in text:
        # If text contains multiple lines, split it and print each line separately
        text_lines = text.split('\n')
        print(Fore.YELLOW + "[INFO]    " + Fore.RESET)
        for line in text_lines:
            print(line)
    else:
        # If text is a single line, print it as is
        print(Fore.YELLOW + "[INFO]    " + Fore.RESET + text)
