import time
import os
import os.path
import re
import requests
import platform
from datetime import datetime
import pathlib
import fetch_raw_diff
import init
import util.timeUtil
# from flask import Flask
# from flask_github import GitHub

import scraper
from util import localfile
from random import randint
import logging
import json

logger = logging.getLogger('INTRUDE.scraper')
nonCodeFileExtensionList = [line.rstrip('\n') for line in open('./data/NonCodeFile.txt')]
# app = Flask(__name__)

# app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID')
# app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET')
# app.config['GITHUB_BASE_URL'] = 'https://api.github.com/'
# app.config['GITHUB_AUTH_URL'] = 'https://github.com/login/oauth/'

LOCAL_DATA_PATH = init.LOCAL_DATA_PATH

# api = GitHub(app)
api = scraper.GitHubAPI()


# @api.access_token_getter
def token_getter():
    with open('./data/token.txt', 'r') as file:
        access_token = [line.rstrip('\n') for line in file]
        return access_token


def text2list_precheck(func):
    def proxy(text):
        if text is None:
            return []
        ret = func(text)
        return ret

    return proxy


@text2list_precheck
def get_numbers(text):
    # todo previous version, got tons of FP crossreferece numbers
    # nums = list(filter(lambda x: len(x) >= 3, re.findall('([0-9]+)', text)))
    # nums = list(set(nums))

    # use get_pr_and_issue_numbers instead


    return get_pr_and_issue_numbers(text)


@text2list_precheck
def get_version_numbers(text):
    nums = [''.join(x) for x in re.findall('(\d+\.)?(\d+\.)(\d+)', text)]
    nums = list(set(nums))
    return nums


@text2list_precheck
def get_pr_and_issue_numbers(text):
    nums = []
    nums += re.findall('#([0-9]+)', text)
    nums += re.findall('pull\/([0-9]+)', text)
    nums += re.findall('issues\/([0-9]+)', text)
    nums = list(filter(lambda x: len(x) > 0, nums))
    nums = list(set(nums))
    return nums


def allNonCodeFiles(pull):

    # file_list = fetch_file_list(pull)
    try:
        file_list = fetch_file_list(pull)
    except:
        print("file list too big")
        return True
        # raise Exception('too big', pull['html_url'])

    total_num_files = len(file_list)
    noncode_file_count = 0
    for file in file_list:
        for extension in nonCodeFileExtensionList:
            if file['name'].endswith(extension):
                noncode_file_count += 1
        if (noncode_file_count == total_num_files):
            return True
        else:
            return False

# This function checks if the PR has changed too many files
def check_too_big(pull):
    if not ("changed_files" in pull):
        pull = get_pull(pull["base"]["repo"]["full_name"], pull["number"])

    if not ("changed_files" in pull):
        pull = get_pull(pull["base"]["repo"]["full_name"], pull["number"], True)

    if pull["changed_files"] > 50:
        #         print('more than 50 changed files')
        return True
    if (pull["additions"] >= 10000) or (pull["deletions"] >= 10000):
        #         print('more than 10000 Loc changes')
        return True
    return False


check_large_cache = {}


# This function checks if the pull has changed too many files, call check_too_big internally. I am not sure why this is efficient...
def check_large(pull):
    #     print ("check_large:" + str(pull['number']))
    global check_large_cache
    index = (pull["base"]["repo"]["full_name"], pull["number"])
    if index in check_large_cache:
        return check_large_cache[index]

    check_large_cache[index] = True  # defalue true

    if check_too_big(pull):
        return True

    try:
        l = len(fetch_pr_info(pull))
    except Exception as e:
        if 'too big' in str(e):
            return True

    '''
    if l == 0:
        try:
            file_list = fetch_file_list(pull, True)
        except:
            path = '/DATA/luyao/pr_data/%s/%s' % (pull["base"]["repo"]["full_name"], pull["number"])
            flag_path = path + '/too_large_flag.json'
            localfile.write_to_file(flag_path, 'flag')
            print('too big', pull['html_url'])
            return True
    '''

    path = init.LOCAL_DATA_PATH + '/pr_data/%s/%s/raw_diff.json' % (pull["base"]["repo"]["full_name"], pull["number"])
    if os.path.exists(path) and (os.path.getsize(path) >= 50 * 1024):
        return True

    check_large_cache[index] = False
    return False


'''
def fresh_pr_info(pull):
    file_list = fetch_file_list(pull)
    path = '/DATA/luyao/pr_data/%s/%s' % (pull["base"]["repo"]["full_name"], pull["number"])
    parse_diff_path = path + '/parse_diff.json'
    localfile.write_to_file(parse_diff_path, file_list)
'''

