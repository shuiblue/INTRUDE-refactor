import csv
import os, os.path
import errno
def writeListToFile(list,filepath):
    with safe_open_w(filepath) as f_output:
        tsv_output = csv.writer(f_output, delimiter='\t')
        tsv_output.writerow(list)




# Taken from https://stackoverflow.com/a/600612/119527
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    mkdir_p(os.path.dirname(path))
    return open(path, 'w')
