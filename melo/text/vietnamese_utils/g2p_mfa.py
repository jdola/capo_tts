# Copyright (c) 2023 Amphion.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import re
from g2p_en.g2p import G2p
from string import punctuation
import os
import json


def read_lexicon(lex_path):
    lexicon = {}
    with open(lex_path) as f:
        for line in f:
            temp = re.split(r"\s+", line.strip("\n"))
            word = temp[0]
            phones = temp[1:]
            if word.lower() not in lexicon:
                lexicon[word.lower()] = phones
    return lexicon

def preprocess_english(text, lexicon):
    text = text.rstrip(punctuation)

    g2p = G2p()
    phones = []
    words = re.split(r"([,;.\-\?\!\s+])", text)
    for w in words:
        if w.lower() in lexicon:
            phones += lexicon[w.lower()]
        else:
            phones += list(filter(lambda p: p != " ", g2p(w)))
    phones = "}{".join(phones)
    phones = re.sub(r"\{[^\w\s]?\}", "{sp}", phones)
    phones = phones.replace("}{", " ")

    return phones

# VIETNAMESE_MFA_ROOT_PATH = os.getenv("VIETNAMESE_MFA_ROOT_PATH", "/raid/agi-ds/data-sharing/common/models/tts/vn_phoneme")
MFA_G2P_ROOT_PATH = os.getenv("MFA_G2P_ROOT_PATH", "/raid/agi-ds/data-sharing/common/models/tts/g2p_mfa")
def read_mfa_dict_as_lexicon(dict_path, meta_path):
    lexicon = {}
    with open(dict_path) as f:
        for line in f:
            temp = re.split(r"\t", line.strip("\n"))
            word = temp[0]
            phones = temp[-1].split()
            if word.lower() not in lexicon:
                lexicon[word.lower()] = phones
    with open(meta_path) as f:
        meta = json.load(f)
    return lexicon, meta

def preprocess_mfa(text, mfa_name = "vietnamese_ho_chi_minh_city_mfa"):
    text = text.rstrip(punctuation)
    mfa_path = os.path.join(MFA_G2P_ROOT_PATH, mfa_name)
    lexicon, meta = read_mfa_dict_as_lexicon(os.path.join(mfa_path, f"{mfa_name}.dict"), os.path.join(mfa_path, "meta.json"))
    phones = []
    words = re.split(r"([,;.\-\?\!\s+])", text)
    for w in words:
        if w.lower() in lexicon:
            phones += lexicon[w.lower()]
        else:
            phones += list(filter(lambda p: p != " ", preprocess_by_mfa(w, mfa_path)))
    phones = "}{".join(phones)
    phones = re.sub(r"\{[^\w\s]?\}", "{sp}", phones)
    phones = phones.replace("}{", " ")

    return phones