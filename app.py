import streamlit as st
import pandas as pd
from league import Team, League

st.set_page_config(page_title='PPL League Manager', layout='wide')

if 'league' not in st.session_state:
    st.session_state.league = None

st.title('PlayAll Pickleball League Manager')

# Teams editor
st.header('1. Team Registration')
template = {
    'Team ID': list(range(1,17)),
    'Team Name': ['']*16,
    'Pool': ['']*16,
    'Player 1': ['']*16,
    'P1 DUPR': [0.0]*16,
    'Player 2': ['']*16,
    'P2 DUPR': [0.0]*16,
    'Player 3': ['']*16,
    'P3 DUPR': [0.0]*16
}
df_teams = st.experimental_data_editor(pd.DataFrame(template), num_rows='dynamic', key='teams')

df_teams['Total DUPR'] = df_teams[['P1 DUPR','P2 DUPR','P3 DUPR']].sum(axis=1)
bad = df_teams[df_teams['Total DUPR']>11]
if not bad.empty:
    st.error('Teams exceeding DUPR 11: ' + ', '.join(bad['Team Name']))

if st.button('Load Teams'):
    teams=[]
    for _,row in df_teams.iterrows():
        if row['Team Name'] and row['Total DUPR']<=11:
            players=[{'name':row['Player 1'],'dupr':row['P1 DUPR']},
                     {'name':row['Player 2'],'dupr':row['P2 DUPR']},
                     {'name':row['Player 3'],'dupr':row['P3 DUPR']}]
            teams.append(Team(int(row['Team ID']), row['Team Name'], row['Pool'], players))
    st.session_state.league = League(teams)
    st.success('League initialized')

if st.session_state.league is None:
    st.stop()
league = st.session_state.league

# Fixtures display
st.header('2. Fixtures & Results')
col1,col2 = st.columns(2)
dfA=pd.DataFrame([f for f in league.fixtures if f['pool']=='A'])
dfB=pd.DataFrame([f for f in league.fixtures if f['pool']=='B'])
with col1:
    st.subheader('Pool A Fixtures'); st.dataframe(dfA)
with col2:
    st.subheader('Pool B Fixtures'); st.dataframe(dfB)

# Result entry
st.subheader('Enter Result')
pool_sel = st.selectbox('Pool',['A','B'])
choices=[(i,f"R{f['round']} {league.teams[f['home']].name} vs {league.teams[f['away']].name}") 
         for i,f in enumerate(league.fixtures) if f['pool']==pool_sel]
idx = st.selectbox('Fixture', choices, format_func=lambda x: x[1])[0]
f=league.fixtures[idx]
h,a = f['home'], f['away']
col3,col4 = st.columns(2)
with col3:
    lineup_h=[st.selectbox('H1',[p['name'] for p in league.teams[h].players],key=f'h1_{idx}'),
              st.selectbox('H2',[p['name'] for p in league.teams[h].players],key=f'h2_{idx}')]
    sh = st.number_input('Score Home',0,50, key=f'sh_{idx}')
with col4:
    lineup_a=[st.selectbox('A1',[p['name'] for p in league.teams[a].players],key=f'a1_{idx}'),
              st.selectbox('A2',[p['name'] for p in league.teams[a].players],key=f'a2_{idx}')]
    sa = st.number_input('Score Away',0,50, key=f'sa_{idx}')
if st.button('Submit'):
    league.enter_result(idx,sh,sa,lineup_h,lineup_a)
    st.experimental_rerun()

# Standings & tracker
st.header('3. Standings & Tracker')
for pool in ['A','B']:
    st.subheader(f'Pool {pool}')
    dfS=league.standings(pool)
    dfS['Rank']=dfS['Pts'].rank(method='dense',ascending=False).astype(int)
    dfS=dfS.sort_values('Rank')
    st.dataframe(dfS.style.applymap(lambda v:'background-color:lightgreen' if isinstance(v,int) and v<=4 else '', subset=['Rank']))
    st.markdown(f'**Pool {pool} Players**')
    st.dataframe(league.player_tracker(pool))

# Export
st.header('4. Export')
if st.button('Export to Excel'):
    league.export_to_excel('PPL.xlsx')
    with open('PPL.xlsx','rb') as fp:
        st.download_button('Download', fp, file_name='PPL.xlsx')
