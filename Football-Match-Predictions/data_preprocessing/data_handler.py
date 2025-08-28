import pandas as pd

# Load data
team_stats = pd.read_csv('./teamstats.csv')

# Extract unique season and date per gameID (since they should be the same for both teams)
game_info = team_stats.groupby('gameID')[['season', 'date']].first().reset_index()

team_stats = team_stats.drop(columns=['season'])

# Pivot so each game has one row with home and away columns
game_stats = team_stats.pivot(index='gameID', columns='location')

# Rename columns to start with 'h_' for home and 'a_' for away
game_stats.columns = [f'{loc}_{col}' for col, loc in game_stats.columns]

# Reset index
game_stats = game_stats.reset_index()

game_stats = game_stats.drop(columns=['h_date','a_date'])

# Merge back the season and date columns
game_stats = game_stats.merge(game_info, on='gameID', how='left')

result_mapping = {'W': '1', 'D': 'X', 'L': '2'}

# Create new result column based on home team's result
game_stats['result'] = game_stats['h_result'].map(result_mapping)

results = game_stats[['gameID','result']]

game_stats = game_stats.drop(columns=['result'])

game_stats['date'] = pd.to_datetime(game_stats['date'], errors='coerce')

def get_last_n_games(team, game_date, n=10):
    previous_games = game_stats[((game_stats['h_teamID'] == team)| (game_stats['a_teamID'] == team)) & (game_stats['date'] < game_date)].sort_values(by='date', ascending=False)
    return previous_games.head(n)

prev_games = []
for _,row in team_stats.iterrows():
    game = row['gameID']
    team = row['teamID']
    #season = row['season']
    date = row['date']
    location = row['location']

    last_games = get_last_n_games(team, date)
    last_games.to_dict(orient='list')
    home = []
    prev_games_dict = {}
    prev_games_dict['gameID'] = game
    prev_games_dict['teamID'] = team
    prev_games_dict['location'] = location
    count = 0
    for id in last_games.get('h_teamID'):
        if id == team:
            home.append(True)
        else:
            home.append(False)
        key = f'is_home_{count}'
        prev_games_dict[key] = home[count]
        count += 1

    
    for col, rows in last_games.items():
        sliced_col = col[2:]
        if sliced_col == 'teamID' or col == 'gameID':
            continue
        if col[0] == 'h' or col[0] =='a':
            for count, stat in enumerate(rows):
                if (home[count] and col == 'a_result') or (not home[count] and col == 'h_result'):
                    continue
                if (col[0] == 'h' and home[count]) or (col[0] == 'a' and not home[count]):
                    key = f'{sliced_col}_{count}'
                    prev_games_dict[key] = stat
                else:
                    key = f'{sliced_col}_faced_{count}'
                    prev_games_dict[key] = stat
        else:
            for count, stat in enumerate(rows):
                key = f'{col}_{count}'
                prev_games_dict[key] = stat

    prev_games.append(prev_games_dict)

prev_games_df = pd.DataFrame(prev_games)

# Pivot so each game has one row with home and away columns
h_a_prev_games = prev_games_df.pivot(index='gameID', columns='location')

# Rename columns to start with 'h_' for home and 'a_' for away
h_a_prev_games.columns = [f'{loc}_{col}' for col, loc in h_a_prev_games.columns]

# Reset index
h_a_prev_games = h_a_prev_games.reset_index()

h_a_prev_games = h_a_prev_games.merge(game_info, on='gameID', how='left')

h_a_prev_games = h_a_prev_games.merge(results, on='gameID', how='left')

# Print results
print(h_a_prev_games.head())
print(h_a_prev_games.shape)

h_a_prev_games.to_csv('prev_games.csv', index=False)
