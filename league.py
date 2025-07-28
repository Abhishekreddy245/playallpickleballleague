import pandas as pd
from itertools import combinations
from collections import defaultdict

class Team:
    def __init__(self, team_id, name, pool, players):
        self.id, self.name, self.pool = team_id, name, pool
        self.players = players
        self.total_dupr = sum(p['dupr'] for p in players)
        if self.total_dupr > 11:
            raise ValueError(f'Team {name} DUPR exceeds 11.0')
        self.reset_tracking()

    def reset_tracking(self):
        self.match_count = 0
        self.wins = 0
        self.score_diff = 0
        self.player_counts = {p['name']: 0 for p in self.players}

    def record_match(self, is_home, scored, conceded, lineup):
        self.match_count += 1
        self.score_diff += (scored - conceded)
        if scored > conceded:
            self.wins += 1
        for p in lineup:
            self.player_counts[p] += 1

class League:
    def __init__(self, teams):
        self.teams = {t.id: t for t in teams}
        self._init_pools()
        self._generate_fixtures()
        self.results = []

    def _init_pools(self):
        self.pools = defaultdict(list)
        for t in self.teams.values():
            self.pools[t.pool].append(t.id)

    def _generate_fixtures(self):
        self.fixtures = []
        for pool, ids in self.pools.items():
            for a,b in combinations(ids, 2):
                self.fixtures.append({
                    'pool': pool, 'home': a, 'away': b,
                    'played': False
                })

    def enter_result(self, idx, score_home, score_away, lineup_home, lineup_away):
        f = self.fixtures[idx]
        if f['played']:
            raise RuntimeError('Already played')
        f.update({
            'score_home': score_home, 'score_away': score_away,
            'lineup_home': lineup_home, 'lineup_away': lineup_away,
            'played': True
        })
        self.teams[f['home']].record_match(True, score_home, score_away, lineup_home)
        self.teams[f['away']].record_match(False, score_away, score_home, lineup_away)
        self.results.append(f)

    def standings(self, pool):
        data = []
        for tid in self.pools[pool]:
            t = self.teams[tid]
            pts = t.wins * 2
            data.append({
                'Team': t.name,
                'P': t.match_count,
                'W': t.wins,
                'L': t.match_count - t.wins,
                'Pts': pts,
                'Diff': t.score_diff
            })
        df = pd.DataFrame(data)
        return df.sort_values(['Pts','Diff'], ascending=[False,False]).reset_index(drop=True)

    def player_tracker(self, pool):
        rows = []
        for tid in self.pools[pool]:
            t = self.teams[tid]
            for p in t.players:
                name = p['name']
                played = t.player_counts[name]
                rows.append({
                    'Team': t.name,
                    'Player': name,
                    'Played': played,
                    'RemainingMin3': max(0,3-played),
                    'RemainingMax4': max(0,4-played)
                })
        return pd.DataFrame(rows)

    def export_to_excel(self, path):
        with pd.ExcelWriter(path, engine='openpyxl') as out:
            df_teams = pd.DataFrame([
                {
                    'ID': t.id,
                    'Team': t.name,
                    'Pool': t.pool,
                    **{f'P{i+1}': p['name'] for i,p in enumerate(t.players)},
                    **{f'DUPR{i+1}': p['dupr'] for i,p in enumerate(t.players)},
                    'TotalDUPR': t.total_dupr
                }
                for t in self.teams.values()
            ])
            df_teams.to_excel(out, sheet_name='Teams', index=False)
            pd.DataFrame(self.fixtures).to_excel(out, sheet_name='Matches', index=False)
            for pool in sorted(self.pools):
                self.standings(pool).to_excel(out, sheet_name=f'Standings_{pool}', index=False)
                self.player_tracker(pool).to_excel(out, sheet_name=f'Players_{pool}', index=False)
        print(f'Written to {path}')
