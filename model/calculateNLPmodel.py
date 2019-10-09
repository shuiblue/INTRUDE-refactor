'''
Featurization: calculating similarity scores for each feature for PR1 & PR2
'''

# TODO 1. title, descriptio:  tfidf -> similarity
#      2. code: tfidf -> (1) similarity of PR (2) overlapped files's code change similarity
#      3. changed files (1) similarity (2) overlapped files number (shurui: not sure)
#      4. location: (1) similarity of PR (2) overlapped files's location similarity
#      5, reference (1) version (2) issue/pr (3) commits
#      6. time interval


import init
from nlp import nlp
import os
import json
from tqdm import tqdm

bigram_flag = True
dataset = init.dataset
TFIDF_flag = True
LSI_flag = True

title_file_name = '/title_tokens_stemmed.tsv'
body_file_name = '/body_tokens_stemmed.tsv'
commitMSG_file_name = '/commit_tokens_stemmed.tsv'
if bigram_flag == True:
    title_file_name = '/title_bigrams_tokens_stemmed.tsv'
    body_file_name = '/body_bigrams_tokens_stemmed.tsv'
    commitMSG_file_name = '/commit_bigrams_tokens_stemmed.tsv'

def initNLPModel_per_repo(renew):
    for repo in tqdm(init.trainModelRepoList):
        print('init nlp model for repo: %s' % repo)
        # -------- model for title & description & commit msg
        global text_model
        textMode_save_id = repo.replace('/', '_') + '_title_body_commitmsg'
        try:
            text_model = nlp.Model([], textMode_save_id, renew)
            print('get text_model for repo: %s from local file' % repo)
        except:
            All_title_body_commitmsg_tokens = getAll_title_body_commitmsg_tokens(repo)
            if len(All_title_body_commitmsg_tokens) > 0:
                print('in total %s repos' % str(len(All_title_body_commitmsg_tokens)))

                text_model = nlp.Model(All_title_body_commitmsg_tokens, textMode_save_id, renew)
                print('done with text_model for repo: %s' % repo)

        # -------- model for code
        global code_model
        codeMode_save_id = repo.replace('/', '_') + '_code'

        try:
            code_model = nlp.Model([], codeMode_save_id, renew)
            print('get code_model for repo: %s from local file' % repo)
        except:
            All_code_tokens = getAll_code_tokens(repo, bigram_flag)
            if len(All_code_tokens) > 0:
                print('in total %s repos' % str(len(All_code_tokens)))
                code_model = nlp.Model(All_code_tokens, codeMode_save_id, renew)
                print('done with code_model for repo: %s' % repo)


def getAll_title_body_commitmsg_tokens(repo):
    # few ways to get all pr text
    # (1) for testing purpose, only collect pr in local disk
    # (2) collect all pr text for msr paper repos
    # (3) collect subset msr repos
    # (4) randomly sample 1000 prs for msr repos
    print('collecting all title, body, commit msg tokens ...')
    tokens = []
    for rootDir, dirs, filenames in os.walk(init.local_pr_data_dir + repo):
        for subdir in tqdm(dirs):
            dir = rootDir + "/" + subdir
            # for sub_rootDir, sub_dirs, sub_filenames in os.walk(rootDir + "/" + subdir):
            doc = []
            if os.path.exists(dir + title_file_name):
                doc.extend(getTextTokenInFile(dir + title_file_name))
            if os.path.exists(dir + body_file_name):
                doc.extend(getTextTokenInFile(dir + body_file_name))

            if os.path.exists(dir + commitMSG_file_name):
                doc.extend(getTextTokenInFile(dir + commitMSG_file_name))
            tokens.append(doc)
        break
    return tokens


def getAll_code_tokens(repo, bigram_flag):
    # few ways to get all pr text
    # (1) for testing purpose, only collect pr in local disk
    # (2) collect all pr text for msr paper repos
    # (3) collect subset msr repos
    # (4) randomly sample 1000 prs for msr repos
    print('collecting all code tokens ...')
    addCodeFile = '/add_code.json'
    deleteCodeFile = '/del_code.json'

    key = 'stem_tokens'
    if bigram_flag == True:
        key = 'stem_bigram_tokens'

    tokens = []
    for rootDir, dirs, filenames in os.walk(init.local_pr_data_dir + repo):
        for subdir in tqdm(dirs):
            dir = rootDir + "/" + subdir
            doc = []
            # print(dir + addCodeFile)
            if os.path.exists(dir + addCodeFile):
                with open(dir + addCodeFile) as jsonfile:
                    data = json.load(jsonfile)
                    for changeFile in data['file']:
                        if key in changeFile:
                            doc.extend(changeFile[key].split('\t'))
            if os.path.exists(dir + deleteCodeFile):
                with open(dir + deleteCodeFile) as jsonfile:
                    data = json.load(jsonfile)
                    for changeFile in data['file']:
                        if key in changeFile:
                            doc.extend(changeFile[key].split('\t'))
            tokens.append(doc)
        break
    return tokens


def getTextTokenInFile(filepath):
    tokens = []
    if os.path.exists(filepath):
        with open(filepath) as tsv:
            tokens_perPR = [line.strip().split('\t') for line in tsv]
            for t in tokens_perPR:
                tokens.extend(t)
    return tokens

if __name__ == "__main__":
    renew = True
    initNLPModel_per_repo(renew)
