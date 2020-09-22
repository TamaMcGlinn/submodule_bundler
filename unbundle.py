#!/usr/bin/env python3
""" Extract bundles for submodules """

import os
import argparse
import shutil
import tarfile
import pullbundle
import submodule_commits

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

pullbundle.pullbundle(f'{temp_dir}/..bundle', True)
for submodule in submodule_commits.submodule_commits():
    subdir = submodule["subdir"]
    commit = submodule["commit"]
    print(f'{subdir} -> {commit}')
    os.chdir(subdir)
    route_to_root = (subdir.count('/') + 1) * '../'
    bundle_file = f'{route_to_root}{temp_dir}/{subdir}.bundle'
    if not os.path.isfile(bundle_file):
        print(f'Skipping submodule {subdir} because there is no bundle')
    else:
        pullbundle.pullbundle(bundle_file)
    os.chdir(root_dir)

print("Removing temp directory")
shutil.rmtree(temp_dir)
