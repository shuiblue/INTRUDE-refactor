import os
import sys

from datetime import datetime, timedelta
# from sklearn.utils import shuffle

from github import git

import os
import os.path
from sklearn.externals import joblib
import init
import util
from model import calculateNLPmodel
import model.calculateNLPmodel



print('load existing model')
c = joblib.load(init.model_saved_path)

cite = {}
renew_pr_list_flag = False

filter_out_too_old_pull_flag = True
filter_already_cite = True
filter_create_after_merge = False
filter_overlap_author = True
filter_out_too_big_pull_flag = False
filter_same_author_and_already_mentioned = True
onlyChangedNonCodeFiles_flag = True




def get_time(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")


last_detect_repo = None



def have_commit_overlap(p1, p2):
    t = set(git.pull_commit_sha(p1)) & set(git.pull_commit_sha(p2))
    p1_user = p1["user"]["id"]
    p2_user = p2["user"]["id"]
    for x in t:
        if (x[1] == p1_user) or (x[1] == p2_user):
            return True
    return False


# returns similarity score and feature vector
def get_topK(repo, num1, topK=10, print_progress=False, use_way='new'):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    global last_detect_repo
    if last_detect_repo != repo:
        last_detect_repo = repo
        model.initNLPModel_per_repo(repo)
        # init_model_with_repo(repo)

    pulls = git.get_repo_info(repo, 'pull', renew=False)
    print("get all " + str(len(pulls)) + "  prs for repo " + repo)

    print("get pr " + str(num1))
    pullA = git.get_pull(repo, num1)

    if git.allNonCodeFiles(pullA):
        return [], None

    if filter_already_cite:
        cite[str(pullA["number"])] = git.get_another_pull(pullA)

    results = {}
    results_featureVector = {}
    tot = len(pulls)
    cnt = 0

    pull_v = {}

    # check if any flags are active & violated
    for pull in pulls:
        feature_vector = {}
        cnt += 1

        # if the pr is older than 1 year, ignore
        current_pr_createdAt = pull['created_at']
        if (util.timeUtil.days_between(now, current_pr_createdAt) > init.comparePRs_timeWindow_inDays):
            print(str(pull['number']) + "older than " + str(init.pr_date_difference_inDays) + " days , stop")
            break

        if filter_out_too_old_pull_flag:
            #             time_diff = abs((get_time(pullA["updated_at"]) - get_time(pull["updated_at"])).days)
            #  updated_at is not reliable, see example: https://github.com/jquery/jquery/pull/1002
            time_diff = abs((get_time(pullA["created_at"]) - get_time(pull["created_at"])).days)
            # print ("time diff" + str(time_diff))
            if time_diff >= 2 * 365:  # more than 2 years
                continue

        if filter_larger_number:
            if int(pull["number"]) >= int(num1):
                continue

        if filter_same_author_and_already_mentioned:
            # same author
            if pull["user"]["id"] == pullA["user"]["id"]:
                continue

            # case of following up work (not sure)
            if str(pull["number"]) in (git.get_pr_and_issue_numbers(pullA["title"]) + \
                                       git.get_pr_and_issue_numbers(pullA["body"])):
                continue

        # load events of both PRs, check if one referenced the other
        # EX: https://github.com/akinnae/curly-train/pull/1
        # cross-reference check
        if filter_already_cite:
            # "cite" cases
            if (str(pull["number"]) in cite.get(str(pullA["number"]), [])) or \
                    (str(pullA["number"]) in cite.get(str(pull["number"]), [])):
                continue

        if filter_create_after_merge:
            # create after another is merged
            if (pull["merged_at"] is not None) and \
                    (get_time(pull["merged_at"]) < get_time(pullA["created_at"])) and \
                    ((get_time(pullA["created_at"]) - get_time(pull["merged_at"])).days >= 14):
                continue


        # if print_progress:
        #     if cnt % 100 == 0:
        #         print('progress = ', 1.0 * cnt / tot)
        #         sys.stdout.flush()

        if use_way == 'new':
            # feature_vector = get_pr_sim_vector(pullA, pull)
            feature_vector =  model.featurization.get_featureVector_ForPRpair(repo, pullA, pull)
            results_featureVector[pull["number"]] = feature_vector
            results[pull["number"]] = c.predict_proba([feature_vector])[0][1]


    result = [(x, y) for x, y in sorted(results.items(), key=lambda x: x[1], reverse=True)][:topK]
    # result_fv = [(x,y) for x, y in sorted(results_featureVector.items(), key=lambda x: x[1], reverse=True)][:topK]

    if (len(result) == 0):
        return result, None
    else:
        return result, results_featureVector[result[0][0]]


def run_list(repo, renew=False, run_num=200, rerun=False):
    model.init_model_with_repo(repo)
    pulls = git.get_repo_info(repo, 'pull', renew_pr_list_flag)

    all_p = set([str(pull["number"]) for pull in pulls])
    select_p = all_p

    log_path = 'evaluation/' + repo.replace('/', '_') + '_stimulate_detect.log'
    out_path = 'evaluation/' + repo.replace('/', '_') + '_run_on_select_all.txt'

    print('-----', file=open(out_path, 'w+'))

    for pull in pulls:
        num1 = str(pull["number"])

        if num1 not in select_p:
            continue

        print('Run on PR #%s' % num1)

        topk, featureVector_list = get_topK(repo, num1)
        if len(topk) == 0:
            continue

        num2, prob = topk[0][0], topk[0][1]
        vet = (pull, git.get_pull(repo, num2))

        with open(out_path, 'a+') as outf:
            print("\t".join([repo, str(num1), str(num2), "%.4f" % prob] + \
                            ["%.4f" % f for f in vet] + \
                            ['https://www.github.com/%s/pull/%s' % (repo, str(num1)), \
                             'https://www.github.com/%s/pull/%s' % (repo, str(num2))]
                            ),
                  file=outf)

        with open(log_path, 'a+') as outf:
            print(repo, num1, ':', topk, file=outf)


def detect_one(repo, num):
    print('analyzing ', repo, num)
    speed_up = True
    filter_create_after_merge = True

    ret, feature_vector = get_topK(repo, num, 1, True)
    if len(ret) < 1:
        print("no result")
        return -1, -1, -1
    else:
        return ret[0][0], ret[0][1], feature_vector
        # return ret[0][0], ret[0][1]


if __name__ == "__main__":
    # detect one PR
    if len(sys.argv) == 3:
        r = sys.argv[1].strip()
        n = sys.argv[2].strip()
        detect_one(r, n)

    # detection on history (random sampling)
    if len(sys.argv) == 2:
        speed_up = True
        filter_create_after_merge = True
        filter_larger_number = True
        r = sys.argv[1].strip()
        run_list(r)
