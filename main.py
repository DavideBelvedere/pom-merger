import os
import re
from shutil import copymode, move
from tempfile import mkstemp
from tqdm import tqdm
import configuration as cfg
from commands import git


def find_version(branch):
    pattern = re.compile('<version>(.+)</version>')
    return pattern.search(git.file(branch, 'pom.xml')).group(1)


def change_version(file_path, version_to_replace, version_to_keep):
    # Create temp file
    fh, abs_path = mkstemp()
    with os.fdopen(fh, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(version_to_replace, version_to_keep))
    # Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    # Remove original file
    os.remove(file_path)
    # Move new file
    move(abs_path, file_path)


os.chdir(cfg.project_path)

git.fetch()
original_branch = git.current_branch()
branch_to_merge = cfg.branch_to_merge

currVersion = find_version(original_branch)
versionToReplace = find_version(branch_to_merge)

branch_for_merge = "merge/" + original_branch
git.new_branch(branch_for_merge)
git.merge(branch_to_merge, dry_run=False)

conflictingFiles = git.find_conflicting_file(branch_to_merge)
pomList = list(filter(lambda name: "pom.xml" in name, conflictingFiles))
dsAndHostList = list(
    filter(lambda name: "phoenix.datasource" in name or "postgres.datasource" in name or "FS.HOST" in name,
           conflictingFiles))
excelList = list(filter(lambda name: ".xls" in name, conflictingFiles))

onlyVersionIsChanged = '1 file changed, 4 insertions(+)'
for pom in tqdm(pomList, desc="Merging Pom"):
    diffFromOrigin = git.diff(original_branch, pom, short_stat=True)
    diffFromBranchToMerge = git.diff(branch_to_merge, pom, short_stat=True)
    if diffFromOrigin == onlyVersionIsChanged:
        git.accept_from_current_branch(pom)
    elif diffFromBranchToMerge == onlyVersionIsChanged:
        git.accept_from_other_branch(branch_to_merge, pom)
        change_version(pom, versionToReplace, currVersion)
        git.add(pom)
print("Pom merge ended")

for file in dsAndHostList:
    git.accept_from_current_branch(file)

for excel in excelList:
    git.accept_from_other_branch(branch_to_merge, excel)
    git.add(excel)
