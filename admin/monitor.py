from datetime import datetime, timedelta
import schedule
import time
import mysql.connector
import platform
import github.github_api
from flask import Flask, redirect, request, render_template
import os
import csv
import backend_interface

pr2_created_at_index = 2
##### feature list 33 in total ########
similarity_final = 4
title_lsi = 5
title_tfidf = 6
body_lsi = 7
body_tfidf = 8
commit_lsi = 9
commit_tfidf = 10
pr1_add_files = 11
pr2_add_files = 12
pr1_delete_files = 13
pr2_delete_files = 14
add_files_sim = 15
delet_files_sim = 16
add_filenames_sim = 17
delet_filenames_sim = 18
code_sim_addCode_lsi = 19
code_sim_addCode_lsi_overlap_filepath = 20
code_sim_addCode_lsi_same_filename = 21
code_sim_addCode_tfidf_add = 22
code_sim_addCode_tfidf_overlap_filepath = 23
code_sim_addCode_tfidf_same_filename = 24
code_sim_deleteCode_lsi = 25
code_sim_deleteCode_lsi_overlap_filepath = 26
code_sim_deleteCodelsi_same_filename = 27
code_sim_deleteCode_tfidf_add = 28
code_sim_deleteCode_tfidf_overlap_filepath = 29
code_sim_deleteCodetfidf_same_filename = 30
location_similarity_allfile = 31
location_similarity_overlapfile = 32
timeInterval = 33
ref_version = 34
ref_issue = 35
ref_SHA = 36
ref_url = 37
#############

api = github.github_api.GitHubAPI()
app = Flask(__name__)
htmlpage_url = 'interface.html'

# Connect to MySQL database
with open('./input/mysqlParams.txt') as f:
# with open('../input/mysqlParams.txt') as f:
    MYSQL_USER, MYSQL_PASS, MYSQL_HOST, PORT = f.read().splitlines()
# conn = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASS, host=MYSQL_HOST, database='repolist', port='3306')
conn = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASS, host=MYSQL_HOST, database='fork', port=PORT)
cur = conn.cursor()
# Create flag for showing all PR pairs vs one per repo
show_hide = 'hide'

