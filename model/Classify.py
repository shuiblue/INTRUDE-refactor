from sklearn import svm
from sklearn.linear_model import LogisticRegression
from sklearn import linear_model
from sklearn.ensemble import *
from sklearn.metrics import *
from sklearn.model_selection import cross_val_score
from sklearn.externals import joblib
import matplotlib.pyplot as plt
import init

dir = '/Users/shuruiz/Work/INTRUDE-refactor/data/clf/compress/'
dump_model_flag = True
draw_pic = True  # draw PR curve
draw_roc = True  # draw ROC curve
default_model = 'boost'  # default model: AdaBoost


X_train, y_train = [], []
filelist = ['first_msr_pairs_feature_vector_X_and_Y.txt', 'nondup-train-final.txt']
for file in filelist:
    with open(dir + file) as fp:
        line = fp.readline()
        while line:
            label = int(line.split('[', 1)[1].split(']')[1].strip())
            y_train.append(label)
            # y_train += label
            pr_pair = line.split('[', 1)[0]
            featurelist = line.split('[', 1)[1].split(']')[0].split(', ')
            X_train.append(featurelist)
            line = fp.readline()

X_test, y_test = [], []
filelist = ['second_msr_pairs_feature_vector_X_and_Y.txt', 'nondup-test-final.txt']
for file in filelist:
    with open(dir + file) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            # print("Line {}: {}".format(cnt, line.strip()))
            label = int(line.split('[', 1)[1].split(']')[1].strip())
            # y_test += label
            y_test.append(label)
            pr_pair = line.split('[', 1)[0]
            featurelist = line.split('[', 1)[1].split(']')[0].split(', ')
            X_test.append(featurelist)
            # print(len(featurelist))
            line = fp.readline()
            cnt += 1




# Train a classification model
def train_model(model_type=default_model):
    print('--------------------------')
    print('Size of Dataset: training_set', len(X_train), 'testing_set', len(X_test), 'feature_length=', len(X_train[0]))
    # X_train_aug = X_train
    # y_train_aug = y_train
    # X_train_aug += [t[0] for t in s if t[1]==1] * 5
    # y_train_aug += [1 for t in s if t[1]==1] * 5

    # model choice

    # clf = GradientBoostingClassifier(n_estimators=160, learning_rate=1.0, max_depth=15, random_state=0).fit(X_train, y_train)
    # clf = AdaBoostClassifier(n_estimators=60).fit(X_train, y_train)
    # clf =  DecisionTreeClassifier(max_depth=50)

    print('------ model: ', model_type, '------')
    if model_type == 'SVM':
        clf = svm.SVC(random_state=0, probability=1)
    elif model_type == 'LogisticRegression':
        clf = LogisticRegression()
    elif model_type == 'SGDClassifier':
        clf = linear_model.SGDClassifier(tol=0.01)
    elif model_type == 'boost':
        # clf = AdaBoostClassifier(n_estimators=200, learning_rate=0.1).fit(X_train, y_train)
        # clf = AdaBoostClassifier(base_estimator=DecisionTreeClassifier(max_depth=5), n_estimators=100, learning_rate=0.01).fit(X_train, y_train)
        # sm = SMOTE(random_state=42, k_neighbors=15, kind = 'svm')
        # X_res, y_res = sm.fit_resample(X_train, y_train)
        for n_est in [1300]: # tried 100-1700
            for m_d in [3]: # tried 2-8
                clf = GradientBoostingClassifier(n_estimators=n_est, learning_rate=0.01, max_depth=m_d, random_state=0)
                # clf = RUSBoostClassifier(random_state=0, n_estimators=250, learning_rate=0.01)
                s = sorted(zip(X_train, y_train), reverse=True)

                scores = cross_val_score(clf, X_train, y_train, cv=5)
                print("n_estimators:", n_est, "max_depth:", m_d)
                print(scores.mean())

                clf = clf.fit(X_train, y_train)

                # Predict
                acc = clf.score(X_test, y_test)
                print('Mean Accuracy:', acc)

                y_score = clf.decision_function(X_test)
                average_precision = average_precision_score(y_test, y_score)
                print('Average precision score: {0:0.4f}'.format(average_precision))

                f1_s = f1_score(y_test, clf.predict(X_test))
                print('F1 score: {0:0.4f}'.format(f1_s))

                print(acc, average_precision, f1_s, sep='\t')

                # print('load existing model')
                # # clf_load = joblib.load('filename.pkl')
                # clf_load = joblib.load(init.model_saved_path)
                #
                # # Check that the loaded model is the same as the original
                # print(clf_load.score(X_test, y_test))

                if dump_model_flag:
                    joblib.dump(clf, init.model_saved_path.replace("saved_model", "saved_model20191213"))
                if draw_pic:
                    # draw the PR-curve
                    precision, recall, _ = precision_recall_curve(y_test, y_score)

                    plt.step(recall, precision, color='b', alpha=0.1, where='post')
                    plt.fill_between(recall, precision, step='post', alpha=0.1, color='b')

                    plt.xlabel('Recall')
                    plt.ylabel('Precision')
                    plt.ylim([0.0, 1.05])
                    plt.xlim([0.0, 1.0])
                    plt.title('Precision-Recall curve')

                if draw_roc:
                    # Compute ROC curve and ROC area for each class
                    fpr, tpr, _ = roc_curve(y_test, y_score)
                    roc_auc = auc(fpr, tpr)

                    plt.figure()

                    plt.plot(fpr, tpr, color='darkorange',
                             lw=2, label='ROC curve (area = %0.5f)' % roc_auc)

                    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
                    plt.xlim([0.0, 1.0])
                    plt.ylim([0.0, 1.05])
                    plt.xlabel('False Positive Rate')
                    plt.ylabel('True Positive Rate')
                    plt.title('Receiver operating characteristic example')
                    plt.legend(loc="lower right")
                    plt.show()

    '''
    threshold = 0.5
    y_pred_proba = clf.predict_proba(X_test)
    t_acc, t_tot = 0, 0
    t_rec, t_rec_tot = 0, 0
    t_pre, t_pre_tot = 0, 0
    for i in range(len(y_test)):
        if y_pred_proba[i][1] >= threshold:
            y_threshold_score = 1
        else:
            y_threshold_score = 0

        t_tot += 1
        if y_threshold_score == y_test[i]:
            t_acc += 1

        if y_test[i] == 1:
            t_rec_tot += 1
            if y_threshold_score == 1:
                t_rec += 1
        if y_threshold_score == 1:
            t_pre_tot += 1
            if y_test[i] == 1:
                t_pre += 1

    print('threshold acc =', 1.0 * t_acc / t_tot)
    print('threshold re-call =', 1.0 * t_rec / t_rec_tot)
    print('threshold precision =', 1.0 * t_pre / t_pre_tot)
    '''

    # model result
    # print('coef in model = ', clf.coef_)
    # print(clf.intercept_)
    # print(clf.loss_function_)

    # retrain
    # y_train_score = clf.decision_function(X_train)
    # s = sorted(zip(y_train_score, X_train, y_train), reverse=True)
    # X_train_new = [t[1] for t in s[:int(len(s)/10)]]
    # y_train_new = [t[2] for t in s[:int(len(s)/10)]]
    # X_train_new += [t[1] for t in s if t[2]==1]
    # y_train_new += [1 for t in s if t[2]==1]

    # clf = clf.fit(X_train_new, y_train_new)

    # save the model to disk

    return clf


if __name__ == "__main__":
    # if not path.exists(init.model_saved_path):
    # print('retrain the model')
    clf = train_model()
