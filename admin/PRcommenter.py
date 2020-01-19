import json
import requests

# Authentication info

# with open('./input/authParams.txt') as f:
with open('../input/authParams.txt') as f:
    USERNAME, TOKEN = f.read().splitlines()


# def make_github_comment(REPO, PR_NUMBER, PR_NUMBER2, FEATURES, body=None):
def make_github_comment(REPO, PR_NUMBER, PR_NUMBER2, body=None):
    '''Create a comment on github.com using the given parameters.'''
    # Our url to create comments via POST
    url = 'https://api.github.com/repos/%s/issues/%i/comments' % (REPO, PR_NUMBER)
    # Create an authenticated session to create the comment
    headers = {
        "Authorization": "token %s" % TOKEN,
    }
    # Create our comment
    body = body % PR_NUMBER2
    survey_url = "http://forks-insight.com/INTRUDE-survey?repo="+REPO+"&pr1="+str(PR_NUMBER)+"&pr2="+str(PR_NUMBER2)+"&response="

    body += '\n\n' +" To improve our bot, you can help us out by clicking one of the options below:\n \
    - This pull request __is a duplicate__, so this comment was __useful__. [check]("+survey_url+"dup_useful)\n \
    - This pull request is __not a duplicate__, but this comment was __useful__ nevertheless. [check]("+survey_url+"notDup_useful)\n \
    - This pull request is __not a duplicate__, so this comment was __not useful__. [check]("+survey_url+"notDup_notUseful)\n \
    - I do not need this service, so this comment was __not useful__. [check]("+survey_url+"stopBother)\n\n"

    body += "This bot is currently in its alpha stage, and we are only sending at most one comment per repository. If you are interested in using our bot in the future, please \
   [subscribe](http://forks-insight.com/INTRUDE-subscribe). If you would like to learn more, see our [web page](http://forks-insight.com/INTRUDE-welcome)."
    data = {"body":  body}


    r = requests.post(url, json.dumps(data), headers=headers)
    if r.status_code == 201:
        print('Successfully created comment "%s"' % body)
        return 'success'
    else:
        print('Could not create comment "%s"' % body)
        print('Response:', r.content)
        return 'fail'
