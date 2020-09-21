#!/usr/bin/env python3
""" Create bundles for submodules """

import os
import sys
import subprocess

existing_commits = filter(None, sys.stdin.read().split("\n"))
new_commits = filter(None, subprocess.check_output(['git', 'submodule', 'status']).decode("utf-8").split("\n"))

updates_required = {}
new_submodules = {}

for new_commit in new_commits:
    split = new_commit.split(' ')
    commit_sha = split[1]
    submodule_dir = split[2]
    new_submodules[submodule_dir] = commit_sha

root_dir = os.getcwd()

for existing_commit in existing_commits:
    split = existing_commit.split(' ')
    commit_sha = split[1]
    submodule_dir = split[2]
    new_commit_sha = new_submodules.pop(submodule_dir, None)
    if new_commit_sha is None:
        # the submodule was removed, don't need to make any bundle
        continue
    if new_commit_sha == commit_sha:
        # no change, no bundle
        continue
    print(f"Need to update {submodule_dir} from {commit_sha} to {new_commit_sha}")
    bundle_name = submodule_dir.replace('/', '_')
    os.chdir(submodule_dir)
    dirs_up = submodule_dir.count('/')
    bundle_path = "../" * (dirs_up + 2) + bundle_name + '.bundle'
    # A workaround for git bundle not working on sha's directly
    # see also stackoverflow.com/questions/42542005/error-trying-to-create-a-git-bundle-ranged-between-2-commits
    subprocess.run(['git', 'branch', f'branch_{commit_sha}', commit_sha])
    subprocess.run(['git', 'branch', f'branch_{new_commit_sha}', new_commit_sha])
    subprocess.run(['git', 'bundle', 'create', bundle_path, f'branch_{commit_sha}..branch_{new_commit_sha}'])
    os.chdir(root_dir)

for submodule_dir, commit_sha in new_submodules.items():
    print(f"New submodule {submodule_dir}")
    bundle_name = submodule_dir.replace('/', '_')
    os.chdir(submodule_dir)
    dirs_up = submodule_dir.count('/')
    bundle_path = "../" * (dirs_up + 2) + bundle_name + '.bundle'
    # A workaround for git bundle not working on sha's directly
    # see also stackoverflow.com/questions/42542005/error-trying-to-create-a-git-bundle-ranged-between-2-commits
    subprocess.run(['git', 'branch', f'branch_{commit_sha}', commit_sha])
    subprocess.run(['git', 'bundle', 'create', bundle_path, f'branch_{commit_sha}'])
    os.chdir(root_dir)
