import requests
import os
import json

TOKEN = os.environ['CHUNIREC_TOKEN']

MAXSCORE = 1010000.0
SSSP = 1009000.0
SSS = 1007500.0
SSP = 1005000.0
SS = 1000000.0
SP = 990000
S = 975000

def score_to_rank_rate(score):
    if score >= SSSP:
        return ('SSSP', 2.15)
    elif score >= SSS:
        return ('SSS', 2.0 + (score - SSS) * 0.0001)
    elif score >= SSP:
        return ('SSP', 1.5 + (score - SSP) * 0.0002)
    elif score >= SS:
        return ('SS', 1.0 + (score - SS) * 0.0001)
    elif score >= S:
        return ('S', 0 + (score - S) * 0.00004)
    else:
        return ('?', 0)

# Music Meta
# id title genre artist release bpm
class MusicMeta:
    def __init__(self, meta):
        self.__dict__.update(meta)

# Music Chart
# diff level const maxcombo is_const_unknown
class MusicChart:
    def __init__(self, data, diff):
        self.__dict__.update(data)
        self.diff = diff
    def note_score(self):
        return MAXSCORE / self.maxcombo

# MusicInfo
# meta charts...{ diff: chart }
class MusicInfo:
    def __init__(self, info):
        self.meta = MusicMeta(info['meta'])
        self.charts = dict()
        for diff, ch in info['data'].items():
            self.charts[diff] = MusicChart(ch, diff)

# Music Dict
# get_info to get music info
class MusicDict:
    def __init__(self):
        payload = {
                'region': 'jp2',
                'token': TOKEN
        }
        r = requests.get('https://api.chunirec.net/2.0/music/showall.json', params=payload)
        data = json.loads(r.text)
        self.musics = dict()
        for d in data:
            self.musics[d['meta']['id']] = MusicInfo(d)
    def get_info(self, id):
        return self.musics[id]

# Music Result
# id diff level title const score rating is_const_unknown is_clear is_fullcombo is_alljustice
# is_fullchain genre updated_at is_played
class MusicResult:
    def __init__(self, data):
        self.__dict__.update(data)
    def __repr__(self):
        return f"({self.title}, {self.score})"

#https://api.chunirec.net/2.0/records/showall.json
class NormalRecord:
    def __init__(self, user_name = None):
        payload = {
                'region': 'jp2',
                'token': TOKEN
        }
        if user_name is not None:
            payload['user_name'] = user_name
        r = requests.get('https://api.chunirec.net/2.0/records/showall.json', params=payload)
        self.records = [MusicResult(data) for data in json.loads(r.text)['records']]

    def bests(self):
        sorted_records = sorted(self.records, key = lambda record: record.rating)
        sorted_records.reverse()
        return sorted_records[0:30]

#https://api.chunirec.net/2.0/records/rating_data.json
class RatingRecord:
    def __init__(self, user_name = None):
        payload = {
                'region': 'jp2',
                'token': TOKEN
        }
        if user_name is not None:
            payload['user_name'] = user_name
        r = requests.get('https://api.chunirec.net/2.0/records/rating_data.json', params=payload)
        self.bests = [MusicResult(data) for data in json.loads(r.text)['best']['entries']]
        self.recent = [MusicResult(data) for data in json.loads(r.text)['recent']['entries']]
        self.best_candidate = [MusicResult(data) for data in json.loads(r.text)['best_candidate']['entries']]
        self.best_candidate_sss = [MusicResult(data) for data in json.loads(r.text)['best_candidate_sss']['entries']]
        self.outside = [MusicResult(data) for data in json.loads(r.text)['best_outside']['entries']]

# positions: L, C, R
class MarkDownChart:
    def __init__(self, threads, positions):
        pos_elem = { "L": ":---", "C": ":---:", "R": "---:" }
        self.thread_md = "|" + "|".join(threads) + "|"
        self.position_md = "|" + "|".join([pos_elem[p] for p in positions]) + "|"
        self.bodys = []
    def add_elem(self, elems):
        self.bodys.append("|" + "|".join(elems) + "|")
    def generate_md_table(self):
        return "{}\n{}\n{}\n".format(self.thread_md, self.position_md, "\n".join(self.bodys))

class YTUrlDict:
    def __init__(self, dic):
        self.dic = dic
    def get(self, result):
        key = result.title + " " + result.diff
        if key in self.dic:
            return self.dic[key]
        else:
            return ""

def load_yt_dict(json_file):
    with open(json_file, mode="rt", encoding="utf-8") as f:
        return YTUrlDict(json.load(f))

def generate_md_chart(music_dict, record, results, yt_dict):
    bests = record.bests()
    md = MarkDownChart(
            ["title", "best", "diff", "Lv.", "score", "const", "rate", "yt"],
            ["L"    , "C"   , "C"   , "C"  , "R"    , "R"    , "R"   , "C" ]
        )
    for result in results:
        yt_url = yt_dict.get(result)
        is_best = result in bests
        md.add_elem([str(result.title), "\\*" if is_best else "", str(result.diff), str(result.level), "`" + str(result.score) + "`", str(result.const), str(result.rating), "[yt]({})".format(yt_url) if yt_url != "" else ""])
    return md.generate_md_table()

def over14p_results(records):
    results = []
    for res in record.records:
        if res.const >= 14.5:
            results.append(res)
    results.sort(key = lambda res: (res.const, res.score), reverse=True)
    return results

if __name__ == '__main__':
    music_dict = MusicDict()
    record = NormalRecord()
    rating_info = RatingRecord()
    yt_dict = load_yt_dict("yt_url.json")
    with open("readme.md", mode="w") as readme:
        chart = generate_md_chart(music_dict, record, over14p_results(record), yt_dict)
        text = "# 14+以上のリザルトと手元動画\n\nスコアと対応してない動画があるのでがんばって撮る\n\n{}".format(chart)
        readme.write(text)
