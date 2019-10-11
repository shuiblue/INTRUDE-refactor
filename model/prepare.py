from util import localfile
import os.path
from github.github import *
from nlp import nlp
from util import wordext
import copy
import itertools
from tqdm import tqdm
from random import sample
import datetime
import concurrent.futures

part_params = None

extract_sim_type = 'ori_and_overlap'

add_timedelta = False
add_conf = False
add_commit_message = True
feature_conf = ''
if add_timedelta:
    feature_conf += '_time'
if add_conf:
    feature_conf += '_conf'
if add_commit_message:
    feature_conf += '_commit_message'


def process_PR(repo):
    renew = True
    # for repo in init.trainModelRepoList:
    print('Start analyzing repo: ', repo)
    # prID_list = get_prID_list(repo, renew)
    pr_list = get_pr_list(repo, renew)

    print('number of PR pairs in dataset:', len(pr_list))
    preprocess_documents(repo, pr_list, renew)


def get_pr_list(repo, renew):
    pr_list = []
    prlist_json_filepath = init.local_pr_data_dir + repo + '/pull_list.json'
    if not os.path.exists(prlist_json_filepath):
        get_repo_info_forPR(repo, 'pull', renew)

    with open(prlist_json_filepath) as json_file:
        data = json.load(json_file)
        for p in data:
            pr_list.append(p)
        # pr_list.sort(reverse=False)
        # todo for testing purpose, sample 100 prs per repo
        # pr_list = sample(pr_list, 100)
    return pr_list


def generatePaths(data, out):
    default_path = data.replace('.txt', '') + '_feature_vector'
    out = default_path if out is None else default_path + '_' + out
    X_path, y_path = out + '_X.json', out + '_y.json'
    out_file = open(out + '_X_and_Y.txt', 'w+')
    return X_path, y_path, out_file


def preprocess_documents(repo, pulls, renew):
    for pull in tqdm(pulls):  # tqdm is used for print progress bar https://github.com/tqdm/tqdm/

        pr_id = pull['number']
        # if pr_id != 14378:
        #     continue
        outfile_prefix = init.local_pr_data_dir + repo + "/" + str(pr_id)
        print(str(pr_id))
        if os.path.exists(outfile_prefix + '/updateAt.txt') and (not renew):
            print('skip')
            continue

        # if the pr is older than 1 year, ignore
        #         # todo: why do I care about the create date when training the model? comment out for now
        #         # current_pr_createdAt = pull['created_at']
        #         # if (util.timeUtil.days_between(now, current_pr_createdAt) > init.comparePRs_timeWindow_inDays):
        #         #     print(str(pull['number']) + " older than " + str(init.pr_date_difference_inDays) + " days , stop")
        #         #     break

        # ----------- title and description -----------
        wordext.get_tokens_from_file(pull['title'], outfile_prefix, 'title')
        if pull["body"]:
            if not os.path.exists(outfile_prefix + "/body_tokens_stemmed.tsv") or renew:
                body_str = re.sub("(<.*?>)", "", pull['body'], flags=re.DOTALL)
                wordext.get_tokens_from_file(body_str, outfile_prefix, 'body')

        # # ----------- commit msg  -----------
        print('check commit')
        all_commit_msg = concat_commits(get_pr_commit(repo, pr_id))
        wordext.get_tokens_from_file(all_commit_msg, outfile_prefix, 'commit')
        # # ----------- CODE & FILE  -----------
        print('check code ,file ')
        pr_filelist_json = fetch_pr_code_info(repo, pr_id)
        if (len(pr_filelist_json) == 0):
            localfile.write_to_file(outfile_prefix + "/updateAt.txt",
                                    str(datetime.datetime.now().strftime("%Y-%m-%d")))
            continue
        wordext.get_code_tokens_from_file(pr_filelist_json, outfile_prefix, 'add_code')
        wordext.get_code_tokens_from_file(pr_filelist_json, outfile_prefix, 'del_code')

        # ----------- Location  -----------
        pr_filelist_json = fetch_pr_code_info(repo, pr_id)
        if len(pr_filelist_json) > 0:
            getCodeLocation(pr_filelist_json, outfile_prefix)
        # ----------- version number  & crossReference  PR or ISSUE-----------
        print('check reference')
        body_text = '' if pull["body"] is None else pull["body"]
        pull_text = str(pull["title"]) + ' ' + str(body_text) + ' ' + all_commit_msg
        getReference(repo, pull_text, outfile_prefix)

        localfile.write_to_file(outfile_prefix + "/updateAt.txt", str(datetime.datetime.now().strftime("%Y-%m-%d")))


def getReference(repo, pull_text, outfile_prefix):
    ref_json = []
    version_numberList = wordext.get_version_number(repo, pull_text)
    issueList = wordext.getIssueReference(pull_text)
    SHA_list = wordext.getSHA(pull_text)
    ref_json.append({
        'version': '\t'.join(version_numberList),
        'issue': '\t'.join(issueList),
        'SHA': '\t'.join(SHA_list)
    })
    with open(outfile_prefix + "/version_reference.json", 'w+') as outfile:
        json.dump(ref_json, outfile)


def get_tokens(text, outfile_prefix):
    tokens = wordext.get_words_from_text(text, outfile_prefix)
    return tokens


def getCodeLocation(filelist_json, outfile_prefix):
    location_set = {}
    for f_json in filelist_json:
        file = f_json["name"]
        location_set[file] = []
        # ignore non code file
        if language_tool.is_text(file):
            continue
        loc_list = f_json['location']['add']
        for x in loc_list:
            location_set[file].append([int(x[0]), int(x[0]) + int(x[1])])
    with open(outfile_prefix + "/code_loc.json", 'w+') as outfile:
        json.dump(location_set, outfile)



# import a new API to create a thread pool
from concurrent.futures import ThreadPoolExecutor as PoolExecutor

repolist = init.trainModelRepoList
# create a thread pool of 4 threads
with PoolExecutor(max_workers=4) as executor:

    # distribute the 1000 URLs among 4 threads in the pool
    # _ is the body of each page that I'm ignoring right now
    for _ in executor.map(process_PR, repolist):
        pass