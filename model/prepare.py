from util.localfile import *

part_params = None
text_sim_type = 'lsi'
# text_sim_type = 'tfidf'

code_sim_type = 'tfidf'
# code_sim_type = 'bow'
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

model_data_renew_flag = False

# model save name
model_data_save_path_suffix = 'ok_text_%s_code_%s_%s_%s' % (
    text_sim_type, code_sim_type, extract_sim_type, feature_conf)

''' This function process PR, including
'''
def process_PR:




def model_data_prepare(dataset):
    X_train, y_train = [], []
    X_test, y_test = [], []

    for s in dataset:
        # get feature vector
        new_X, new_y = get_feature_vector(s[0], s[1], model_data_renew_flag, model_data_save_path_suffix)

        if s[2] == 'train':
            X_train += new_X
            y_train += new_y
        elif s[2] == 'test':
            X_test += new_X
            y_test += new_y

    print('--------------------------')
    print('Loading Data')
    X_train, y_train, X_test, y_test = model_data_prepare(dataset)

    if part_params:
        def extract_experiment_param(a, c):
            for i in range(len(a)):
                t = []
                for j in range(len(c)):
                    if c[j] == 1:
                        t.append(a[i][j])
                a[i] = t

        extract_experiment_param(X_train, part_params)
        extract_experiment_param(X_test, part_params)
        print('extract=', part_params)

    print('--------------------------')
    print('Size of Dataset: training_set', len(X_train), 'testing_set', len(X_test), 'feature_length=', len(X_train[0]))
    # X_train_aug = X_train
    return clf

def get_feature_vector(data, label, renew=False, out=None):
    print('Model Data Input=', data)

    default_path = data.replace('.txt', '') + '_feature_vector'
    out = default_path if out is None else default_path + '_' + out
    X_path, y_path = out + '_X.json', out + '_y.json'

    if os.path.exists(X_path) and os.path.exists(y_path) and (not renew):
        print('warning: feature vector already exists!', out)
        X = localfile.get_file(X_path)
        y = localfile.get_file(y_path)
        return X, y

    X, y = [], []

    # run with all PR's info model
    p = {}
    pr_len = 0
    with open(data) as f:
        all_pr = f.readlines()
        pr_len = len(all_pr)
    count = 0

    for l in all_pr:
        print(str(count / pr_len) + ' pr:' + l)
        r, n1, n2 = l.strip().split()

        if 'msr_pairs' not in data:
            # print('check if there are too much texts in the PR description.. such as template..')
            if check_large(get_pull(r, n1)) or check_large(get_pull(r, n2)):
                continue

        if r not in p:
            p[r] = []
        p[r].append((n1, n2, label))
        count = count + 1

    print('all=', len(all_pr))

    out_file = open(out + '_X_and_Y.txt', 'w+')

    for r in p:
        init_model_with_repo(r)

    for r in p:
        print('Start running on', r)

        # init NLP model
        init_model_with_repo(r)

        print('pairs num=', len(p[r]))

        # sequence
        cnt = 0
        for z in p[r]:
            # print(r, z[0], z[1])

            x0, y0 = get_sim(r, z[0], z[1]), z[2]
            X.append(x0)
            y.append(y0)
            print(r, z[0], z[1], x0, y0, file=out_file)

            cnt += 1
            if cnt % 100 == 0:
                print('current:', r, cnt)

    out_file.close()

    # save to local
    localfile.write_to_file(X_path, X)
    localfile.write_to_file(y_path, y)
    return (X, y)


# init NLP model
def init_model_with_pulls(pulls, save_id=None):
    t = [str(pull["title"]) for pull in pulls]
    b = []
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    candidate_pulls = []

    for pull in pulls:
        # if the pr is older than 1 year, ignore
        current_pr_createdAt = pull['created_at']
        if (util.timeUtil.days_between(now, current_pr_createdAt) > init.comparePRs_timeWindow_inDays):
            print(str(pull['number']) + "older than " + str(init.pr_date_difference_inDays) + " days , stop")
            break

        if pull["body"] and (len(pull["body"]) <= 2000):
            b.append(pull["body"])
            candidate_pulls.append(pull)
    init_model_from_raw_docs(t + b, save_id)

    if code_sim_type == 'tfidf':
        c = []
        print(str(len(candidate_pulls)) + " candidate pulls")
        # if (len(candidate_pulls) == 0):
        #     print(str(len(candidate_pulls)) + "candidate pulls, skip")
        #     return
        for pull in candidate_pulls:  # only added code
            # for pull in pulls:  # only added code
            try:
                if not check_large(pull):
                    p = copy.deepcopy(pull)
                    p["file_list"] = fetch_pr_info(p)
                    c.append(get_code_tokens(p)[0])
            except Exception as e:
                print('Error on get', pull['url'])
        # if(len(c) == 0):
        #     print(" no pr available")
        #     return None
        init_code_model_from_tokens(c, save_id + '_code' if save_id is not None else None)

