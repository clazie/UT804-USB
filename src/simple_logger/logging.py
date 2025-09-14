# Color constants
OKGRAY = '\033[0;90m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'


class Logging:

  # Logging constants
  DEBUG = False
  INFO = True

  def __init__(self):
    pass

  # Logging functions
  def Log(self, msg: str):
    if (self.DEBUG or self.INFO):
      print(f'{OKGREEN}{msg}{ENDC}')

  def Info(self, msg: str):
    if (self.INFO):
      print(f'{OKCYAN}{msg}{ENDC}')

  def Debug(self, msg: str):
    if (self.DEBUG):
      print(f'{OKGRAY}{msg}{ENDC}')

  def Warn(self, msg: str):
    print(f'{WARNING}{msg}{ENDC}')

  def Error(self, msg: str):
    print(f'{FAIL}{msg}{ENDC}')


Log: Logging = Logging()
