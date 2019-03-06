#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

import readline
def ask(prompt:str, guess:str="", insist=True) -> str:
    """ ask the user for some information, maybe with a guess to accept """
    readline.set_startup_hook(lambda: readline.insert_text(guess))
    try:
        retval = ''
        while retval == '':
            retval = input(prompt)
            if not insist:
                break
    finally:
        readline.set_startup_hook()
    return retval

from typing import List
def select(prompt:str, options:List, *additional:str) -> str:
    """ ask the user to choose an option from a list (by number), or
        one of the provided additional options
    """ 
    print(prompt)
    if len(options) == 0:
        print("(nothing available)")
    logging.debug("selecting from: " + str(options))
    for i in range(len(options)):
        logging.debug("option {0} is {1}".format(str(i), str(options[i])))
        print("{0:>3d}: {1}".format(i+1, str(options[i])))
    print("Selection: ")
    while True:
        choice = input()
        if choice in additional:
            return choice
        try:
            ichoice = int(choice)
        except ValueError:
            # user put something invalid, trigger a retry
            ichoice = 0
        # offset back to 0:
        ichoice -= 1
        if ichoice >= 0 and ichoice < len(options):
            #return ichoice
            return options[ichoice]
        choices = ', '.join([c for c in additional])
        print("Not a valid selection, please select a number from the list above or one of: " + choices)

def multi_select(prompt:str, options:List, *additional:str) -> List[str]:
    """ ask the user to choose options by number, and accept multiple options 
        as a space-separated list
    """
    print(prompt)
    for i in range(len(options)):
        print("{0:>3d}: {1}".format(i+1, str(options[i])))
    print("To select multiple items, please use spaces to separate them")
    print("Selections: ")
    while True:
        result = []
        choices = input().split()
        for choice in choices: 
            if choice in additional:
                result.append(choice)
                continue
            ichoice = int(choice)
            if ichoice >= 1 and ichoice <= len(options)+1:
                #result.append(ichoice-1)
                result.append(options[ichoice-1])
                continue
            print("{0} is not a valid selection, please try again".format(choice))
            break
        else:
            return result # all were valid

def truefalse(prompt, default=False):
    readline.set_startup_hook(lambda: readline.insert_text(str(default)))
    guess = 'Y' if default else 'N'
    try:
        while True:
            response = input(prompt)
            if response.lower() in ('yes', 'y', 'true', 't'):
                retval = True
                break
            elif response.lower() in ('no', 'n', 'false', 'f'):
                retval = False
                break
            else:
                prompt = "invalid response, please enter Y or N"
        return retval
    finally:
        readline.set_startup_hook()

