#!/usr/bin/env python3
""" Pull from bundles """

import argparse
import subprocess
import re
import os

ref_head_regex = 'refs/heads/(.*)'
head_commit = None

class UnableToFastForwardError(RuntimeError):
    pass

def iterate_branches(bundle_refs):
    """ Given lines of output from 'git bundle unbundle' this writes the HEAD commit to the head_commit global
        and yields each branch, commit pair """
    global head_commit
    for bundle_ref in bundle_refs:
        ref_split = bundle_ref.split()
        commit = ref_split[0]
        ref_name = ref_split[1]
        if ref_name == 'HEAD':
            head_commit = commit
        else:
            match = re.search(ref_head_regex, ref_name)
            if match:
                branch_name = match.group(1)
                yield (branch_name, commit)

def update_branch(branch, commit, check_divergence=False):
    """ Update branch to commit if possible by fast-forward """
    rev_parse_branch_output = subprocess.check_output(['git', 'rev-parse', branch])
    old_commit = rev_parse_branch_output.decode("utf-8").strip('\n')
    if old_commit == commit:
        print(f'Skipping {branch} which is up-to-date at {commit}')
    else:
        rev_parse_current_output = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        current_branch = rev_parse_current_output.decode("utf-8").strip('\n')

        returncode = subprocess.call(['git', 'merge-base', '--is-ancestor', branch, commit])
        branch_is_behind_commit = returncode == 0
        if branch_is_behind_commit:
            print(f'Fast-forwarding {branch} from {old_commit} to {commit}')
            if current_branch == branch:
                subprocess.call(['git', 'reset', '--hard', '-q', commit])
            else:
                subprocess.call(['git', 'branch', '-Dq', branch])
                subprocess.run(['git', 'branch', '-q', branch, commit])
        else:
            returncode = subprocess.call(['git', 'merge-base', '--is-ancestor', commit, branch])
            branch_is_ahead_of_commit = returncode == 0
            if branch_is_ahead_of_commit:
                print(f'Skipping {branch} which is at {old_commit}, ahead of bundle version {commit}')
                if current_branch == branch and check_divergence:
                    raise UnableToFastForwardError("Unable to update branch: already ahead of bundle") from None
            else:
                print(f'Error: {branch} already exists, at {old_commit} which diverges from '
                      + f'bundle version at {commit}')
                print('You could switch to the bundle version as follows, but you might lose work.')
                print(f'git checkout -B {branch} {commit}')
                if current_branch == branch and check_divergence:
                    raise UnableToFastForwardError("Unable to update branch: diverged from bundle") from None

def pullbundle(bundle_file, check_divergence=False):
    """ Main function; update all branches from given bundle file """
    subprocess.run(['git', 'fetch', bundle_file, '+refs/tags/*:refs/tags/*'], stderr=subprocess.DEVNULL)
    unbundle_output = subprocess.check_output(['git', 'bundle', 'unbundle', bundle_file])
    bundle_refs = filter(None, unbundle_output.decode("utf-8").split('\n'))

    for branch, commit in iterate_branches(bundle_refs):
        returncode = subprocess.call(['git', 'show-ref', '-q', '--heads', branch])
        branch_exists = returncode == 0
        if branch_exists:
            update_branch(branch, commit, check_divergence)
        else:
            print(f'Created {branch} pointing at {commit}')
            subprocess.run(['git', 'branch', branch, commit])

    if head_commit is not None:
        # checkout as detached head without branch
        # note this might not happen; if the bundle updates a bunch of branches
        # then whichever one we were already on is updated already and we don't need to do anything here
        subprocess.run(['git', 'checkout', head_commit])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update all branches and tags contained in a bundle file')
    parser.add_argument('filename', metavar='filename', help='git bundle file to pull e.g. ../foo.bundle')
    parser.add_argument('-c', '--check_divergence', help="return an errorcode if the current branch was not updated "
                        + "because of already being ahead or having diverged from the bundle version of that branch",
                        action='store_true')
    args = parser.parse_args()
    pullbundle(args.filename, args.check_divergence)

