#!/usr/bin/env python3
""" Pull from bundles """

import argparse
import subprocess

parser = argparse.ArgumentParser(description='update all branches and tags contained in a bundle file')

parser.add_argument('filename', metavar='filename', type=str, help='git bundle file to pull e.g. ../foo.bundle')

args = parser.parse_args()

subprocess.run(['git', 'bundle', 'unbundle', args.filename])
