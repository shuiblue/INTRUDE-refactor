import os
import re
import nltk
import itertools
import time
from collections import Counter
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
from util import fileIO
import json
from util import language_tool
from util import localfile

stemmer = PorterStemmer()
# nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


def word_split_by_char(s, flag=None):
    """ split the word by some separators
        Args:
            Word
        Returns:
            List of the split words
    """
    # return [s]

    old_words = []
    old_words.append(s)
    result = []
    while len(old_words) > 0:
        new_words = []
        for s in old_words:
            if len(s) > 1:
                result.append(s)
                if '-' in s:  # Case: ab-cd-ef
                    s = re.sub(r"[-]+", "-", s)
                    new_words += s.split('-')
                elif '.' in s:  # Case: ab.cd.ef
                    s = re.sub(r"[.]+", ".", s)
                    new_words += s.split('.')
                elif '_' in s:  # Case: ab_cd_ef
                    s = re.sub(r"[_]+", "_", s)
                    new_words += s.split('_')
                elif '/' in s:  # Case: ab/cd/ef
                    s = re.sub(r"[/]+", "/", s)
                    if len(s.split('/')) < 3:
                        new_words += s.split('/')
                elif '\\' in s:  # Case: ab\cd\ef
                    s = re.sub(r"[\\]+", "/", s)
                    if len(s.split('/')) < 3:
                        new_words += s.split('/')
                else:
                    t = camel_case_split(s)
                    if len(t) > 1:
                        new_words += t
        if flag == 'bigrams':
            bigrams_list_init = zip(*[new_words[i:] for i in range(2)])
            bigrams_list = ["~".join(ngram) for ngram in bigrams_list_init]
            new_words += bigrams_list
        old_words = new_words
    return result


# def filter_common_words_in_pr(tokens):
#    return list(filter(lambda x: x not in language_tool.get_common_words_in_pr(), tokens))

def stem_process(tokens):
    # Do stem on the tokens.
    for try_times in range(3):
        try:
            result = [stemmer.stem(word) for word in tokens]
            return result
        except Exception as ex:
            print(ex)
            time.sleep(5)
    return tokens


def lemmatize_process(tokens):
    for try_times in range(3):  # NLTK is not thread-safe, use simple retry to fix it.
        try:
            result = [lemmatizer.lemmatize(word) for word in tokens]
        except Exception as ex:
            print(ex)
            time.sleep(5)
    return tokens


def move_other_char(text):
    return re.sub("[^0-9A-Za-z_]", "", text)


def token_filtering(tokens, file=None):
    tokens = list(filter(lambda x: re.search(r"[0-9A-Za-z_./\\\-]", x), tokens))
    newtokens = []
    for t in tokens:
        t = re.sub(r"^[_\\/\-.]+", "", t)
        t = re.sub(r"[_\\/\-.]+$", "", t)
        t = re.sub(r"\d+", "", t)
        if len(t) > 1:
            newtokens.append(t)
    newtokens = list(filter(lambda x: len(x) >= 2, newtokens))
    if (file is not None) and (not language_tool.is_text(file)):
        newtokens = list(filter(lambda x: x not in language_tool.PL_reserved_words, newtokens))
    newtokens = [x.lower() for x in newtokens]
    tokens = list(filter(lambda x: x not in language_tool.general_stopwords, newtokens))
    return tokens

def filteringText(text,outfile_prefix):
    # handle url
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]| [! * \(\),] | (?: %[0-9a-fA-F][0-9a-fA-F]))+'
    url_list = re.findall(url_regex, text)
    fileIO.writeListToFile(url_list, outfile_prefix + "/url_list.tsv")
    # remove url
    text = re.sub(url_regex, ' ', text)

    text = re.sub('\\\\u[0-9A-Fa-f]{4}', '', text)
    text = re.sub('\\\\x[0-9A-Fa-f]{2}', '', text)
    text = re.sub('\\\\[n|t]', ' ', text)
    text = re.sub(r"[^0-9A-Za-z_./\\\-]", ' ', text)
    return text

def get_code_tokens_from_file(filelist_json, outfile_prefix, category=None, bigram_flag=True):
    data = {}
    data['file'] = []
    for f_json in filelist_json:

        file = f_json["name"]
        # ignore non code file
        if language_tool.is_text(file):
            continue
        # print(file)
        # ignore file if the change is too big
        # if f_json['LOC']['add'] > 10000 or (f_json['LOC']['add'] < 5 and len(f_json['add_code']) > 10000):
        if (f_json['LOC']['add'] < 5 and len(f_json['add_code']) > 10000):
            print('code change in current file is too long, skip')
            continue

        text = f_json[category]

        text = filteringText(text,outfile_prefix)

        tokens = nltk.word_tokenize(text)

        # generate an array of bigrams
        filtered_tokens = token_filtering(tokens, file)
        if bigram_flag:
            bigram_tokens = list(itertools.chain(*[word_split_by_char(token, 'bigrams') for token in filtered_tokens]))
            bigram_tokens = token_filtering(bigram_tokens, file)
            stem_bigrams_tokens = stem_process(bigram_tokens)

        tokens = list(itertools.chain(*[word_split_by_char(token) for token in filtered_tokens]))
        stem_tokens = stem_process(tokens)

        if bigram_tokens:
            data['file'].append({
                'filename': file,
                # 'bigram_tokens':'\t'.join(bigram_tokens),
                'stem_bigram_tokens': '\t'.join(stem_bigrams_tokens),
                # 'tokens':'\t'.join(tokens),
                'stem_tokens': '\t'.join(stem_tokens)
            })
        else:
            data['file'].append({
                'filename': file,
                # 'tokens': '\t'.join(tokens),
                'stem_tokens': '\t'.join(stem_tokens)
            })
    with open(outfile_prefix + "/" + category + ".json", 'w+') as outfile:
        json.dump(data, outfile)


