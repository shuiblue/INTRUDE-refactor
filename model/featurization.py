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
from util import localfile
from util import misc
from util import wordext
from tqdm import tqdm
from github import github
from datetime import datetime

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

overlap_addFiles = []


def get_location_similarity_map(repo, pr1, pr2, overlap_addFiles):
    pr1_locList, pr1_overlap_loc = getPRLocationList(repo, pr1, overlap_addFiles)
    pr2_locList, pr2_overlap_loc = getPRLocationList(repo, pr2, overlap_addFiles)

    sim = {}
    locSimilarity = location_similarity(pr1_locList, pr2_locList)
    overlapLocSimilarity = location_similarity(pr1_overlap_loc, pr2_overlap_loc)

    sim['allfile'] = locSimilarity
    sim['overlapfile'] = overlapLocSimilarity
    return [sim['allfile'], sim['overlapfile']]


def getPRLocationList(repo, pr, overlap_addFiles=None):
    file_loc_list = []
    overlap_file_loc_list = []
    filepath = init.local_pr_data_dir + repo + '/' + pr + '/code_loc.json'
    if os.path.exists(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
            for file in data.keys():
                for loc in data[file]:
                    lst = []
                    lst.append(file)
                    lst.extend(loc)
                    file_loc_list.append(lst)
                    if (overlap_addFiles is not None) and (file in overlap_addFiles):
                        overlap_file_loc_list.append(lst)
    return file_loc_list, overlap_file_loc_list


def location_similarity(la, lb):
    def cross(x1, y1, x2, y2):
        return not ((y1 < x2) or (y2 < x1))

    if (la is None) or (lb is None):
        return 0.0

    '''
    # only calc on overlap files
    a_f = [x[0] for x in la]
    b_f = [x[0] for x in lb]
    c_f = set(a_f) & set(b_f)

    la = list(filter(lambda x: x[0] in c_f, la))
    lb = list(filter(lambda x: x[0] in c_f, lb))
    '''

    if len(la) + len(lb) == 0:
        return 0.0

    match_a = [False for x in range(len(la))]
    match_b = [False for x in range(len(lb))]

    index_b = {}
    for i in range(len(lb)):
        file = lb[i][0]
        if file not in index_b:
            index_b[file] = []
        index_b[file].append(i)

    for i in range(len(la)):
        file = la[i][0]
        for j in index_b.get(file, []):
            if cross(la[i][1], la[i][2], lb[j][1], lb[j][2]):
                match_a[i] = True
                match_b[j] = True

    # weigh with code line
    a_match, a_tot = 0, 0
    for i in range(len(la)):
        part_line = la[i][2] - la[i][1]
        a_tot += part_line
        if match_a[i]:
            a_match += part_line

    b_match, b_tot = 0, 0
    for i in range(len(lb)):
        part_line = lb[i][2] - lb[i][1]
        b_tot += part_line
        if match_b[i]:
            b_match += part_line

    if a_tot + b_tot == 0:
        return 0
    return (a_match + b_match) / (a_tot + b_tot)
    # return (match_a.count(True) + match_b.count(True)) / (len(match_a) + len(match_b))


def get_file_similarity(pr1_add_files, pr2_add_files, pr1_delete_files, pr2_delete_files):
    sim = {}
    sim['add'] = list_similarity(pr1_add_files, pr2_add_files)
    sim['delete'] = list_similarity(pr1_delete_files, pr2_add_files)
    return [sim['add'], sim['delete']]


def getFileCodeMap(repo, pr):
    file_add_code_map = {}
    file_del_code_map = {}

    dirPath = init.local_pr_data_dir + repo + '/' + pr
    addCodeFile = '/add_code.json'
    deleteCodeFile = '/del_code.json'

    key = 'stem_tokens'
    if bigram_flag == True:
        key = 'stem_bigram_tokens'

    addCodeJson = dirPath + addCodeFile
    deleteCodeJson = dirPath + deleteCodeFile

    if os.path.exists(addCodeJson):
        with open(addCodeJson) as jsonfile:
            data = json.load(jsonfile)
            for changeFile in data['file']:
                if key in changeFile:
                    file_add_code_map[changeFile['filename']] = changeFile[key]

    if os.path.exists(deleteCodeJson):
        with open(deleteCodeJson) as jsonfile:
            data = json.load(jsonfile)
            for changeFile in data['file']:
                if key in changeFile:
                    file_del_code_map[changeFile['filename']] = changeFile[key]

    return file_add_code_map, file_del_code_map


def getCodeSim(repo, pr1, pr2):
    sim = {}
    pr1_file_add_code_map, pr1_file_delete_code_map = getFileCodeMap(repo, pr1)
    pr2_file_add_code_map, pr2_file_delete_code_map = getFileCodeMap(repo, pr2)

    overlap_addFiles = misc.intersection(list(pr1_file_add_code_map.keys()), list(pr2_file_add_code_map.keys()))
    overlap_deleteFiles = misc.intersection(list(pr1_file_delete_code_map.keys()),
                                            list(pr2_file_delete_code_map.keys()))

    save_id = repo.replace('/', '_') + '_code'
    code_model = nlp.Model([], save_id)

    pr1_addCode_tokens = getCodeTokens(pr1_file_add_code_map, None)
    pr1_deleteCode_tokens = getCodeTokens(pr1_file_delete_code_map, None)
    pr1_addCode_tokens_overlapFile = getCodeTokens(pr1_file_add_code_map, overlap_addFiles)
    pr1_deleteCode_tokens_overlapFile = getCodeTokens(pr1_file_delete_code_map, overlap_deleteFiles)

    pr2_addCode_tokens = getCodeTokens(pr2_file_add_code_map, None)
    pr2_deleteCode_tokens = getCodeTokens(pr2_file_delete_code_map, None)
    pr2_addCode_tokens_overlapFile = getCodeTokens(pr2_file_add_code_map, overlap_addFiles)
    pr2_deleteCode_tokens_overlapFile = getCodeTokens(pr2_file_delete_code_map, overlap_deleteFiles)

    if LSI_flag:
        sim['lsi_add'] = code_model.query_sim_lsi(pr1_addCode_tokens, pr2_addCode_tokens)
        sim['lsi_delete'] = code_model.query_sim_lsi(pr1_deleteCode_tokens, pr2_deleteCode_tokens)

        sim['lsi_add_overlap'] = code_model.query_sim_lsi(pr1_addCode_tokens_overlapFile,
                                                          pr2_addCode_tokens_overlapFile)
        sim['lsi_delete_overlap'] = code_model.query_sim_lsi(pr1_deleteCode_tokens_overlapFile,
                                                             pr2_deleteCode_tokens_overlapFile)
    if TFIDF_flag:
        sim['tfidf_add'] = code_model.query_sim_tfidf(pr1_addCode_tokens, pr2_addCode_tokens)
        sim['tfidf_delete'] = code_model.query_sim_tfidf(pr1_deleteCode_tokens, pr2_deleteCode_tokens)

        sim['tfidf_add_overlap'] = code_model.query_sim_tfidf(pr1_addCode_tokens_overlapFile,
                                                              pr2_addCode_tokens_overlapFile)
        sim['tfidf_delete_overlap'] = code_model.query_sim_tfidf(pr1_deleteCode_tokens_overlapFile,
                                                                 pr2_deleteCode_tokens_overlapFile)

    return [sim['lsi_add'], sim['lsi_delete'], sim['lsi_add_overlap'], sim['lsi_delete_overlap'], sim['tfidf_add'],
            sim['tfidf_delete'], sim['tfidf_add_overlap'], sim['tfidf_delete_overlap']], \
           list(pr1_file_add_code_map.keys()), list(pr2_file_add_code_map.keys()), \
           list(pr2_file_add_code_map.keys()), list(pr2_file_delete_code_map.keys()), overlap_addFiles


def getCodeTokens(file_add_code_map, overlapFileList):
    tokens = []
    if overlapFileList is not None:
        for file in overlapFileList:
            tokens.extend(file_add_code_map[file].split())
    else:
        for codelist in file_add_code_map.values():
            tokens.extend(codelist.split())
    return tokens


def get_text_sim(repo, pr1, pr2, type):
    sim = {}
    pr1_token = getTokens(repo, pr1, type)
    pr2_token = getTokens(repo, pr2, type)
    save_id = repo.replace('/', '_') + '_title_body_commitmsg'

    if LSI_flag:
        text_model = nlp.Model([], save_id)
        sim['lsi'] = text_model.query_sim_lsi(pr1_token, pr2_token)
    if TFIDF_flag:
        text_model = nlp.Model([], save_id)
        sim['tfidf'] = text_model.query_sim_tfidf(pr1_token, pr2_token)

    return [sim['lsi'], sim['tfidf']]


def getTokens(repo, pr, type):
    dirPath = init.local_pr_data_dir + repo + '/' + pr
    if type == 'title':
        return getTextTokenInFile(dirPath + title_file_name)
    if type == 'body':
        return getTextTokenInFile(dirPath + body_file_name)
    if type == 'commit':
        return getTextTokenInFile(dirPath + commitMSG_file_name)




def reference_similarity(A, B):
    sim = list_similarity(A, B)
    A_set = set(A)
    B_set = set(B)
    if (A_set is None) or (B_set is None):
        return 0
    if (len(A_set) == 0) or (len(B_set) == 0):
        return 0

    if ((len(A_set) > 0) and (len(B_set) > 0)) and sim == 0:
        return -1
    return sim


def list_similarity(A, B):
    A_set = set(A)
    B_set = set(B)
    if (A_set is None) or (B_set is None):
        return 0
    if (len(A_set) == 0) or (len(B_set) == 0):
        return 0

    sim = len(A_set.intersection(B_set)) / len(A_set.union(B_set))
    return sim


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
    return tokens


def getTextTokenInFile(filepath):
    tokens = []
    with open(filepath) as tsv:
        tokens_perPR = [line.strip().split('\t') for line in tsv]
        for t in tokens_perPR:
            tokens.extend(t)
    return tokens


def getPRPairMapPerProject(data, label, renew=False, out=None):
    print('Model Data Input=', data)

    # run with all PR's info model
    PRpair_map_per_repo = {}
    pr_len = 0
    with open(data) as f:
        all_pr = f.readlines()
        pr_len = len(all_pr)
    count = 0

    for l in all_pr:
        # print("progress: " + str(count / pr_len) + ' pr:' + l)
        repo, pr1, pr2 = l.strip().split()

        # add pr pairs into map
        if repo not in PRpair_map_per_repo:
            PRpair_map_per_repo[repo] = []
        PRpair_map_per_repo[repo].append((pr1, pr2, label))
        count = count + 1
    return PRpair_map_per_repo


def getFeatureVectorForModeling(renew):

    for data in dataset:
        path = data[0]
        path = 'data/clf/first_msr_pairs.txt'
        label = data[1]
        group = data[2]

        default_path = init.currentDIR+'/'+path.replace('.txt', '') + '_feature_vector'
        X_path, y_path = default_path + '_X.json', default_path + '_y.json'

        if os.path.exists(X_path) and os.path.exists(y_path) and (not renew):
            print('feature vector already exists, read from local file')
            X = localfile.get_file(X_path)
            y = localfile.get_file(y_path)
            return X, y

        X, y = [], []

        # run with all PR's info model
        repo2PRpair_map = {}
        with open(init.currentDIR + '/' + path) as f:
            all_pr = f.readlines()

        for l in tqdm(all_pr):
            repo, n1, n2 = l.strip().split()

            if repo not in repo2PRpair_map:
                repo2PRpair_map[repo] = []
            repo2PRpair_map[repo].append((n1, n2))

        print('all=', len(all_pr))
        out_file = open(default_path + '_X_and_Y.txt', 'w+')

        for repo in tqdm(repo2PRpair_map):
            print('Start running on', repo)
            # sequence
            for pr_pair in tqdm(repo2PRpair_map[repo]):
                print(repo, pr_pair[0], pr_pair[1])
                featureVec = get_featureVector_ForPRpair(repo, pr_pair[0], pr_pair[1])
                X.append(featureVec)
                y.append(label)
                print(repo, pr_pair[0], pr_pair[1], featureVec, label, file=out_file)

        out_file.close()

        # save to local
        localfile.write_to_file(X_path, X)
        localfile.write_to_file(y_path, y)
        return (X, y)


'''
feature vector 
[title, description (body), commit_msg, code, file_list, overlap_file_list, loc, overlap_loc, version, issue/pr, SHA, time_interval, branch .....]
'''


def get_featureVector_ForPRpair(repo, pr1, pr2):
    similarity_vector = []

    #   1.   title [lsi, tfidf]   (count = 2)
    title_similarity_map = get_text_sim(repo, pr1, pr2, 'title')
    similarity_vector.extend(title_similarity_map)
    # #   2.   description body  (count = 2)
    description_similarity_map = get_text_sim(repo, pr1, pr2, 'body')
    similarity_vector.extend(description_similarity_map)
    # #   3.   commit body  (count = 2)
    commitMSG_similarity_map = get_text_sim(repo, pr1, pr2, 'commit')
    similarity_vector.extend(commitMSG_similarity_map)
    #
    # #   4. code  (count = 8)
    code_similarity, pr1_add_files, pr2_add_files, pr1_delete_files, pr2_delete_files, overlap_addFiles = getCodeSim(
        repo, pr1, pr2)
    similarity_vector.extend(code_similarity)
    # #   5. file set  (count = 2)
    fileList_similarity = get_file_similarity(pr1_add_files, pr2_add_files, pr1_delete_files, pr2_delete_files)
    similarity_vector.extend(fileList_similarity)

    #   6. code location  (count = 2)
    location_similarity = get_location_similarity_map(repo, pr1, pr2, overlap_addFiles)
    similarity_vector.extend(location_similarity)
    #    7. time interval  (count = 1)
    timeInterval = getTimeInterval(repo, pr1, pr2)
    similarity_vector.extend([timeInterval])
    #   8. reference  (count = 3)
    reference_similarity = getReferenceSimilarity(repo, pr1, pr2)
    similarity_vector.extend(reference_similarity)

    return similarity_vector


def getReferenceSimilarity(repo, pr1, pr2):
    pr1_reference_jsonfile = init.local_pr_data_dir + repo + '/' + pr1 + '/version_reference.json'
    pr2_reference_jsonfile = init.local_pr_data_dir + repo + '/' + pr2 + '/version_reference.json'

    sim = {}
    if os.path.exists(pr1_reference_jsonfile):
        with open(pr1_reference_jsonfile) as jsonfile:
            pr1_reference = json.load(jsonfile)[0]

    if os.path.exists(pr2_reference_jsonfile):
        with open(pr2_reference_jsonfile) as jsonfile:
            pr2_reference = json.load(jsonfile)[0]

    if pr1_reference['version'] != '' or pr2_reference['version'] != '':
        sim['version'] = reference_similarity(pr1_reference['version'].split('\t'), pr2_reference['version'].split('\t'))
    else:
        sim['version'] = 0

    if pr1_reference['issue'] != '' or pr2_reference['issue'] != '':
        sim['issue'] = reference_similarity(pr1_reference['issue'].split('\t'), pr2_reference['issue'].split('\t'))
    else:
        sim['issue'] = 0

    if pr1_reference['SHA'] != '' or pr2_reference['SHA'] != '':
        sim['SHA'] = reference_similarity(pr1_reference['SHA'].split('\t'), pr2_reference['SHA'].split('\t'))
    else:
        sim['SHA'] = 0

    return [sim['version'], sim['issue'], sim['SHA']]


def getTimeInterval(repo, pr1, pr2):
    d1 = getTime(repo, pr1)
    d2 = getTime(repo, pr2)

    d1 = datetime.strptime(d1, "%Y-%m-%dT%H:%M:%SZ")
    d2 = datetime.strptime(d2, "%Y-%m-%dT%H:%M:%SZ")
    return abs((d2 - d1).days)


def getTime(repo, pr):
    json_filepath = init.local_pr_data_dir + repo + '/' + pr + '/api.json'
    timeStampFile = init.local_pr_data_dir + repo + '/' + pr + '/timestamp.txt'

    if os.path.exists(timeStampFile):
        with open(timeStampFile) as timefile:
            return timefile.read()
    else:
        if os.path.exists(json_filepath):
            with open(json_filepath) as jsonfile:
                pulljson = json.load(jsonfile)
        else:
            pulljson = github.get_pull(repo, pr)

        timeStamp = pulljson['created_at']

        file1 = open(timeStampFile, "w")
        file1.write(timeStamp)
        file1.close()
    return timeStamp


if __name__ == "__main__":
    renew = True
    initNLPModel_per_repo(renew)
    # getFeatureVectorForModeling(renew)
