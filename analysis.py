# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 22:18:00 2019

@author: Archie
"""
#Importing modules: Pandas is used for dataframes and numpy for several functions

import numpy as np
import pandas as pd


#Reading the data from Olympics, country regions and country GDPs
olympics = pd.read_csv('athlete_events.csv')
noc = pd.read_csv('noc_regions.csv')
gdp = pd.read_csv('world_gdp.csv', skiprows=3)
pop = pd.read_csv('WorldPopulation.csv')



#Replacing empty cells in the medal column with No Medal
olympics=olympics[olympics['Year'] >= 1960]
olympics['Medal'].fillna('No Medal', inplace=True)

#Summer Olympics
olympics=olympics[olympics['Season'] == "Summer"]

#Removing a column that isn't used from the names of countries
noc.drop('notes', axis = 1 , inplace = True)

gdp.drop(['Indicator Name', 'Indicator Code'],
         axis=1,
         inplace=True)
gdp = pd.melt(gdp, id_vars = ['Country Name', 'Country Code'], var_name = 'Year', value_name = 'GDP')
gdp['Year'] = pd.to_numeric(gdp['Year'])

pop.drop(['Indicator Name', 'Indicator Code'], axis = 1, inplace = True)
pop = pd.melt(pop,
              id_vars = ['Country', 'Country Code'],
              var_name = 'Year',
              value_name = 'Population')
pop = pop.iloc[:-217]
pop['Year'] = pd.to_numeric(pop['Year'])



olympics = olympics.merge(noc, left_on='NOC', right_on='NOC', how='left')
olympics['region'] = np.where(olympics['NOC']=='SGP', 'Singapore', olympics['region'])
olympics['region'] = np.where(olympics['NOC']=='ROT', 'Refugee Olympic Athletes', olympics['region'])
olympics['region'] = np.where(olympics['NOC']=='TUV', 'Tuvalu', olympics['region'])
olympics.drop('Team', axis=1, inplace=True)
olympics.rename(columns = {'region': 'Team'}, inplace = True)



olympics = olympics.merge(gdp[['Country Name', 'Country Code']].drop_duplicates(),
                          left_on = 'Team',
                          right_on = 'Country Name',
                          how = 'left')
olympics.drop('Country Name', axis = 1, inplace = True)



olympics = olympics.merge(gdp,
                          left_on = ['Country Code', 'Year'],
                          right_on = ['Country Code', 'Year'],
                          how = 'left')
olympics.drop('Country Name', axis = 1, inplace = True)




olympics = olympics.merge(pop,
                          left_on = ['Country Code', 'Year'],
                          right_on= ['Country Code', 'Year'],
                          how = 'left')
olympics.drop('Country', axis = 1, inplace = True)



olympics['Medal_Won'] = np.where(olympics.loc[:,'Medal'] == 'No Medal', 0, 1)



identify_team_events = pd.pivot_table(olympics,
                                      index = ['Team', 'Year', 'Event'],
                                      columns = 'Medal',
                                      values = 'Medal_Won',
                                      aggfunc = 'sum',
                                      fill_value = 0).drop('No Medal', axis = 1).reset_index()

identify_team_events = identify_team_events.loc[identify_team_events['Gold'] > 1, :]

team_sports = identify_team_events['Event'].unique()
remove_sports = ["Gymnastics Women's Balance Beam", "Gymnastics Men's Horizontal Bar", 
                 "Swimming Women's 100 metres Freestyle", "Swimming Men's 50 metres Freestyle"]

team_sports = list(set(team_sports) - set(remove_sports))
# if an event name matches with one in team sports, then it is a team event. Others are singles events.
team_event_mask = olympics['Event'].map(lambda x: x in team_sports)
single_event_mask = [not i for i in team_event_mask]

# rows where medal_won is 1
medal_mask = olympics['Medal_Won'] == 1

# Put 1 under team event if medal is won and event in team event list
olympics['Team_Event'] = np.where(team_event_mask & medal_mask, 1, 0)

# Put 1 under singles event if medal is won and event not in team event list
olympics['Single_Event'] = np.where(single_event_mask & medal_mask, 1, 0)

# Add an identifier for team/single event
olympics['Event_Category'] = olympics['Single_Event'] + olympics['Team_Event']
medal_tally_agnostic = olympics.groupby(['Year', 'Team', 'Event', 'Medal'])[['Medal_Won', 'Event_Category']].\
agg('sum').reset_index()




medal_tally_agnostic = olympics.groupby(['Year', 'Team', 'Event', 'Medal'])[['Medal_Won', 'Event_Category']].agg('sum').reset_index()

medal_tally_agnostic['Medal_Won_Corrected'] = medal_tally_agnostic['Medal_Won']/medal_tally_agnostic['Event_Category']

# Medal Tally.
medal_tally = medal_tally_agnostic.groupby(['Year','Team'])['Medal_Won_Corrected'].agg('sum').reset_index()

medal_tally_pivot = pd.pivot_table(medal_tally,
                     index = 'Team',
                     columns = 'Year',
                     values = 'Medal_Won_Corrected',
                     aggfunc = 'sum',
                     margins = True).sort_values('All', ascending = False)[1:5]

# print total medals won in the given period
print(medal_tally_pivot.loc[:,'All'])
# List of top countries
top_countries = ['USA', 'Russia', 'Germany', 'China']

year_team_medals = pd.pivot_table(medal_tally,
                                  index = 'Year',
                                  columns = 'Team',
                                  values = 'Medal_Won_Corrected',
                                  aggfunc = 'sum')[top_countries]

# plotting the medal tallies
year_team_medals.plot(linestyle = '-', marker = 'o', alpha = 1, figsize = (10,8), linewidth = 2)