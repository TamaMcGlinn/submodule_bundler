#!/usr/bin/env python3
""" Create bundles for submodules """

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
parser.add_argument('commit_range', metavar='[baseline]..[target]', type=str, default='..HEAD', nargs='?',
                    help='commit range of top-level repository to bundle; defaults to everything')

args = parser.parse_args()

class IllegalArgumentError(ValueError):
    pass

try:
    [baseline, target] = args.commit_range.split('..')
except ValueError:
    raise IllegalArgumentError(f"Invalid commit range: '{args.commit_range}': "
                               + "Expected [baseline]..[target]. Baseline and target are optional "
                               + "but the dots are necessary to distinguish between the two.") from None

full_histories = False
from_str = f'from {baseline} '
if baseline == '':
    print("No baseline (all bundles will be complete history bundles)")
    full_histories = True
    from_str = "from scratch "

if target == '':
    target = 'HEAD'

print('Making bundles to update ' + from_str + f'to {target}')

updates_required = {}
new_submodules = {}
bundles = []

for submodule in submodule_commits.submodule_commits('.', target):
    new_submodules[submodule['subdir']] = submodule['commit']

root_dir = os.getcwd()
tar_file_name = os.path.basename(args.filename).split('.')[0]
temp_dir = f'temp_dir_for_{tar_file_name}_bundles'  # note this won't work if that dir already has contents

def create_bundle(submodule_dir, new_commit_sha, baseline_descriptor=''):
    bundle_path_in_temp = f'{submodule_dir}.bundle'
    bundle_path = f'{temp_dir}/{bundle_path_in_temp}'
    if submodule_dir == '.':
        route_to_root = './'
    else:
        route_to_root = (submodule_dir.count('/') + 1) * '../'
    os.makedirs(os.path.dirname(bundle_path), exist_ok=True)
    os.chdir(submodule_dir)
    rev_parse_output = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    current_branch = rev_parse_output.decode("utf-8").strip('\n')
    need_to_create_branch = (current_branch == 'HEAD')
    if need_to_create_branch:
        # Create branch as workaround for git bundle not working on sha's directly
        # see also stackoverflow.com/questions/42542005/error-trying-to-create-a-git-bundle-ranged-between-2-commits
        random_id = ''.join(random.choices(string.ascii_lowercase, k=22))  # random to avoid overwriting your branches
        current_branch = f'tmp_branch_{random_id}'
        subprocess.run(['git', 'branch', '-f', current_branch, new_commit_sha])
    subprocess.run(['git', 'bundle', 'create', route_to_root + bundle_path, f'{baseline_descriptor}{current_branch}'])
    if need_to_create_branch:
        subprocess.run(['git', 'branch', '-D', current_branch, '--quiet'])  # if we made it, we clean it up
    bundles.append(bundle_path_in_temp)
    os.chdir(root_dir)

if not full_histories:
    for existing_commit in submodule_commits.submodule_commits('.', baseline):
        baseline_commit = existing_commit['commit']
        submodule_dir = existing_commit['subdir']
        new_commit_sha = new_submodules.pop(submodule_dir, None)
        if new_commit_sha is None:
            # the submodule was removed, don't need to make any bundle
            continue
        if new_commit_sha == baseline_commit:
            # no change, no bundle
            continue
        print(f"Need to update {submodule_dir} from {baseline_commit} to {new_commit_sha}")
        create_bundle(submodule_dir, new_commit_sha, f'{baseline_commit}..')

for submodule_dir, commit_sha in new_submodules.items():
    print(f"New submodule {submodule_dir}")
    bundle_name = f'{submodule_dir}.bundle'
    create_bundle(submodule_dir, commit_sha)

# the bundle of the top-level repository itself is oddly called '..bundle'
# it is impossible to have a submodule that clashes with this
# because you cannot name a directory '.'
create_bundle('.', target)

print("Packing bundles into tarfile:")
with tarfile.open(args.filename, mode="w:") as tar:  # no compression; git already does that
    os.chdir(temp_dir)
    for bundle in bundles:
        print(bundle)
        tar.add(bundle)
    os.chdir(root_dir)

print("Removing temp directory")
shutil.rmtree(f'{root_dir}/{temp_dir}')

