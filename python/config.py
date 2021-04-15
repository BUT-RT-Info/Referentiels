
"""Configuration (chemins et données qui ne sont pas dans les documents)
"""
import os

class Config(object):
    ROOT=".."
    # ECTS des UE de chaque semestres
    ECTS = {
        1 : {
            "RT1" : 12, "RT2" : 8, "RT3" : 10,
        },
        2 : {
            "RT1" : 11, "RT2" : 10, "RT3" : 9,
        }
    }

# Safety check
for sem_id in Config.ECTS:
    sum_ects_sem = sum( [ Config.ECTS[sem_id][ue]  for ue in Config.ECTS[sem_id] ] )
    assert sum_ects_sem == 30