def get_tokens_from_file(text, outfile_prefix, category=None, bigram_flag=True):
    """
        Args:
            file: file full name
            text: the raw text of the file
        Returns:
            A list of the tokens of the result of the participle. 
    """
    if (text is None):
        return []

    text = filteringText(text, outfile_prefix)
    tokens = nltk.word_tokenize(text)

    # generate an array of bigrams
    filtered_tokens = token_filtering(tokens)
    if bigram_flag:
        bigram_tokens = list(itertools.chain(*[word_split_by_char(token, 'bigrams') for token in filtered_tokens]))
        # fileIO.writeListToFile(bigram_tokens, outfile_prefix + "/" + category + "_bigrams_tokens.tsv")
        stem_bigrams_tokens = stem_process(bigram_tokens)
        fileIO.writeListToFile(stem_bigrams_tokens, outfile_prefix + "/" + category + "_bigrams_tokens_stemmed.tsv")

    tokens = list(itertools.chain(*[word_split_by_char(token) for token in filtered_tokens]))
    # fileIO.writeListToFile(tokens, outfile_prefix + "/" + category + "_tokens.tsv")
    stem_tokens = stem_process(tokens)
    fileIO.writeListToFile(stem_tokens, outfile_prefix + "/" + category + "_tokens_stemmed.tsv")

    # tokens.extend(list(itertools.chain(*[word_split_by_char(token) for token in origin_tokens]))) # Keep original tokens
    # lemmatize_process
    # lemmatize_tokens = lemmatize_process(tokens)

    # stemmed_tokens = [PorterStemmer().stem(word) for word in tokens] # do stem on the tokens
    # if bigram_flag:
    #     return stem_bigrams_tokens
    # else:
    #     return stem_tokens


def get_words_from_text(text, outfile_prefix):
    return get_tokens_from_file(text, outfile_prefix, 'title_body')


def get_version_number(repo, pull_text):
    nums = [''.join(x) for x in re.findall('(\d+\.)?(\d+\.)(\d+)', pull_text)]
    if repo == 'edx/edx-platform':  # https://github.com/edx/edx-platform/pulls
        nums = [''.join(x) for x in re.findall(r'(BOM-\d+)', pull_text)]
    nums = list(set(nums))
    return nums


def getIssueReference(pull_text):
    nums = []
    nums += re.findall('#([0-9]+)', pull_text)
    nums += re.findall('pull/([0-9]+)', pull_text)
    nums += re.findall('issues?/([0-9]+)', pull_text)
    nums = list(filter(lambda x: len(x) > 0, nums))
    nums = list(set(nums))
    return nums


def getSHA(pull_text):
    SHAs = []
    SHAs += re.findall("\\b[0-9a-f]{7} |\\b[0-9a-f]{40}\\b", pull_text)
    return SHAs


def get_counter(tokens):
    tokens = filter(lambda x: x is not None, tokens)
    return Counter(tokens)


def get_top_words(tokens, top_number, list_option=True):
    if tokens is None:
        return None
    counter = get_counter(tokens).most_common(top_number)
    if list_option:
        return [x for x, y in counter]
    else:
        return dict([(x, y) for x, y in counter])


def get_top_words_from_text(text, top_number=10):
    return get_top_words(get_words_from_text(text), top_number)


def _removeNonAscii(s):
    return "".join(i for i in s if ord(i) < 128)

def getTextTokenInFile(filepath):
    tokens = []
    if os.path.exists(filepath):
        with open(filepath) as tsv:
            tokens_perPR = [line.strip().split('\t') for line in tsv]
            for t in tokens_perPR:
                tokens.extend(t)
    return tokens

if __name__ == "__main__":
    s =   "VCINSTALLDIR_SERVO C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\BuildTools\\VC\\",
    t =  'xxxx C:\\Program Files (x86)\\Windows Kits\\10\\'
    s = re.sub(r"[\\]+", '/', s)
    t = re.sub(r"[\\]+", '/', t)
    u = re.sub('^[a-zA-Z]:/(((?![<>:"/|?*]).)+((?<![ .])/)?)*$', ' ', s)
    w = re.sub('^[a-zA-Z]:/(((?![<>:"/|?*]).)+((?<![ .])/)?)*$', ' ', t)

    print()
