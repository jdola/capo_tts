import re
from functools import partial

from num2words import num2words

""" from https://github.com/keithito/tacotron """

from typing import Dict

import inflect

_inflect = inflect.engine()
_comma_number_re = re.compile(r"([0-9][0-9\,]+[0-9])")
_currency_re = re.compile(r"(£|\$|¥)([0-9\,\.]*[0-9]+)")
_ordinal_re = re.compile(r"[0-9]+(st|nd|rd|th)")
_number_re = re.compile(r"-?[0-9]+")

_expand_num_regex = r"(?:\s|^)(\d+)(?:[.,](\d+))?(?![.\d])(?!(?:[\/\\_\-\:]))"


def generic_num2word(integer_part, fractional_part, lang, sep, use_as_space=" "):

    words = []
    if integer_part:
        words.append(num2words(int(integer_part), lang=lang))
    if fractional_part:
        words.append(sep)
        if len(fractional_part) == 2 and fractional_part[0] != "0":
            words.append(num2words(int(fractional_part), lang=lang))
        else:
            words.extend(num2words(int(digit), lang=lang) for digit in fractional_part)
        # words.extend(num2words(int(digit), lang=lang) for digit in fractional_part)
    return " ".join([word.replace(" ", use_as_space) for word in words])


def _expand_number(match, lang, sep, use_as_space=" "):
    integer_part = match.group(1)
    fractional_part = match.group(2)
    return " " + generic_num2word(integer_part, fractional_part, lang, sep, use_as_space)


def _expand_vi_number(text, lang="vi", sep="chấm", use_as_space=" "):
    text = re.sub(
        _expand_num_regex,
        partial(_expand_number, lang=lang, sep=sep, use_as_space=use_as_space),
        text,
    )
    return text


def _remove_commas(m):
    return m.group(1).replace(",", "")


def __expand_currency(value: str, inflection: Dict[float, str]) -> str:
    parts = value.replace(",", "").split(".")
    if len(parts) > 2:
        return f"{value} {inflection[2]}"  # Unexpected format
    text = []
    integer = int(parts[0]) if parts[0] else 0
    if integer > 0:
        integer_unit = inflection.get(integer, inflection[2])
        text.append(f"{integer} {integer_unit}")
    fraction = int(parts[1]) if len(parts) > 1 and parts[1] else 0
    if fraction > 0:
        fraction_unit = inflection.get(fraction / 100, inflection[0.02])
        text.append(f"{fraction} {fraction_unit}")
    if len(text) == 0:
        return f"zero {inflection[2]}"
    return " ".join(text)


def _expand_currency(m: "re.Match") -> str:
    currencies = {
        "$": {
            0.01: "cent",
            0.02: "cents",
            1: "dollar",
            2: "dollars",
        },
        "€": {
            0.01: "cent",
            0.02: "cents",
            1: "euro",
            2: "euros",
        },
        "£": {
            0.01: "penny",
            0.02: "pence",
            1: "pound sterling",
            2: "pounds sterling",
        },
        "¥": {
            # TODO rin
            0.02: "sen",
            2: "yen",
        },
    }
    unit = m.group(1)
    currency = currencies[unit]
    value = m.group(2)
    return __expand_currency(value, currency)


def normalize_numbers_vietnamese(text):
    text = re.sub(_comma_number_re, _remove_commas, text)
    text = re.sub(_currency_re, _expand_currency, text)
    text = _expand_vi_number(text)
    return text
