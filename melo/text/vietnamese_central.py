import os
import re

from .vietnamese_utils.g2p import (
    global_vi_phonemizer_central as global_vi_phonemizer,
)
from phonemizer.separator import Separator
from transformers import AutoTokenizer

from . import symbols
from .japanese import distribute_phone
from .vietnamese_utils.number_norm import normalize_numbers_vietnamese
from .vietnamese_utils.time_norm import expand_time_vietnamese

current_file_path = os.path.dirname(__file__)


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


def vnm_g2p(text):
    separator = Separator(phone="|", word=" ")
    global_vi_phonemizer
    phones = global_vi_phonemizer.phonemize([text], strip=True, njobs=1, separator=separator)[0]
    return [x.split("|") for x in phones.split(" ")]


tone_dict = {"no_tone": 0, "ɜ": 1, "2": 2, "4": 3, "5": 4, "6": 5}


def refine_ph(phn):
    match = re.search(r"[ɜ2456]", phn)
    if match:
        tone = tone_dict[match.group()]
        phn = re.sub(r"[ɜ2456]", "", phn)
    else:
        tone = tone_dict["no_tone"]
    return phn.lower(), tone


def refine_syllables(syllables):
    tones = []
    phonemes = []
    for phn_list in syllables:
        for i in range(len(phn_list)):
            phn = phn_list[i]
            if phn == "":
                continue
            phn, tone = refine_ph(phn)
            phonemes.append(phn)
            tones.append(tone)
    return phonemes, tones


def text_normalize(text):
    text = text.lower()
    text = expand_time_vietnamese(text)
    text = normalize_numbers_vietnamese(text)
    # text = expand_abbreviations(text)
    return text


model_id = "google-bert/bert-base-multilingual-cased"
# model_id = 'trituenhantaoio/bert-base-vietnamese-uncased'
tokenizer = AutoTokenizer.from_pretrained(model_id)
# tokenizer = BertTokenizer.from_pretrained(model_id)


def g2p(text, pad_start_end=True, tokenized=None):
    if tokenized is None:
        tokenized = tokenizer.tokenize(text)
    # import pdb; pdb.set_trace()
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
        phns, tns = refine_syllables(vnm_g2p(w.lower()))
        phones += phns
        tones += tns
        phone_len += len(phns)

        aaa = distribute_phone(phone_len, word_len)
        word2ph += aaa
    phones = [post_replace_ph(i) for i in phones]

    if pad_start_end:
        phones = ["_"] + phones + ["_"]
        tones = [0] + tones + [0]
        word2ph = [1] + word2ph + [1]
    return phones, tones, word2ph


if __name__ == "__main__":
    # print(get_dict())
    # print(eng_word_to_phoneme("hello"))
    from text.vietnamese_bert import get_bert_feature

    text = "In this paper, we propose 1 DSPGAN, a N-F-T GAN-based universal vocoder."
    text = text_normalize(text)
    phones, tones, word2ph = g2p(text)
    import pdb

    pdb.set_trace()
    bert = get_bert_feature(text, word2ph)

    print(phones, tones, word2ph, bert.shape)

    # all_phones = set()
    # for k, syllables in eng_dict.items():
    #     for group in syllables:
    #         for ph in group:
    #             all_phones.add(ph)
    # print(all_phones)