file_list_cache = {}


def fetch_pr_info(pull, must_in_local=False):
    #     print ("fetch_pr_info:" + str(pull['number']))
    global file_list_cache
    ind = (pull["base"]["repo"]["full_name"], pull["number"])
    if ind in file_list_cache:
        return file_list_cache[ind]

    path = LOCAL_DATA_PATH + '/pr_data/%s/%s' % (pull["base"]["repo"]["full_name"], pull["number"])
    parse_diff_path = path + '/parse_diff.json'
    raw_diff_path = path + '/raw_diff.json'
    pull_files_path = path + '/pull_files.json'

    flag_path = path + '/too_large_flag.json'
    if os.path.exists(flag_path):
        raise Exception('too big', pull['html_url'])

    if os.path.exists(parse_diff_path):
        try:
            ret = localfile.get_file(parse_diff_path)
            file_list_cache[ind] = ret
            return ret
        except:
            pass

    if os.path.exists(raw_diff_path) or os.path.exists(pull_files_path):
        if os.path.exists(raw_diff_path):
            file_list = localfile.get_file(raw_diff_path)
        elif os.path.exists(pull_files_path):
            pull_files = localfile.get_file(pull_files_path)
            file_list = [parse_diff(file["file_full_name"], file["changed_code"]) for file in pull_files]
        else:
            raise Exception('error on fetch local file %s' % path)
    else:
        if must_in_local:
            raise Exception('not found in local')

        try:
            file_list = fetch_file_list(pull)
        except:
            localfile.write_to_file(flag_path, 'flag')
            raise Exception('too big', pull['html_url'])

    # print(path, [x["name"] for x in file_list])
    localfile.write_to_file(parse_diff_path, file_list)
    file_list_cache[ind] = file_list
    return file_list


# -------------------About Repo--------------------------------------------------------
def get_repo_info(repo, type, renew):
    save_path = LOCAL_DATA_PATH + '/pr_data/' + repo + '/%s_list.json' % type
    if type == 'fork':
        save_path = LOCAL_DATA_PATH + '/result/' + repo + '/forks_list.json'

    if (os.path.exists(save_path)) and (not renew):
        try:
            return localfile.get_file(save_path)
        except:
            pass

    print('start fetch new list for ', repo, type)
    if (type == 'pull') or (type == 'issue'):
        ret = api.request('repos/%s/%ss' % (repo, type), state='all', paginate=True)
    else:
        if type == 'branch':
            type = 'branche'
        ret = api.request('repos/%s/%ss' % (repo, type), True)

    localfile.write_to_file(save_path, ret)
    return ret


def get_repo_info_forPR(repo, type, renew):
    filtered_result = []

    pullListfile = pathlib.Path(init.local_pr_data_dir + repo + '/pull_list.json')
    if pullListfile.exists():
        tocheck_pr = getOldOpenPRs(repo)
        print("tocheck_pr " + str(tocheck_pr))
        if (tocheck_pr is None):
            tocheck_pr = 0

        save_path = LOCAL_DATA_PATH + '/pr_data/' + repo + '/%s_list.json' % type
        if type == 'fork':
            save_path = LOCAL_DATA_PATH + '/result/' + repo + '/forks_list.json'

        if (os.path.exists(save_path)) and (not renew):
            try:
                return localfile.get_file(save_path)
            except:
                pass

        print('start fetch new list for ', repo, type)
        if (type == 'pull') or (type == 'issue'):
            page_index = 1
            while (True):
                ret = api.requestPR('repos/%s/%ss' % (repo, type), state='all', page=page_index)
                numPR = init.numPRperPage
                if (len(ret) > 0):
                    for pr in ret:
                        # if (pr['number'] >= tocheck_pr):
                        if (pr['number'] > tocheck_pr):
                            filtered_result.append(pr)
                        else:
                            print('get all ' + str(len(filtered_result)) + ' prs')
                            localfile.replaceWithNewPRs(save_path, filtered_result)
                            return filtered_result
                    if (len(filtered_result) < numPR):
                        print('get all ' + str(len(filtered_result)) + ' prs -- after page ' + str(page_index))
                        localfile.replaceWithNewPRs(save_path, filtered_result)
                        return filtered_result
                    else:
                        page_index += 1
                        numPR += init.numPRperPage
                else:
                    print("get pulls failed")
                    return filtered_result
        else:
            if type == 'branch':
                type = 'branche'
            ret = api.request('repos/%s/%ss' % (repo, type), True)

        localfile.write_to_file(save_path, ret)
    else:
        print('pull list does not exist, get from scratch')
        ret = get_repo_info(repo, type, renew)
    return ret


