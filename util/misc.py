import init
import os
from util import  fileIO
import csv


def getAnalyzedPRs(train_repo):
    tokens = []
    for rootDir, dirs, filenames in os.walk(init.local_pr_data_dir + train_repo):
        for subdir in dirs:
            for sub_rootDir, sub_dirs, sub_filenames in os.walk(rootDir + "/" + subdir):
                if os.path.exists(sub_rootDir + '/title_bigrams_tokens_stemmed.tsv'):
                    with open(sub_rootDir + '/title_bigrams_tokens_stemmed.tsv') as tsv:
                        tokens_perPR = [line.strip().split('\t') for line in tsv]
                        for t in tokens_perPR:
                            tokens.extend(t)
    return tokens


def intersection(lst1, lst2):
    # Use of hybrid method
    temp = set(lst2)
    lst3 = [value for value in lst1 if value in temp]
    return lst3


if __name__ == "__main__":

    getAnalyzedPRs('joomla/joomla-cms')