#!/usr/bin/env python3
""" Extract bundles for submodules """

import os
import argparse
import subprocess
import tarfile
import submodule_commits
import string
import random
import shutil

parser = argparse.ArgumentParser(description='Create bundles for submodules (recursively), \
                                              to facilitate sneakernet connections. On the online computer, \
                                              a bundle is made for each repository, and then packed into a .tar file. \
                                              On the offline computer, use unbundle.py on the tarfile to unzip and \
                                              pull from the corresponding bundle for each repository.')

parser.add_argument('filename', metavar='filename', type=str, help='file to create e.g. ../my_bundles.tar')

args = parser.parse_args()

tar_file_name = os.path.basename(args.filename).split('.')[0]
temp_dir = f'temp_dir_for_{tar_file_name}_extraction'

with tarfile.open(args.filename, 'r:') as tar:
    tar.extractall(temp_dir)

subprocess.run(['git', 'bundle', 'unbundle', f'{temp_dir}/..bundle'])
