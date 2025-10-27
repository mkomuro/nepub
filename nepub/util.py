import re

RANGE_PATTERN = re.compile(r"[1-9][0-9]*(-[1-9][0-9]*)?(,[1-9][0-9]*(-[1-9][0-9]*)?)*")


def half_to_full(c: str):
    return {
        "A": "Ａ",
        "B": "Ｂ",
        "C": "Ｃ",
        "D": "Ｄ",
        "E": "Ｅ",
        "F": "Ｆ",
        "G": "Ｇ",
        "H": "Ｈ",
        "I": "Ｉ",
        "J": "Ｊ",
        "K": "Ｋ",
        "L": "Ｌ",
        "M": "Ｍ",
        "N": "Ｎ",
        "O": "Ｏ",
        "P": "Ｐ",
        "Q": "Ｑ",
        "R": "Ｒ",
        "S": "Ｓ",
        "T": "Ｔ",
        "U": "Ｕ",
        "V": "Ｖ",
        "W": "Ｗ",
        "X": "Ｘ",
        "Y": "Ｙ",
        "Z": "Ｚ",
        "a": "ａ",
        "b": "ｂ",
        "c": "ｃ",
        "d": "ｄ",
        "e": "ｅ",
        "f": "ｆ",
        "g": "ｇ",
        "h": "ｈ",
        "i": "ｉ",
        "j": "ｊ",
        "k": "ｋ",
        "l": "ｌ",
        "m": "ｍ",
        "n": "ｎ",
        "o": "ｏ",
        "p": "ｐ",
        "q": "ｑ",
        "r": "ｒ",
        "s": "ｓ",
        "t": "ｔ",
        "u": "ｕ",
        "v": "ｖ",
        "w": "ｗ",
        "x": "ｘ",
        "y": "ｙ",
        "z": "ｚ",
        "0": "０",
        "1": "１",
        "2": "２",
        "3": "３",
        "4": "４",
        "5": "５",
        "6": "６",
        "7": "７",
        "8": "８",
        "9": "９",
        ".": "．",
        ",": "，",
        "!": "！",
        "?": "？",
        "%": "％",
    }[c]


def range_to_episode_ids(my_range: str):
    my_range = my_range.replace(" ", "")
    if not RANGE_PATTERN.fullmatch(my_range):
        raise Exception(f"range が想定しない形式です: {my_range}")
    episode_ids: set[str] = set([])
    for r in my_range.split(","):
        if "-" in r:
            start, end = r.split("-")
            if int(end) > 10_000:
                # 安全のため値が大きすぎる場合はエラーにする
                raise Exception(f"range に含まれる値が大きすぎます: {end}")
            for i in range(int(start), int(end) + 1):
                episode_ids.add(str(i))
        else:
            episode_ids.add(r)
    return episode_ids
