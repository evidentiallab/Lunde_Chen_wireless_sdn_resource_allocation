from wireless_sdn_graph_model import GraphModel
import random

'''
sudo pip install networkx==1.9.1
sudo pip install dill==0.2.7.1
'''

'''
Run 4 such python programs at the same time:

$ nohup python wireless_sdn_pickle_graph_model_20_nodes.py >> ~/hi.txt &
$ nohup python wireless_sdn_pickle_graph_model_20_nodes.py >> ~/hi.txt &
$ nohup python wireless_sdn_pickle_graph_model_20_nodes.py >> ~/hi.txt &
$ nohup python wireless_sdn_pickle_graph_model_20_nodes.py >> ~/hi.txt &

'''

if __name__ == "__main__":
    for i in range(100):
        try:
            while 1:
                gm = GraphModel(number_nodes=20,
                                number_links_transmission=60,
                                number_extra_conflict_link_pairs=random.choice(range(-10, 10)),
                                number_of_cliques_min=9,
                                number_of_cliques_max=17,
                                number_of_channels=7,
                                min_number_link_of_each_channel=4,
                                max_number_link_of_each_channel=14,
                                transmission_range=6.7,
                                interference_range=9,
                                transmission_connection_ratio=1.0,
                                clique_based=False,
                                json_channels={1: {"color": "violet", "capacity": 600},
                                               2: {"color": "blue", "capacity": 600},
                                               3: {"color": "orange", "capacity": 600},
                                               4: {"color": "green", "capacity": 600},
                                               5: {"color": "yellow", "capacity": 600},
                                               6: {"color": "red", "capacity": 600},
                                               7: {"color": "gray", "capacity": 600},
                                               },
                                number_of_openflow_entries=20000, number_of_group_entries=2000,
                                xylimit=14, file_type=".png")
                if gm.check_is_constructed():
                    break
            print("i = " + str(i))
            gm.illustrate()
            gm.save()
        except Exception:
            continue