def fetch_commit(url, renew=False):
    save_path = LOCAL_DATA_PATH + '/pr_data/%s.json' % url.replace('https://api.github.com/repos/', '')
    if os.path.exists(save_path) and (not renew):
        try:
            return localfile.get_file(save_path)
        except:
            pass

    c = api.request(url)
    time.sleep(0.7)
    file_list = []
    for f in c['files']:
        if 'patch' in f:
            file_list.append(fetch_raw_diff.parse_diff(f['filename'], f['patch']))
    localfile.write_to_file(save_path, file_list)
    return file_list


# ------------------About Pull Requests----------------------------------------------------

def get_pull(repo, num, renew=False):
    save_path = LOCAL_DATA_PATH + '/pr_data/%s/%s/api.json' % (repo, num)
    if os.path.exists(save_path) and (not renew):
        try:
            return localfile.get_file(save_path)
        except:
            pass

    r = api.request('repos/%s/pulls/%s' % (repo, num))
    time.sleep(3.0)
    localfile.write_to_file(save_path, r)
    return r


def get_pull_commit(pull, renew=False):
    save_path = LOCAL_DATA_PATH + '/pr_data/%s/%s/commits.json' % (pull["base"]["repo"]["full_name"], pull["number"])
    if os.path.exists(save_path) and (not renew):
        try:
            return localfile.get_file(save_path)
        except:

            pass
    #     commits = api.request(pull['commits_url'].replace('https://api.github.com/', ''), True)

    commits = api.request(pull['commits_url'].replace('https://api.github.com/', ''), paginate=True, state='all')
    # commits = api.request(pull['commits_url'].replace('https://api.github.com/', paginate=True, state='all'))
    time.sleep(0.7)
    localfile.write_to_file(save_path, commits)
    return commits


def get_another_pull(pull, renew=False):
    save_path = LOCAL_DATA_PATH + '/pr_data/%s/%s/another_pull.json' % (
        pull["base"]["repo"]["full_name"], pull["number"])
    if os.path.exists(save_path) and (not renew):
        try:
            return localfile.get_file(save_path)
        except:
            pass

    comments_href = pull["_links"]["comments"]["href"]  # found cites in comments, but checking events is easier.
    comments = api.request(comments_href, True)
    time.sleep(0.7)
    candidates = []
    for comment in comments:
        candidates.extend(get_pr_and_issue_numbers(comment["body"]))
    candidates.extend(get_pr_and_issue_numbers(pull["body"]))

    result = list(set(candidates))

    localfile.write_to_file(save_path, result)
    return result


def fetch_file_list(pull, renew=False):
    repo, num = pull["base"]["repo"]["full_name"], str(pull["number"])
    save_path = LOCAL_DATA_PATH + '/pr_data/' + repo + '/' + num + '/raw_diff.json'

    if os.path.exists(save_path) and (not renew):
        try:
            return localfile.get_file(save_path)
        except:
            pass

    # t = api.get('repos/%s/pulls/%s/files?page=3' % (repo, num))
    t = api.request('repos/%s/pulls/%s/files?page=3' % (repo, num))
    file_list = []
    if len(t) > 0:
        raise Exception('too big', pull['html_url'])
    else:
        li = api.request('repos/%s/pulls/%s/files' % (repo, num), paginate=True)
        # li = api.request( 'repos/%s/pulls/%s/files' % (repo, num), True)
        time.sleep(0.8)
        for f in li:
            if f.get('changes', 0) <= 5000 and ('filename' in f) and ('patch' in f):
                file_list.append(fetch_raw_diff.parse_diff(f['filename'], f['patch']))

    localfile.write_to_file(save_path, file_list)
    return file_list


pull_commit_sha_cache = {}


def pull_commit_sha(p):
    index = (p["base"]["repo"]["full_name"], p["number"])
    if index in pull_commit_sha_cache:
        return pull_commit_sha_cache[index]
    c = get_pull_commit(p)
    ret = [(x["sha"], x["commit"]["author"]["name"]) for x in
           list(filter(lambda x: x["commit"]["author"] is not None, c))]
    pull_commit_sha_cache[index] = ret
    return ret


# ------------------Data Pre Collection----------------------------------------------------
def run_and_save(repo, skip_big=False):
    repo = repo.strip()

    skip_exist = True

    pulls = get_repo_info(repo, 'pull', True)

    for pull in pulls:
        num = str(pull["number"])
        pull_dir = LOCAL_DATA_PATH + '/pr_data/' + repo + '/' + num

        pull = get_pull(repo, num)

        if skip_big and check_too_big(pull):
            continue

        if skip_exist and os.path.exists(pull_dir + '/raw_diff.json'):
            continue

        fetch_file_list(repo, pull)

        print('finish on', repo, num)


