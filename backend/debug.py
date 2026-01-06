def msg(text):
    print(text)

COLOR_DEBUG = "\033[37m"
COLOR_INFO = "\033[96m"
COLOR_WARN = "\033[33m"
COLOR_ERR  = "\033[31m"
COLOR_RESET = "\033[0m"

def debug(text):
    print(f"{COLOR_INFO} .. {COLOR_RESET}{text}")
def info(text):
    print(f"{COLOR_INFO} :: {COLOR_RESET}{text}")
def warn(text):
    print(f"{COLOR_WARN} ?? {COLOR_RESET}{text}")
def err(text):
    print(f"{COLOR_ERR} XX {COLOR_RESET}{text}")