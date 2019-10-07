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
import json

logger = logging.getLogger('INTRUDE.scraper')
nonCodeFileExtensionList = [line.rstrip('\n') for line in open('../data/NonCodeFile.txt')]
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
