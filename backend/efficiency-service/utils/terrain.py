import pandas as pd

def group_highway_for_analysis(highway):
    if pd.isna(highway):
        return 'unspecified_road'
    elif highway == 'steps':
        return 'steps'
    elif highway in ['path', 'footway', 'pedestrian', 'cycleway']:
        return 'pedestrian_cycle'
    elif highway in ['track', 'unclassified', 'service', 'residential', 'tertiary', 'trunk_link']:
        return 'minor_road'
    elif highway in ['secondary', 'trunk']:
        return 'major_road'
    else:
        return 'other_road'

def group_surface_for_analysis(surface, highway):
    if pd.isna(surface):
        if highway in ['path', 'footway', 'pedestrian']:
            return 'unpaved'
        elif highway == 'cycleway':
            return 'paved'
        elif highway in ['track', 'unclassified', 'service', 'residential', 'tertiary']:
            return 'unpaved'
        elif highway in ['secondary', 'trunk', 'steps']:
            return 'paved'
        else:
            return 'unknown_surface'
    elif surface in ['asphalt', 'paved', 'paving_stones', 'sett', 'cobblestone', 'unhewn_cobblestone', 'grass_paver', 'metal', 'stone']:
        return 'paved'
    elif surface in ['gravel', 'compacted', 'unpaved', 'dirt', 'sand']:
        return 'unpaved'
    elif surface in ['grass', 'ground', 'wood']:
        return 'soft'
    elif surface == 'rock':
        return 'rocky'
    else:
        return 'other_surface'
    