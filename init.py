
import platform
import os

if (platform.system() == 'Windows'):
    LOCAL_DATA_PATH = 'C:\\Users\\annik\\Documents\\REUSE\\INTRUDE\\PR_data'  # backslashes are escape characters, so doubles are needed
    experiment_param_filePath = '.\\data\\test_repo_list.txt'
    PR_pairList_filePath_prefix = '.\\data\\consecutive_PR_pairs_'
    repos = [line.rstrip('\n') for line in open(".\\data\\test_repo_list.txt")]
    dupPR_result_filePath_prefix = '.\\data\\dupPR_'
else:
    if (platform.system() == 'Linux'):
        LOCAL_DATA_PATH = '/DATA/luyao'
    else:
        LOCAL_DATA_PATH = '/Users/shuruiz/Work/researchProjects'
    # monitored_repoList_filePath = 'data/test_repo_list.txt'
    PR_pairList_filePath_prefix = 'data/consecutive_PR_pairs_'
    # PR_candidate_List_filePath_prefix = 'data/candidate_PR_'
    PR_candidate_List_filePath_prefix = LOCAL_DATA_PATH +'/PRCandidate/candidate_PR_'
    dupPR_result_filePath_prefix = LOCAL_DATA_PATH + '/dupPR/'
    local_pr_data_dir = LOCAL_DATA_PATH + '/pr_data/'

    numPRperPage = 100
    model_saved_path = LOCAL_DATA_PATH + '/INTRUDE_classifier/saved_model.pkl'

    # testing & training dataset
    data_folder = 'data/clf'
    dataset = [
        [data_folder + '/first_msr_pairs.txt', 1, 'train'],
        [data_folder + '/second_msr_pairs.txt', 1, 'test'],
        #     [data_folder + '/first_nondup.txt', 0, 'train'],
        #     [data_folder + '/second_nondup.txt', 0, 'test'], # model 0
        #     [data_folder + '/testSet_Model1.txt', 0, 'test'], #model 1
        #     [data_folder + '/testSet_Model2.txt', 0, 'test'],  #model 2

        ### consequtive non dup pr pairs
        [data_folder + '/latest_NonDupPR_training.txt', 0, 'train'],
        [data_folder + '/latest_NonDupPR_testing.txt', 0, 'test'],
    ]
    currentDIR = os.path.dirname(os.path.realpath(__file__))
    trainModelRepoList = []
    with open(currentDIR+'/data/msr_repo_list.txt') as f:
        trainModelRepoList = f.read().splitlines()
    model_dir = currentDIR + '/NLPmodel/'
pr_date_difference_inDays= 2
comparePRs_timeWindow_inDays= 9999 #todo for bot == 60 days
FilterOutNonCodeFile_flag = True
mysqlParam = "./input/mysqlParams.txt"

# print('monitored_repoList_filePath:' + monitored_repoList_filePath)
# print('LOCAL_DATA_PATH:' + LOCAL_DATA_PATH)
# print('PR_candidate_List_filePath_prefix:' + PR_candidate_List_filePath_prefix)


