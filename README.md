# Bundle file for offline distribution

The best way to update a repository on a computer that has no internet is to transfer bundle files; a complete history bundle file contains all commits in a repostiory, while a partial commit has a baseline commit that is assumed to already exist on the offline computer: these contain only the diffs necessary to update from that commit. Bundle files can contain multiple branches and can contain any or all tags that reference commits in the bundle.

For example, on the online computer, you could run:

```
git bundle create ../my_update.bundle master..develop
```

Which will generate a bundle file my_update.bundle next to the repository with the commits on develop but not on master. This bundle file can be pulled from on the offline computer. Let's assume you put a usb stick in with drive letter G (on a windows computer; similar instructions work for linux, and bundle files can be transferred between any OS-combination), and you are already on the develop branch which the bundle contains:

```
git pull G:/bundles/my_update.bundle
```

Note: I will continue to use the term 'online computer' to mean the host of the repository that has the newer commits to be transferred to the 'offline computer', even though internet is not required for any of this.

# Problem

But if you have submodules, you have problems. Each one should have its own bundle file to update it, and doing this manually could be a lot of work, even though the specification given above: 'master..develop' actually also says which submodules would need updates and from which commit to which commit. The scripts in this repository solve that problem.

# Usage

Given a repository with submodules, run `bundle.py ../my_update.tar old_commit..new_commit`, transfer the tar file to the offline computer and run `unbundle.py my_update.tar`. Note the tar file is not compressed because each of the bundle files are already compressed by git. TODO: check the assumption that adding gzip compression wouldn't decrease the size.

# TODO add integration tests

- With a project that includes alire as a submodule at commit 3f0d7fd6cbb066f5d2660b6e0a6bf327108650c7, updating it to e4a2ef34c33ae864f760745e06c0143e40fd23fc is interesting; the partial bundles are 3MB while full bundle files would be 9MB, and during the update at least deps/ansi is a new submodule.
- What if, in one of the submodules, we have diverged? (this works, but good to have a test)
- What if, in the main repository, we have added a submodule in the same place? We would need to deinitialise and remove for this case. (untested, probably doesn't work)

