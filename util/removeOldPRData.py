import os
import sys
import init
import json
import util.timeUtil
from datetime import datetime, timedelta

import shutil

import init


def remove_oldPR_rawdata():
    pulllist_file = "pull_list.json"
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    oldPR_list = []
    oldpr = 0

    for subdir, dirs, files in os.walk(init.local_pr_data_dir):
        for subdir_tmp in dirs:
            print(subdir_tmp)
            for subdir_1, dirs_1, files_1 in os.walk(os.path.join(subdir, subdir_tmp)):
                for repo in dirs_1:
                    print(subdir_tmp + "/" + repo)
                    if (subdir_tmp + "/" + repo) in init.trainModelRepoList:
                        print("repo is usedful for training model, skip " + subdir_tmp + "/" + repo)
                        continue
                    for subdir_2, dirs_2, files_2 in os.walk(subdir_1 + "/" + repo):
                        if len(dirs_2) == 0:
                            break
                        # get old pr list
                        if os.path.exists(subdir_2 + "/" + pulllist_file):
                            with open(subdir_2 + "/" + pulllist_file, 'r') as f:
                                datastore = json.load(f)
                                for pr in datastore:
                                    if (util.timeUtil.days_between(now, pr['created_at']) > 366):
                                        oldpr = pr['number']
                                        break
                                for pr in datastore:
                                    prid = pr['number']
                                    filepath = subdir_2 + "/" + str(prid)
                                    if (prid <= oldpr and os.path.exists(filepath)):
                                        # oldPR_list.append(prid)
                                        # delete old pr dir
                                        shutil.rmtree(filepath)
                                        print("delete " + filepath)
                                break


import os
import fnmatch


def removeFile_byPattern_allrepo():
    # Get a list of all the file paths that ends with .txt from in specified directory
    for rootDir, subdirs, filenames in os.walk(init.local_pr_data_dir):
        # Find the files that matches the given patterm
        for sd in subdirs:
            for srootDir, ssubdirs, sfilenames in os.walk(rootDir + sd):
                for sssubdir in ssubdirs:
                    for root, sub, subfile in os.walk(srootDir + '/' + sssubdir):
                        for subb in sub:
                            if (os.path.exists(root +'/'+subb+ '/parse_diff.json')):
                                print(root +'/'+subb+ '/parse_diff.json')
                                try:
                                    os.remove(root + '/' + subb + '/parse_diff.json')
                                    break
                                except OSError:
                                    print("Error while deleting file")


def removeFile_byPattern():
    # Get a list of all the file paths that ends with .txt from in specified directory

    # Get a list of all files in directory
    for train_repo in init.trainModelRepoList:
        for rootDir, subdirs, filenames in os.walk(init.local_pr_data_dir + train_repo):
            # Find the files that matches the given patterm
            for sd in subdirs:
                for srootDir, ssubdirs, sfilenames in os.walk(init.local_pr_data_dir + train_repo + "/" + sd):
                    for filename in fnmatch.filter(sfilenames, 'toobig.txt'):
                        with open (init.local_pr_data_dir + train_repo + "/" + sd + '/' + filename) as myfile:
                            if 'loc' in myfile.read():
                                print(init.local_pr_data_dir + train_repo + "/" + sd + '/' + filename)
                                try:
                                    os.remove(os.path.join(init.local_pr_data_dir + train_repo + "/" + sd + '/', filename))
                                    break
                                except OSError:
                                    print("Error while deleting file")


if __name__ == "__main__":
    removeFile_byPattern_allrepo()
    # removeFile_byPattern()
