import re
from functools import reduce
from datetime import datetime
class CfbdParser:
    def __init__(self, api_key=None):
        import cfbd
        config = cfbd.Configuration()
        if api_key is not None:
            config.api_key["Authorization"] = api_key
        config.api_key_prefix['Authorization'] = 'Bearer'
        self.api_client = cfbd.ApiClient(config)
    def scrape_results(obj_list):
        import numpy as np
        import pandas as pd
        M = list(map(lambda x: list(vars(x).keys()), obj_list))
        M = [obj for obj in M if obj]
        if len(M) > 0:
            keys = [re.sub("^_", "", k) for k in reduce(np.intersect1d, M)]
            keys = np.setdiff1d(keys, ["configuration", "discriminator"])
            df = pd.DataFrame()
            for k in keys:
                df[k] = [vars(d)["_%s" % k] for d in obj_list]
            return df
        else:
            return pd.DataFrame()
    def games(self, **kwargs):
        import cfbd
        ga = cfbd.GamesApi(self.api_client)
        gl = ga.get_games(**kwargs)
        df = CfbdParser.scrape_results(gl)
        df.rename({"id": "game_id"}, axis=1, inplace=True) ## for merging
        df["start_date"] = [datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ") for x in df["start_date"].values]
        df.index = df["game_id"].values
        return df
    def teams(self, classification=["fbs", "fcs"], **kwargs):
        import pandas as pd
        import cfbd
        ta = cfbd.TeamsApi(self.api_client)
        tl = ta.get_teams(**kwargs)
        df = CfbdParser.scrape_results(tl)
        df.rename({"id": "team_id", "logos": "logo"}, axis=1, inplace=True) ## for merging
        df = df.loc[~df["logo"].isna(), ["abbreviation", "alt_color", "classification", "color", "conference", "team_id", "logo", "mascot", "school"]]
        df["logo"] = [x[0] for x in df["logo"].values]
        if type(classification) is list and classification:
            df = df.loc[df["classification"].isin(classification), :] ### restrict
        df.index = df["team_id"].values
        return df