# ------------------copy from ghd project ---------------------------------------------------
class TokenNotReady(requests.HTTPError):
    pass


def request(self, url, method='get', paginate=False, data=None, **params):
    # type: (str, str, bool, str) -> dict
    """ Generic, API version agnostic request method """
    timeout_counter = 0
    if paginate:
        paginated_res = []
        params['page'] = 1
        params['per_page'] = 100

    while True:
        for token in self.tokens:
            # for token in sorted(self.tokens, key=lambda t: t.when(url)):
            if not token.ready(url):
                continue

            try:
                r = token.request(url, method=method, data=data, **params)
            except requests.ConnectionError:
                print('except requests.ConnectionError')
                continue
            except TokenNotReady:
                continue
            except requests.exceptions.Timeout:
                timeout_counter += 1
                if timeout_counter > len(self.tokens):
                    raise
                continue  # i.e. try again

            if r.status_code in (404, 451):
                print("404, 451 retry..")
                return {}
                # API v3 only
                # raise RepoDoesNotExist(
                #     "GH API returned status %s" % r.status_code)
            elif r.status_code == 409:
                print("409 retry..")
                # repository is empty https://developer.github.com/v3/git/
                return {}
            elif r.status_code == 410:
                print("410 retry..")
                # repository is empty https://developer.github.com/v3/git/
                return {}
            elif r.status_code == 403:
                # repository is empty https://developer.github.com/v3/git/
                print("403 retry..")
                time.sleep(randint(1, 29))
                continue
            elif r.status_code == 443:
                # repository is empty https://developer.github.com/v3/git/
                print("443 retry..")
                time.sleep(randint(1, 29))
                continue
            elif r.status_code == 502:
                # repository is empty https://developer.github.com/v3/git/
                print("443 retry..")
                time.sleep(randint(1, 29))
                continue
            r.raise_for_status()
            res = r.json()
            if paginate:
                paginated_res.extend(res)
                has_next = 'rel="next"' in r.headers.get("Link", "")
                if not res or not has_next:
                    return paginated_res
                else:
                    params["page"] += 1
                    continue
            else:
                return res

        next_res = min(token.when(url) for token in self.tokens)
        sleep = int(next_res - time.time()) + 1
        if sleep > 0:
            logger.info(
                "%s: out of keys, resuming in %d minutes, %d seconds",
                datetime.now().strftime("%H:%M"), *divmod(sleep, 60))
            time.sleep(sleep)
            logger.info(".. resumed")


def getOldOpenPRs(repo):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    old_openPR_list = []

    file = init.local_pr_data_dir + repo + '/pull_list.json'
    latest_pr = 0
    with open(file) as json_file:
        data = json.load(json_file)
        if (len(data) > 0):
            latest_pr = data[0]['number']
            print("latest_pr" + str(latest_pr))
            for pr in data:
                number = pr['number']
                state = pr['state']
                created_at = pr['created_at']
                if (state == 'open'):
                    if (util.timeUtil.days_between(created_at, now) < 3):
                        old_openPR_list.append(number)

            if len(old_openPR_list) > 0:
                minID = min(old_openPR_list)
                if minID < latest_pr:
                    print("min(old_openPR_list)" + str(min(old_openPR_list)))
                    return min(old_openPR_list)
            else:
                print("latest_pr" + str(latest_pr))
                return latest_pr


if __name__ == "__main__":
    # r = get_pull('angular/angular.js', '16629', 1)
    # print(r['changed_files'])
    # get_pull_commit(get_pull('ArduPilot/ardupilot', '8008'))
    api.request("repos/jquery/jquery/pulls/4406/commits")
    api.request("repos/jquery/jquery/pulls/4406/commits")
    api.request("repos/jquery/jquery/pulls/4406/commits")
    api.request("repos/jquery/jquery/pulls/4406/commits")
#     get_pull_commit('jquery/jquery', '4379', True)
# print(len(get_repo_info('FancyCoder0/INFOX', 'pull', True)))
# print(len(get_repo_info('FancyCoder0/INFOX', 'issue', True)))
# print(len(get_repo_info('FancyCoder0/INFOX', 'commit', True)))
# print(len(get_repo_info('tensorflow/tensorflow', 'branch', True)))
#
# print(len(fetch_file_list(get_pull('FancyCoder0/INFOX', '113', True))))
# print(get_another_pull(get_pull('facebook/react', '12503'), True))
# print([x['commit']['message'] for x in get_pull_commit(get_pull('facebook/react', '12503'), True)])
