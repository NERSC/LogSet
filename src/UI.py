#!/usr/bin/env python

import readline
def ask(prompt, guess=""):
    """ ask the user for some information, maybe with a guess to accept """
   readline.set_startup_hook(lambda: readline.insert_text(guess))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()
