from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO


def get_raw_soup(url):

    # this method gets the html code from the given website, and converts it to a beautiful soup object.

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}
    req = Request(url=url, headers=headers)
    html = urlopen(req).read()
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def format_date(date_str):
    date_bits = date_str.split()
    day = ("0"+date_bits[0][:-2])[-2:]
    month = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
             "October", "November", "December"].index(date_bits[2])
    month = ("0"+str(month))[-2:]
    year = str(date_bits[3])
    return year+"-"+month+"-"+day


def score_from_breakdwon(br_str):
    br_str = br_str[3:]
    parts = br_str.split()
    return int(parts[0]), int(parts[2])


def split_colon(cl_str):
    cl_strip = cl_str.strip()
    pos = cl_strip.find(":")
    part_1, part_2 = cl_strip[:pos], cl_strip[pos+1:]
    return float(part_1), float(part_2)


def killm_parsing(csv_str):
    io = StringIO(csv_str)
    df = pd.read_csv(io)
    players_1 = df.loc[:, "0"][1:].values
    players_2 = df.loc[0, :][2:].values
    results = []
    for i in range(1,6):
        for j in ["1", "2", "3", "4", "5"]:
            results.append(df.loc[i, j])
    return players_1, players_2, results