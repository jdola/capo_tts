import pickle
import os
import re
from g2p_en import G2p

from . import symbols

from .english_utils.abbreviations import expand_abbreviations
from .english_utils.time_norm import expand_time_english
from .english_utils.number_norm import normalize_numbers
from .japanese import distribute_phone

from transformers import AutoTokenizer

current_file_path = os.path.dirname(__file__)
TGL_FIL_DICT_PATH = os.path.join(current_file_path, "language_cmudict/tgl_fil_phones.csv")
TGL_ENG_DICT_PATH = os.path.join(current_file_path, "language_cmudict/tgl_eng_phones.csv")
CACHE_PATH = os.path.join(current_file_path, "language_cmudict/tgl_cache.pickle")
_g2p = G2p()

def post_replace_ph(ph):
    rep_map = {
        "：": ",",
        "；": ",",
        "，": ",",
        "。": ".",
        "！": "!",
        "？": "?",
        "\n": ".",
        "·": ",",
        "、": ",",
        "...": "…",
        "v": "V",
    }
    if ph in rep_map.keys():
        ph = rep_map[ph]
    if ph in symbols:
        return ph
    if ph not in symbols:
        ph = "UNK"
    return ph


def read_dict():
    g2p_dict = {}
    for cmu_dict_path in [TGL_FIL_DICT_PATH, TGL_ENG_DICT_PATH]:
        with open(cmu_dict_path) as f:
            line = f.readline()
            while line:
                line = line.strip()
                word, phones = line.split("|")
                g2p_dict[word] = [phones.split(" ")]
                line = f.readline()

    return g2p_dict


def cache_dict(g2p_dict, file_path):
    with open(file_path, "wb") as pickle_file:
        pickle.dump(g2p_dict, pickle_file)


def get_dict():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "rb") as pickle_file:
            g2p_dict = pickle.load(pickle_file)
    else:
        g2p_dict = read_dict()
        cache_dict(g2p_dict, CACHE_PATH)

    return g2p_dict


tgl_dict = get_dict()


def refine_ph(phn):
    tone = 0
    return phn.lower(), tone


def refine_syllables(syllables):
    tones = []
    phonemes = []
    for phn_list in syllables:
        for i in range(len(phn_list)):
            phn = phn_list[i]
            phn, tone = refine_ph(phn)
            phonemes.append(phn)
            tones.append(tone)
    return phonemes, tones


def text_normalize(text):
    text = text.lower()
    text = expand_time_english(text)
    text = normalize_numbers(text)
    text = expand_abbreviations(text)
    return text

# model_id = 'bert-base-uncased'
model_id = 'google-bert/bert-base-multilingual-cased'
tokenizer = AutoTokenizer.from_pretrained(model_id)

def g2p(text, pad_start_end=True, tokenized=None):
    if tokenized is None:
        tokenized = tokenizer.tokenize(text)
    # import pdb; pdb.set_trace()
    phs = []
    ph_groups = []
    for t in tokenized:
        if not t.startswith("#"):
            ph_groups.append([t])
        else:
            ph_groups[-1].append(t.replace("#", ""))
    
    phones = []
    tones = []
    word2ph = []
    for group in ph_groups:
        w = "".join(group)
        phone_len = 0
        word_len = len(group)
        print(w)
        if w.lower() in tgl_dict:
            phns, tns = refine_syllables(tgl_dict[w.lower()])
            phones += phns
            tones += tns
            phone_len += len(phns)
        else:
            phone_list = list(filter(lambda p: p != " ", _g2p(w)))
            for ph in phone_list:
                phones.append(ph)
                tones.append(0)
                phone_len += 1
        aaa = distribute_phone(phone_len, word_len)
        word2ph += aaa
    phones = [post_replace_ph(i) for i in phones]

    if pad_start_end:
        phones = ["_"] + phones + ["_"]
        tones = [0] + tones + [0]
        word2ph = [1] + word2ph + [1]
    return phones, tones, word2ph

def get_bert_feature(text, word2ph, device=None):
    from text import tagalog_bert

    return tagalog_bert.get_bert_feature(text, word2ph, device=device)

if __name__ == "__main__":
    # print(get_dict())
    # print(eng_word_to_phoneme("hello"))
    from text.tagalog_bert import get_bert_feature
    text = "In this paper, we propose 1 DSPGAN, a N-F-T GAN-based universal vocoder."
    text = text_normalize(text)
    phones, tones, word2ph = g2p(text)
    import pdb; pdb.set_trace()
    bert = get_bert_feature(text, word2ph)
    
    print(phones, tones, word2ph, bert.shape)

    # all_phones = set()
    # for k, syllables in tgl_dict.items():
    #     for group in syllables:
    #         for ph in group:
    #             all_phones.add(ph)
    # print(all_phones)
