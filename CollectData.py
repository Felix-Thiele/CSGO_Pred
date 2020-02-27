import sqlite3

import Tools
import GetMatchData


HLTV_MATCHES_LINK = "https://www.hltv.org/results/"


def find_link_next_page(page_soup):

    # this method finds the next results-page given the old one

    nextPage = page_soup.find("a", {"class": "pagination-next"})
    return "https://www.hltv.org" + nextPage["href"]


def find_match_links(page_soup):

    # this method take a hltv results page and returns a list of all games played

    match_link_list, result = [], []
    result_holder = page_soup.findAll("div", {"class": "results-holder"})
    for body in result_holder:
        result.extend(body.findAll("a", {'href': True}))
    for link in result:
        href = str(link['href'])
        if "/matches/" in href:
            match_link_list.append("https://www.hltv.org" + href)
    return match_link_list


def collect_all(nr_pages, db_name):

    # this method collects the data from all matches and saves it in a sql database
    link = HLTV_MATCHES_LINK
    for _ in range(nr_pages):
        soup = Tools.get_raw_soup(link)
        games = find_match_links(soup)
        for game_link in games:
            try:
                GetMatchData.collect(game_link, db_name)
            except:
                pass
        link = find_link_next_page(soup)


def update(db_name):

    # this method updates the database with the new data
    link = HLTV_MATCHES_LINK
    new = True
    while new:
        soup = Tools.get_raw_soup(link)
        games = find_match_links(soup)
        for game_link in games:
            try:
                new = GetMatchData.collect(game_link, db_name, update=True)
            except:
                pass
            if new==False:
                return
        link = find_link_next_page(soup)


