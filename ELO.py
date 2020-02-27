import sqlite3
import Tools
import pickle
import numpy as np


# The constant K affects the influence each game has on rating.
def calc_elo(db_name, K=0.04):

    NN_train_data_X, NN_train_data_Y = [], []

    team_score_elo = {}
    team_rating_elo = {}
    first_kills_elo = {}
    clutches_elo = {}
    killm_all_elo = {}
    killm_first_elo = {}
    killm_awp_elo = {}
    Kills_elo = {}
    adr_elo = {}
    death_elo = {}
    assist_elo = {}

    # get data sorted by date and time
    conn = sqlite3.connect(db_name + '.db')
    c = conn.cursor()
    c.execute("SELECT * FROM CSGO_GAMES ORDER BY date ASC, time ASC")
    data = c.fetchall()

    # calculate elo
    for game_index, game in enumerate(data):
        # get game information
        team_name_1, team_name_2, veto, time, date, map, breakdown, team_rating, first_kills, \
        clutches_won, stat_table_1, stat_table_2, killm_all, killm_first, killm_awp = game

        try:
            train_data = []
            train_y = []

            # team elo systems
            score_1, score_2 = Tools.score_from_breakdwon(breakdown)
            rating_1, rating_2 = Tools.split_colon(team_rating)
            f_kills_1, f_kills_2 = Tools.split_colon(first_kills)
            clutches_1, clutches_2 = Tools.split_colon(clutches_won)
            for index, elo in enumerate([team_score_elo, team_rating_elo, first_kills_elo, clutches_elo]):
                result_1, result_2 = \
                    [(score_1, score_2), (rating_1, rating_2), (f_kills_1, f_kills_2), (clutches_1, clutches_2)][index]
                if team_name_1 in elo and team_name_2 in elo:
                    train_data += [elo[team_name_1]] + [elo[team_name_2]]
                    if index == 0:
                        train_y += [(result_1-result_2)/abs(result_1-result_2)]
                    expected_score = elo[team_name_1]-elo[team_name_2]
                    elo[team_name_1] = elo[team_name_1]+K*(result_1-result_2-expected_score)
                    elo[team_name_2] = elo[team_name_2]+K*(result_2-result_1+expected_score)
                else:
                    if team_name_1 not in elo:
                        elo[team_name_1] = 0
                    if team_name_2 not in elo:
                        elo[team_name_2] = 0

            # player matrix elo systems
            killm_all = Tools.killm_parsing(killm_all)
            killm_first = Tools.killm_parsing(killm_first)
            killm_awp = Tools.killm_parsing(killm_awp)
            for index, elo in enumerate([killm_all_elo, killm_first_elo, killm_awp_elo]):
                result = [killm_all, killm_first, killm_awp][index]
                if all([False for x in list(result[0])+list(result[1]) if x not in elo]):
                    e_1, e_2 = 0, 0
                    for player_1 in result[0]:
                        e_1 += elo[player_1]
                    for player_2 in result[0]:
                        e_2 += elo[player_2]
                    train_data += [e_1]
                    train_data += [e_2]
                    for index_1, player_1 in enumerate(result[0]):
                        for index_2, player_2 in enumerate(result[1]):
                            res = result[2][5 * index_1 + index_2]
                            result_1, result_2 = Tools.split_colon(res)
                            expected_score = elo[player_1] - elo[player_2]
                            elo[player_1] = elo[player_1] + K * (result_1 - result_2 - expected_score)
                            elo[player_2] = elo[player_2] + K * (result_2 - result_1 + expected_score)
                else:
                    for player in result[0]:
                        elo[player] = 0
                    for player in result[1]:
                        elo[player] = 0
            if len(train_data) == 14:
                NN_train_data_X.append(train_data)
                NN_train_data_Y.append(train_y)
        except:
            pass

        # save elo dict every 5000'th game
        if game_index % 5000 == 0 and game_index > 0:
            print(game_index)

    # save elo history
    with open('elo_hist.pkl', 'wb') as f:
        pickle.dump([team_score_elo, team_rating_elo, first_kills_elo, clutches_elo, killm_all_elo,
                     killm_first_elo, killm_awp_elo], f)
    with open('train_X.pkl', 'wb') as f:
        pickle.dump(NN_train_data_X, f)
    with open('train_Y.pkl', 'wb') as f:
        pickle.dump(NN_train_data_Y, f)
