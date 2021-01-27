# pom-merger
In configuration.py set project_path and branch_to_merge.
1) execute a fetch
2) create and checkout a branch with merge/branch_name
3) merge branch from configuration into current branch
4) resolve automatically conflicts on pom.
      if only version is changed, keep local file
      if version is changed and edit are done only on local file, keep local file
      if version is changed and edit are done only on file on the merged branch, keep merged branch file and set the version of local branch
5) keep phoenix.datasource and postgres.datasource from local version
6) use excel from remote branch
7) now you should merge the other conflicts, commit merge, and merge created branch into original one