def updateResult():
    exe_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    print(exe_time + " check again ... ")
    if platform.system() == 'Windows':
        path = 'C:\\Users\\annik\\Documents\\REUSE\\interface\\dupPR'
    elif platform.system() == 'Linux':
        path = '/DATA/luyao/dupPR'
    else:
        path = '/Users/shuruiz/Work/ForkData/INTRUDE'
        # for every file (repository) in the dupPR directory
    for dir_name in os.listdir(path):

        # print(dir_name)
        # find path to this file
        filepath = path
        if platform.system() == 'Windows':
            filepath += '\\'
        else:
            filepath += '/'
        filepath += dir_name
        if not os.path.isdir(filepath):
            # print("not dir " + filepath)
            continue
        record_date = datetime.strptime(dir_name, '%Y-%m-%d')
        if ((datetime.now() - record_date).days > 2):
            # print(str(record_date) + "is older than 2 days, skip")
            continue

        for repoPRlist in os.listdir(filepath):
            # print(repoPRlist)
            repo_filepath = filepath + "/" + repoPRlist
            # open this file
            with open(repo_filepath) as tsv:
                # for every line (PR pair) in the current file
                for line in csv.reader(tsv, delimiter="\t"):
                    repoURL = line[0]
                    PR1 = line[1]
                    PR2 = line[3]
                    # check whether this pr pair has already been added to the db:
                    flag = 0
                    # searchCurrentPRPari_sql = "SELECT * FROM duppr_pair where repo = '" + repoURL + "' and PR1 = " + PR1 + " AND PR2 = " + PR2
                    searchCurrentPRPari_sql = "SELECT * FROM duppr_pair_update where repo = '" + repoURL + "' and PR1 = " + PR1 + " AND PR2 = " + PR2
                    # print(searchCurrentPRPari_sql)
                    cur.execute(searchCurrentPRPari_sql)
                    check = cur.fetchall()
                    if (len(check) > 0):
                        flag = 1

                    if (flag == 0):
                        pr_pair_tuple = (
                            repoURL, int(PR1, 10), int(PR2, 10), float(line[similarity_final]), float(line[title_lsi]), \
                            float(line[title_tfidf]), float(line[body_lsi]), float(line[body_tfidf]),
                            float(line[commit_lsi]), float(line[commit_tfidf]), \
                            float(line[pr1_add_files]), float(line[pr2_add_files]), float(line[pr1_delete_files]),
                            float(line[pr2_delete_files]), float(line[add_files_sim]), float(line[delet_files_sim]),
                            float(line[add_filenames_sim]), float(line[delet_filenames_sim]), \
                            float(line[code_sim_addCode_lsi]), float(line[code_sim_addCode_lsi_overlap_filepath]),
                            float(line[code_sim_addCode_lsi_same_filename]), float(line[code_sim_addCode_tfidf_add]),
                            float(line[code_sim_addCode_tfidf_overlap_filepath]), \
                            float(line[code_sim_addCode_tfidf_same_filename]), float(line[code_sim_deleteCode_lsi]),
                            float(line[code_sim_deleteCode_lsi_overlap_filepath]),
                            float(line[code_sim_deleteCodelsi_same_filename]),
                            float(line[code_sim_deleteCode_tfidf_add]), \
                            float(line[code_sim_deleteCode_tfidf_overlap_filepath]),
                            float(line[code_sim_deleteCodetfidf_same_filename]),
                            float(line[location_similarity_allfile]), float(line[location_similarity_allfile]),
                            float(line[timeInterval]), \
                            float(line[ref_version]), float(line[ref_issue]), float(line[ref_SHA]),
                            float(line[ref_url]), line[pr2_created_at_index])
                        cur.execute('INSERT INTO duppr_pair_update(repo, pr1, pr2, score, title_lsi,\
                                                                       title_tfidf, body_lsi, body_tfidf, commit_lsi, commit_tfidf,\
                                                                       pr1_add_files, pr2_add_files, pr1_delete_files, pr2_delete_files, add_files_sim,\
                                                                       delet_files_sim, add_filenames_sim, delet_filenames_sim, code_sim_addCode_lsi, code_sim_addCode_lsi_overlap_filepath,\
                                                                       code_sim_addCode_lsi_same_filename, code_sim_addCode_tfidf_add, code_sim_addCode_tfidf_overlap_filepath, code_sim_addCode_tfidf_same_filename, code_sim_deleteCode_lsi,\
                                                                       code_sim_deleteCode_lsi_overlap_filepath, code_sim_deleteCodelsi_same_filename, code_sim_deleteCode_tfidf_add, code_sim_deleteCode_tfidf_overlap_filepath, code_sim_deleteCodetfidf_same_filename, \
                                                                       location_similarity_allfile, location_similarity_overlapfile, timeInterval, ref_version, ref_issue,\
                                                                        ref_SHA, ref_url, timestamp) \
                                                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\
                                                              %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\
                                                              %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\
                                                              %s,%s,%s,%s,%s,%s,%s,%s)',
                                    pr_pair_tuple)

                    else:
                        pr_pair_update_tuple = (
                            float(line[similarity_final]), float(line[title_lsi]), \
                            float(line[title_tfidf]), float(line[body_lsi]), float(line[body_tfidf]),
                            float(line[commit_lsi]), float(line[commit_tfidf]), \
                            float(line[pr1_add_files]), float(line[pr2_add_files]), float(line[pr1_delete_files]),
                            float(line[pr2_delete_files]), float(line[add_files_sim]), \
                            float(line[delet_files_sim]), float(line[add_filenames_sim]),
                            float(line[delet_filenames_sim]), float(line[code_sim_addCode_lsi]),
                            float(line[code_sim_addCode_lsi_overlap_filepath]), \
                            float(line[code_sim_addCode_lsi_same_filename]), float(line[code_sim_addCode_tfidf_add]),
                            float(line[code_sim_addCode_tfidf_overlap_filepath]),
                            float(line[code_sim_addCode_tfidf_same_filename]), float(line[code_sim_deleteCode_lsi]), \
                            float(line[code_sim_deleteCode_lsi_overlap_filepath]),
                            float(line[code_sim_deleteCodelsi_same_filename]),
                            float(line[code_sim_deleteCode_tfidf_add]),
                            float(line[code_sim_deleteCode_tfidf_overlap_filepath]),
                            float(line[code_sim_deleteCodetfidf_same_filename]), \
                            float(line[location_similarity_allfile]), float(line[location_similarity_allfile]),
                            float(line[timeInterval]), float(line[ref_version]), float(line[ref_issue]), \
                            float(line[ref_SHA]), float(line[ref_url]), line[pr2_created_at_index], repoURL,
                            int(PR1, 10), int(PR2, 10))

                        # update_sql = "UPDATE duppr_pair \
                        #               set score = %s, title = %s, description = %s, patch_content = %s, patch_content_overlap = %s, \
                        #                   changed_file = %s, changed_file_overlap = %s, location = %s, location_overlap = %s, issue_number = %s, \
                        #                   commit_message= %s, timestamp = %s  \
                        #               where repo = %s and pr1 = %s and pr2 = %s"
                        update_sql = "UPDATE duppr_pair_update \
                                         set score = %s, title_lsi = %s, \
                                         title_tfidf = %s, body_lsi = %s, body_tfidf = %s, commit_lsi = %s, commit_tfidf = %s, \
                                         pr1_add_files = %s, pr2_add_files = %s, pr1_delete_files = %s, pr2_delete_files = %s, add_files_sim = %s, \
                                         delet_files_sim = %s, add_filenames_sim = %s, delet_filenames_sim = %s, code_sim_addCode_lsi = %s, code_sim_addCode_lsi_overlap_filepath = %s, \
                                         code_sim_addCode_lsi_same_filename = %s, code_sim_addCode_tfidf_add = %s, code_sim_addCode_tfidf_overlap_filepath = %s, code_sim_addCode_tfidf_same_filename = %s, code_sim_deleteCode_lsi = %s,\
                                         code_sim_deleteCode_lsi_overlap_filepath = %s,  code_sim_deleteCodelsi_same_filename = %s, code_sim_deleteCode_tfidf_add = %s, code_sim_deleteCode_tfidf_overlap_filepath = %s, code_sim_deleteCodetfidf_same_filename = %s,\
                                         location_similarity_allfile = %s, location_similarity_overlapfile = %s, timeInterval = %s, ref_version = %s, ref_issue = %s,\
                                         ref_SHA = %s, ref_url = %s, timestamp = %s   \
                                         where repo = %s and pr1 = %s and pr2 = %s"
                        cur.execute(update_sql, pr_pair_update_tuple)

                    conn.commit()
    print('update pr states...')
    updatePRstate()

    threshold = '0.9'
    print("find pr pairs similar score is higher than "+ threshold)
    idlist = top_pair_similarityBiggerThanThreshold_unMarked(threshold)

    print("send email..")
    result_list = []
    if (len(idlist)>0):
        notify_admin(str(len(idlist)))
        for id in idlist:
            list.append(str(id[0]))

        idlist_str = "(" + ', '.join(map(str, result_list)) + ")"
        markEmailedResultToDB(idlist_str)
        print("update " + str(len(idlist_str)) + "in database")
    else:
        print("no new duplicate pr found... wait...")

