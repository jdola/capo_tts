import re

from num2words import num2words

_time_re = re.compile(
    r"""\b
                          ((0?[0-9])|(1[0-1])|(1[2-9])|(2[0-3]))  # hours
                          :
                          ([0-5][0-9])                            # minutes
                          \s*(a\\.m\\.|am|pm|p\\.m\\.|a\\.m|p\\.m)? # am/pm
                          \b""",
    re.IGNORECASE | re.X,
)
vn_unit_map = {"am": "sáng", "pm": "chiều"}


def _expand_num(n: int) -> str:
    return num2words(n, lang="vi")


def _expand_time_vietnamese(match: "re.Match") -> str:
    hour = int(match.group(1))
    past_noon = hour >= 12
    time = []
    if hour > 12:
        hour -= 12
    elif hour == 0:
        hour = 12
        past_noon = True
    time.append(_expand_num(hour))
    time.append("giờ")

    minute = int(match.group(6))
    if minute > 0:
        time.append(_expand_num(minute))
        time.append("phút")
    am_pm = match.group(7)
    if am_pm is None:
        time.append("chiều" if past_noon else "sáng")
    else:
        clean_am_pm = am_pm.replace(".", "")
        time.append(vn_unit_map.get(clean_am_pm, clean_am_pm))
    return " ".join(time)


def expand_time_vietnamese(text: str) -> str:
    return re.sub(_time_re, _expand_time_vietnamese, text)
