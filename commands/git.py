import re
import subprocess
from colorama import Fore
from enumerations import MergeOutcome

__current_branch__ = None


def __run(command, *args):
    return subprocess.run(command.split() + list(args), capture_output=True, text=True)


def fetch():
    return __run("git fetch")


def remote_branches():
    return [str(line).strip() for line in __run('git branch -r').stdout.splitlines()]


def current_branch(refresh=False):
    global __current_branch__
    if refresh or not __current_branch__:
        __current_branch__ = __run('git rev-parse --abbrev-ref HEAD').stdout.strip()
    return __current_branch__


def new_branch(branch):
    global __current_branch__
    __current_branch__ = branch
    return __run('git checkout -b', branch)


def checkout(branch):
    global __current_branch__
    __current_branch__ = branch
    return __run('git checkout', branch)


def delete_local_branch(branch):
    return __run('git branch -D', branch)


def find_conflicting_file(branch):
    global __current_branch__
    __current_branch__ = branch
    return __run('git diff --name-only --diff-filter=U').stdout.splitlines()


def accept_from_current_branch(filename):
    __run("git reset HEAD", filename)
    __run("git checkout --", filename)


def accept_from_other_branch(branch_to_merge, filename):
    __run(f"git checkout {branch_to_merge} --", filename)


def diff(branch_to_compare, filename, short_stat=False, ignore_whitespaces=True):
    result = None
    if short_stat and ignore_whitespaces:
        result = __run("git diff --shortstat -w", branch_to_compare, filename)
    elif short_stat:
        result = __run("git diff --shortstat", branch_to_compare, filename)
    elif ignore_whitespaces:
        result = __run("git diff -w", branch_to_compare, filename)
    else:
        result = __run("git diff", branch_to_compare, filename)

    return " ".join(result.stdout.split())


def merge(branch, dry_run=True):
    print(f'{"dry run " if dry_run else ""}merge {Fore.LIGHTBLUE_EX}{branch}{Fore.RESET}')

    if dry_run:
        merge_result = __run('git merge --no-commit --no-ff', branch)
        __run('git merge --abort')
    else:
        merge_result = __run('git merge', branch)

    if merge_result.returncode == 0:
        if merge_result.stdout.strip() == 'Already up to date.':
            print(f'{Fore.LIGHTGREEN_EX}Already up to date{Fore.RESET}')
            return MergeOutcome.NO_OP
        else:
            print(f'{Fore.LIGHTGREEN_EX}OK{Fore.RESET}')
            return MergeOutcome.OK

    elif merge_result.returncode == 1:
        conflict_pattern = re.compile('''Merge conflict in ([^$]+)''')

        pom_pattern = re.compile('''(?:/|^)pom.xml$''')
        xls_pattern = re.compile('''\.xls$''')
        test_pattern = re.compile('''src/test''')
        fshost_pattern = re.compile('''/FS.host''')

        pom_conflicts = 0
        xls_conflicts = 0
        test_conflicts = 0
        fshost_conflicts = 0

        found_real_conflicts = False

        if not dry_run:
            print(f'{Fore.LIGHTRED_EX}WARNING! MERGED WITH CONFLICTS!{Fore.RESET}')
        for out in merge_result.stdout.split('\n'):
            search = conflict_pattern.search(out)
            if search:
                if pom_pattern.search(search.group(1)):
                    pom_conflicts += 1
                elif xls_pattern.search(search.group(1)):
                    xls_conflicts += 1
                elif test_pattern.search(search.group(1)):
                    test_conflicts += 1
                elif fshost_pattern.search(search.group(1)):
                    fshost_conflicts += 1
                else:
                    print(f'{Fore.LIGHTRED_EX}{search.group(1)}{Fore.RESET}')
                    found_real_conflicts = True

        if pom_conflicts:
            print(f'{Fore.LIGHTYELLOW_EX}{pom_conflicts} pom.xml conflict(s){Fore.RESET}')
        if xls_conflicts:
            print(f'{Fore.LIGHTYELLOW_EX}{xls_conflicts} xls conflict(s){Fore.RESET}')
        if test_conflicts:
            print(f'{Fore.LIGHTYELLOW_EX}{test_conflicts} test conflict(s){Fore.RESET}')
        if fshost_conflicts:
            print(f'{Fore.LIGHTYELLOW_EX}{fshost_conflicts} FS.host conflict(s){Fore.RESET}')

        if found_real_conflicts:
            return MergeOutcome.CONFLICT
        else:
            return MergeOutcome.SOFT_CONFLICT

    else:
        print(f'unexpected return code: {merge_result.returncode}')
        print(merge_result)
        return MergeOutcome.UNKNOWN


def file(branch, filename):
    return __run(f'git show {branch}:{filename}').stdout.strip()