def markEmailedResultToDB(idlist):
    sql_str =  "UPDATE duppr_pair_update set notify_admin = True where id in "+ idlist
    print(sql_str)
    cur.execute(sql_str)
    conn.commit()

def notify_admin(num_newPRpairs):
    cmd_str ="echo \" detect "+ num_newPRpairs +" duplicate PR pairs, please check ASAP at http://128.2.112.25:5000/ :)\" | mail -s \"dupPR_bot: found new pairs\" shuruiz@andrew.cmu.edu"
    print(cmd_str)
    os.system(cmd_str)

def top_pair_similarityBiggerThanThreshold_unMarked(threshold):
    sql_str = "SELECT id \
               FROM duppr_pair_update a\
               WHERE a.repo COLLATE utf8mb4_unicode_ci NOT IN  (SELECT DISTINCT b.repo FROM dupPR_repo b)\
                     AND  (score >" + threshold + ")\
                     AND (notes NOT LIKE '%FP%' OR notes NOT LIKE '%doc%' OR notes IS NULL)\
                     AND TIMESTAMPDIFF(DAY, `timestamp`, CURRENT_TIMESTAMP()) <= 2\
                     AND notify_admin is NULL and checked is Null\
                     AND num_overlapped_participants = 0\
               ORDER BY timestamp DESC;"
    cur.execute(sql_str)
    data_sorted = cur.fetchall()
    conn.commit()  # save changes
    # print(str(len(data_sorted)))


    return data_sorted  # return the sorted list of all pairs


def updatePRstate():
    data = []
    data_dups_update = []
    data_dups = backend_interface.top_pair_featureBiggerThanDotEight()
    for line in data_dups:
        repo, pr1, pr2 = line[1:4]

        # ###  ###  ###  ### get PR state
        pr1_status = api.pr_status(repo, pr1)
        pr2_status = api.pr_status(repo, pr2)

        # ###  ###  ###  ### get PR timeline
        pr1_events = api.get_issue_pr_timeline(repo, pr1)
        pr2_events = api.get_issue_pr_timeline(repo, pr2)
        pr1_participant_list, pr1_num_comments = backend_interface.analyzePREvents(pr1_events)
        pr2_participant_list, pr2_num_comments = backend_interface.analyzePREvents(pr2_events)
        num_participants_overlap = len(pr1_participant_list.intersection(pr2_participant_list))

        # update to db
        backend_interface.update_pr_state_db(repo, pr1, pr2, pr1_status, pr2_status, len(pr1_participant_list), len(pr2_participant_list),
                                             pr1_num_comments, pr2_num_comments, num_participants_overlap)


if __name__ == "__main__":
    exe_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    print(exe_time + " execute... ")
    schedule.every().hour.at(exe_time).do(updateResult)

    while True:
        schedule.run_pending()
        time.sleep(60)