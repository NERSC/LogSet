#!/usr/bin/env python3
""" display information about locally-cached log metadata """

def setup_args(subparsers):
    myparser = subparsers.add_parser('info', help=__doc__)
    # takes no extra arguments


import typing as t

def run(params: t.Dict[str,str]):
    print("running info command")
