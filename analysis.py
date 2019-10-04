# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 22:18:00 2019

@author: Archie
"""
#Importing modules: Numpy is used for several functions, Pandas for dataframes and matplotlib.pyplot for graphing
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#Reading the data from Olympics, country regions, country GDPs and country populations
olympics = pd.read_csv('athlete_events.csv')
noc = pd.read_csv('noc_regions.csv')
gdp = pd.read_csv('world_gdp.csv', skiprows=3)
pop = pd.read_csv('WorldPopulation.csv')



#Replacing empty cells in the medal column with No Medal
olympics=olympics[olympics['Year'] >= 1961]
olympics['Medal'].fillna('No Medal', inplace=True)

#Taking only Summer Olympic results
olympics=olympics[olympics['Season'] == "Summer"]

#Doing some simple formatting
#Dropping uneccessary column
noc.drop('notes', axis = 1 , inplace = True)

#Dropping uneccessary columns
gdp.drop(['Indicator Name', 'Indicator Code'],
         axis=1,
         inplace=True)
#Merging columns for all year's GDPs into a single column, and assigning each GDP its corresponding 'Year' value in the next column
gdp = pd.melt(gdp, id_vars = ['Country Name', 'Country Code'], var_name = 'Year', value_name = 'GDP')
#Converting the 'Year' column to a numerical value
gdp['Year'] = pd.to_numeric(gdp['Year'])

#Dropping uneccessary columns
pop.drop(['Indicator Name', 'Indicator Code'], axis = 1, inplace = True)
#Merging columns for all year's populations into a single column and assigning each population its corresponding 'Year' value in the next column
pop = pd.melt(pop,
              id_vars = ['Country', 'Country Code'],
              var_name = 'Year',
              value_name = 'Population')
#Dropping rows with null values
pop = pop.iloc[:-217]
#Converting the 'Year' column to a numerical value
pop['Year'] = pd.to_numeric(pop['Year'])



#Merging name of country by country code
olympics = olympics.merge(noc, left_on='NOC', right_on='NOC', how='left')
print(olympics.loc[olympics['region'].isnull(),['NOC', 'Team']].drop_duplicates())
#Adding missing values by hand based off above null values
olympics['region'] = np.where(olympics['NOC']=='SGP', 'Singapore', olympics['region'])
olympics['region'] = np.where(olympics['NOC']=='ROT', 'Refugee Olympic Athletes', olympics['region'])
olympics['region'] = np.where(olympics['NOC']=='TUV', 'Tuvalu', olympics['region'])
#Drop uneccessaary column
olympics.drop('Team', axis=1, inplace=True)
#Renaming column to more easily identify
olympics.rename(columns = {'region': 'Team'}, inplace = True)



#Merging all values for each athlete's country
olympics = olympics.merge(gdp[['Country Name', 'Country Code']].drop_duplicates(),
                          left_on = 'Team',
                          right_on = 'Country Name',
                          how = 'left')
olympics.drop('Country Name', axis = 1, inplace = True)



#Selecting the GDP value for each athlete for the year of those Olympic Games
olympics = olympics.merge(gdp,
                          left_on = ['Country Code', 'Year'],
                          right_on = ['Country Code', 'Year'],
                          how = 'left')
olympics.drop('Country Name', axis = 1, inplace = True)



#Merging population for each athlete by 'Country Code' and year of those Olympic Games
olympics = olympics.merge(pop,
                          left_on = ['Country Code', 'Year'],
                          right_on= ['Country Code', 'Year'],
                          how = 'left')
olympics.drop('Country', axis = 1, inplace = True)



#Identifying medal winners
olympics['Medal_Won'] = np.where(olympics.loc[:,'Medal'] == 'No Medal', 0, 1)
#Checking if medals won in a year for an event by a team is more than 1 --> team event
team_events = pd.pivot_table(olympics,
                             values = 'Medal_Won',
                             index = ['Team', 'Year', 'Event'],
                             columns = 'Medal',
                             aggfunc = 'sum',
                             fill_value = 0
                             ).drop('No Medal', axis = 1).reset_index()
team_events = team_events.loc[team_events['Gold'] > 1, :]
team_events = team_events['Event'].unique()



#In the case that two people tied for first, two gold medals would be awarded and
#the events below would be recorded as team events, so we must account for this
false_team_events = ["Gymnastics Women's Balance Beam",
                     "Gymnastics Men's Horizontal Bar",
                     "Swimming Women's 100 metres Freestyle",
                     "Swimming Men's 50 metres Freestyle"]
team_sports=list(set(team_events)-set(false_team_events))



#Seperating team events and single events
team_events_mask = olympics['Event'].map(lambda x: x in team_sports)
single_events_mask = [not i for i in team_events_mask]

medal_mask = olympics['Medal_Won'] == 1

#Put 1 under 'Team_Event' if medal was won and event is in team_events
olympics['Team_Event'] = np.where(team_events_mask & medal_mask, 1, 0)
#Put 1 under 'Single_Event' if medal was won and event is in single_events
olympics['Single_Event'] = np.where(single_events_mask & medal_mask, 1, 0)
olympics['Event Type'] = olympics['Single_Event'] + olympics['Team_Event']






#Everything under here is analysis that I found interesting, need to pick and
#choose what to include.





'''
medal_tally_agnostic = olympics.groupby(['Year', 'Team', 'Event', 'Medal'])[['Medal_Won', 'Event Type']].agg('sum').reset_index()
medal_tally_agnostic['Medal_Won_Corrected'] = medal_tally_agnostic['Medal_Won']/medal_tally_agnostic['Event Type']
medal_tally = medal_tally_agnostic.groupby(['Year','Team'])['Medal_Won_Corrected'].agg('sum').reset_index()
medal_tally_pivot = pd.pivot_table(medal_tally,
                                   index = 'Team',
                                   columns = 'Year',
                                   values = 'Medal_Won_Corrected',
                                   aggfunc = 'sum',
                                   margins = True).sort_values('All', ascending = False)[1:5]
print(medal_tally_pivot.loc[:, 'All'])


# List of top countries
top_countries = ['USA', 'Russia', 'Germany', 'China']

year_team_medals = pd.pivot_table(medal_tally,
                                  index = 'Year',
                                  columns = 'Team',
                                  values = 'Medal_Won_Corrected',
                                  aggfunc = 'sum')[top_countries]

# plotting the medal tallies
plot = year_team_medals.plot(linestyle = '-', marker = 'o', alpha = 0.9, figsize = (10,8), linewidth = 2)
plot.set_xlabel('Olympic Year')
plot.set_ylabel('Number of Medals')
plot.set_title('Olympic Performance Comparison')




# row mask where countries match
row_mask_2 = medal_tally_agnostic['Team'].map(lambda x: x in top_countries)

# Pivot table to calculate sum of gold, silver and bronze medals for each country
medal_tally_specific = pd.pivot_table(medal_tally_agnostic[row_mask_2],
                                      index = ['Team'],
                                      columns = 'Medal',
                                      values = 'Medal_Won_Corrected',
                                      aggfunc = 'sum',
                                      fill_value = 0).drop('No Medal', axis = 1)

# Re-order the columns so that they appear in order on the chart.
medal_tally_specific = medal_tally_specific.loc[:, ['Gold', 'Silver', 'Bronze']]

plot2 = medal_tally_specific.plot(kind = 'bar', stacked = True, figsize = (8,6), rot = 0)
plot2.set_xlabel('Number of Medals')
plot2.set_ylabel('Country')


# To get the sports, teams are best at, we now aggregate the medal_tally_agnostic dataframe as we did earlier.
best_team_sports = pd.pivot_table(medal_tally_agnostic[row_mask_2],
                                  index = ['Team', 'Event'],
                                  columns = 'Medal',
                                  values = 'Medal_Won_Corrected',
                                  aggfunc = 'sum',
                                  fill_value = 0).sort_values(['Team', 'Gold'], ascending = [True, False]).reset_index()

best_team_sports.drop(['Bronze', 'Silver', 'No Medal'], axis = 1, inplace = True)
best_team_sports.columns = ['Team', 'Event', 'Gold_Medal_Count']

year_team_gdp = olympics.loc[:, ['Year', 'Team', 'GDP']].drop_duplicates()

medal_tally_gdp = medal_tally.merge(year_team_gdp,
                                   left_on = ['Year', 'Team'],
                                   right_on = ['Year', 'Team'],
                                   how = 'left')

row_mask_5 = medal_tally_gdp['Medal_Won_Corrected'] > 0
row_mask_6 = medal_tally_gdp['Team'].map(lambda x: x in top_countries)

correlation = medal_tally_gdp.loc[row_mask_5, ['GDP', 'Medal_Won_Corrected']].corr()['Medal_Won_Corrected'][0]
plt.plot(medal_tally_gdp.loc[row_mask_5, 'GDP'], 
           medal_tally_gdp.loc[row_mask_5, 'Medal_Won_Corrected'] , 
           linestyle = 'none', 
           marker = 'o',
           alpha = 0.4)
plt.show()
'''