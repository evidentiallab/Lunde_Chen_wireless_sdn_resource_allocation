from wireless_sdn_graph_model import GraphModel
import random

'''
Run 4 such python programs at the same time:

$ nohup python wireless_sdn_pickle_graph_model_60_nodes.py >> ~/hi.txt &
$ nohup python wireless_sdn_pickle_graph_model_60_nodes.py >> ~/hi.txt &
$ nohup python wireless_sdn_pickle_graph_model_60_nodes.py >> ~/hi.txt &
$ nohup python wireless_sdn_pickle_graph_model_60_nodes.py >> ~/hi.txt &

'''

if __name__ == "__main__":
    for i in range(100):
        try:
            while 1:
                gm = GraphModel(number_nodes=60,
                                number_links_transmission=180,
                                number_extra_conflict_link_pairs=random.choice(range(30, 200)),
                                number_of_cliques_min=-1,
                                number_of_cliques_max=999,
                                number_of_channels=7,
                                min_number_link_of_each_channel=0,
                                max_number_link_of_each_channel=1000,
                                transmission_range=6,
                                interference_range=9,
                                transmission_connection_ratio=1.0,
                                clique_based=True,
                                json_channels={1: {"color": "violet", "capacity": 600},
                                               2: {"color": "blue", "capacity": 600},
                                               3: {"color": "orange", "capacity": 600},
                                               4: {"color": "green", "capacity": 600},
                                               5: {"color": "yellow", "capacity": 600},
                                               6: {"color": "red", "capacity": 600},
                                               7: {"color": "gray", "capacity": 600},
                                               },
                                number_of_openflow_entries=20000, number_of_group_entries=2000,
                                xylimit=17, file_type=".png")
                if gm.check_is_constructed():
                    break
            print("i = " + str(i))
            gm.illustrate()
            gm.save()
        except Exception:
            continue

