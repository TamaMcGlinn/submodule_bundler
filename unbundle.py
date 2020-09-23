#!/usr/bin/env python3
""" Extract bundles for submodules """

import os
import argparse
import shutil
import tarfile
import pullbundle
import submodule_commits
import subprocess

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

root_dir = os.getcwd()

def is_git_repository(dir):
    """ Return true iff dir exists and is a git repository (by checking git rev-parse --show-toplevel) """
    if not os.path.exists(dir):
        return False
    previous_dir = os.getcwd()
    os.chdir(dir)
    rev_parse_toplevel = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'])
    git_dir = rev_parse_toplevel.decode("utf-8").strip('\n')
    current_dir = os.getcwd().replace('\\', '/')
    os.chdir(previous_dir)
    return current_dir == git_dir

pullbundle.pullbundle(f'{temp_dir}/..bundle', True)
for submodule in submodule_commits.submodule_commits():
    subdir = submodule["subdir"]
    commit = submodule["commit"]
    print(f'{subdir} -> {commit}')
    bundle_file_from_root = f'{temp_dir}/{subdir}.bundle'
    if not os.path.isfile(bundle_file_from_root):
        print(f'Skipping submodule {subdir} because there is no bundle')
    else:
        if not is_git_repository(subdir):
            # clone first if the subdir doesn't exist or isn't a git repository yet
            subprocess.run(['git', 'clone', bundle_file_from_root, subdir])
        route_to_root = (subdir.count('/') + 1) * '../'
        bundle_file = f'{route_to_root}{bundle_file_from_root}'
        os.chdir(subdir)
        pullbundle.pullbundle(bundle_file)
    os.chdir(root_dir)

print("Removing temp directory")
shutil.rmtree(temp_dir)

subprocess.run(['git', 'submodule', 'update', '--recursive'])

