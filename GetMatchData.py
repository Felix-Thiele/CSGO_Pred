from bs4 import BeautifulSoup
import sqlite3
import pandas as pd

import Tools


def collect(game_link, db_name, update=False):

    # this method parses a  match and collects all its data


    soup = Tools.get_raw_soup(game_link)
    conn = sqlite3.connect(db_name+'.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS CSGO_GAMES (team_1 TEXT, team_2 TEXT, veto TEXT, time TEXT,"
              " date TEXT, map TEXT, breakdown TEXT, team_rating TEXT, first_kills TEXT, clutches_won TEXT,"
              " stat_table_1 BLOB, stat_table_2 BLOB, killm_all BLOB, killm_first BLOB, killm_awp BLOB)")

    # team
    team_names = []
    team_box = soup.find("div", {"class": "standard-box teamsBox"})
    teams = team_box.find_all("div", {"class": "team"})
    for team in teams:
        team_names.append(team.find("div", {"class": "teamName"}).getText())

    # vetos
    vetos = soup.find_all("div", {"class": "standard-box veto-box"})
    if len(vetos) == 2:
        veto = vetos[1].getText()
    else:
        veto = "random"

    # time/date
    time, date = soup.find("div", {"class": "time"}), soup.find("div", {"class": "date"})
    time, date = time.getText(), date.getText()

    # format date
    date = Tools.format_date(date)

    # detailed stats:
    detailed_stats_link = soup.find("div", {"class": "small-padding stats-detailed-stats"}).find('a', href=True)['href']
    map_links = game_maps("https://www.hltv.org" + detailed_stats_link)
    for map in map_links:
        stat_tables, map, box_info, kill_matrices = collect_detailed_stats(map)
        # params: team_names, veto, time, date, map, breakdown, team rating,
        # first kills, clutches won, stat_tables, killmatrices
        print(team_names)

        if not update:
            c.execute("INSERT INTO CSGO_GAMES (team_1, team_2, veto, time, date, map, breakdown, team_rating, first_kills, "
                      "clutches_won, stat_table_1, stat_table_2, killm_all, killm_first, killm_awp) "
                      "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (team_names[0], team_names[1], veto, time, date, map, box_info[0], box_info[1], box_info[2],
                       box_info[3], stat_tables[0].to_csv(), stat_tables[1].to_csv(), kill_matrices[0].to_csv(),
                       kill_matrices[1].to_csv(), kill_matrices[2].to_csv()))
            conn.commit()
        else:
            c.execute("SELECT * FROM CSGO_GAMES WHERE date = ? AND team_1 = ? AND team_2 = ? AND map = ? AND breakdown = ?",
                      (date, team_names[0], team_names[1], map, box_info[0]))
            data = c.fetchall()
            if data == []:
                c.execute(
                    "INSERT INTO CSGO_GAMES (team_1, team_2, veto, time, date, map, breakdown, team_rating, first_kills, "
                    "clutches_won, stat_table_1, stat_table_2, killm_all, killm_first, killm_awp) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (team_names[0], team_names[1], veto, time, date, map, box_info[0], box_info[1], box_info[2],
                     box_info[3], stat_tables[0].to_csv(), stat_tables[1].to_csv(), kill_matrices[0].to_csv(),
                     kill_matrices[1].to_csv(), kill_matrices[2].to_csv()))
                conn.commit()
            else:
                return False
    c.close()
    return True


def game_maps(link):
    soup = Tools.get_raw_soup(link)

    # check bo3:
    maps, links = [], []
    match_maps = soup.find("div", {"class": "stats-match-maps"})
    columns = match_maps.find_all("div", {"class": "columns"})
    for column in columns:
        maps += column.find_all('a', href=True)
    for map in maps[1:]:
        map_link = map['href']
        links.append("https://www.hltv.org" + map_link)
    if links == []:
        links.append(link)
    return links


def collect_detailed_stats(link):
    soup = Tools.get_raw_soup(link)

    stat_tables = []

    # map
    map = soup.find("div", {"class": "match-info-box"}).getText()
    map = [M for M in ["Inferno", "Overpass", "Cache", "Train", "Mirage", "Nuke", "Dust2", "Vertigo", "Cobblestone",
                       "Canals", "Zoo", "Abbey", "Biome"] if M in map][0]

    # stats table
    stats = soup.find_all("table", {"class": "stats-table"})
    for stat in stats:
        df = pd.read_html(str(stat))[0]
        stat_tables.append(df)

    # Breakdown, Team rating, First kills, Clutches won
    info_rows = soup.find_all("div", {"class": "match-info-row"})
    breakdown = info_rows[0].find("div", {"class": "right"}).getText()
    if str(info_rows[0].find("div", {"class": "right"})).find("t-color") < \
            str(info_rows[0].find("div", {"class": "right"})).find("ct-color"):
        breakdown = "t__" + breakdown
    else:
        breakdown = "ct_"+breakdown
    team_rating = info_rows[1].find("div", {"class": "right"}).getText()
    first_kills = info_rows[2].find("div", {"class", "right"}).getText()
    clutches_won = info_rows[3].find("div", {"class", "right"}).getText()
    box_info = [breakdown, team_rating, first_kills, clutches_won]

    # other page links:
    top_menu = soup.find("div", {"class", "stats-top-menu"})
    other_page_links = top_menu.find_all('a', href=True)

    # performance page
    performance_page = "https://www.hltv.org" + other_page_links[1]['href']
    performance_soup = Tools.get_raw_soup(performance_page)

    # killmatrices
    killmatrix_all = performance_soup.find("div", {"id": "ALL-content"})
    killmatrix_first = performance_soup.find("div", {"id": "FIRST_KILL-content"})
    killmatrix_awp = performance_soup.find("div", {"id": "AWP-content"})

    kill_m_all_df = pd.read_html(str(killmatrix_all.find("table", {"class": "stats-table"})))[0]
    kill_m_first_df = pd.read_html(str(killmatrix_first.find("table", {"class": "stats-table"})))[0]
    kill_m_awp_df = pd.read_html(str(killmatrix_awp.find("table", {"class": "stats-table"})))[0]

    kill_matrices = [kill_m_all_df, kill_m_first_df, kill_m_awp_df]

    return stat_tables, map, box_info, kill_matrices

collect_detailed_stats("https://www.hltv.org/stats/matches/mapstatsid/85758/ence-vs-astralis")