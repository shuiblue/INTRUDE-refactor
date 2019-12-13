import time
import os.path
from datetime import datetime
import pathlib
from github.fetch_raw_diff import *
import init
import util.timeUtil
# from flask import Flask
# from flask_github import GitHub

from util import localfile
from random import randint
import logging
import scraper
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

#
# # @api.access_token_getter
# def token_getter():
#     with open('./data/token.txt', 'r') as file:
#         access_token = [line.rstrip('\n') for line in file]
#         return access_token

def text2list_precheck(func):
    def proxy(text):
        if text is None:
            return []
        ret = func(text)
        return ret

    return proxy


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


'''
def fresh_pr_info(pull):
    file_list = fetch_file_list(pull)
    path = '/DATA/luyao/pr_data/%s/%s' % (pull["base"]["repo"]["full_name"], pull["number"])
    parse_diff_path = path + '/parse_diff.json'
    localfile.write_to_file(parse_diff_path, file_list)
'''

file_list_cache = {}

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


@text2list_precheck
def get_pr_and_issue_numbers(text):
    nums = []
    nums += re.findall('#([0-9]+)', text)
    nums += re.findall('pull\/([0-9]+)', text)
    nums += re.findall('issues\/([0-9]+)', text)
    nums = list(filter(lambda x: len(x) > 0, nums))
    nums = list(set(nums))
    return nums


'''
def fresh_pr_info(pull):
    file_list = fetch_file_list(pull)
    path = '/DATA/luyao/pr_data/%s/%s' % (pull["base"]["repo"]["full_name"], pull["number"])
    parse_diff_path = path + '/parse_diff.json'
    localfile.write_to_file(parse_diff_path, file_list)
'''

file_list_cache = {}

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
