#Importing modules: Numpy is used for several functions, Pandas for dataframes and matplotlib.pyplot for graphing
import numpy as np
import pandas as pd



#Reading the data from Olympics, country regions, country GDPs and country populations
olympics = pd.read_csv('athlete_events.csv')
noc = pd.read_csv('noc_regions.csv')
pop = pd.read_csv('WorldPopulation.csv')


#Taking olympics data from 1960 onwards
olympics = olympics[olympics['Year']>=1960]
#Taking only Summer Olympic results
olympics = olympics[olympics['Season']=="Summer"]
#Replacing empty cells in the medal column with No Medal
olympics['Medal'].fillna('No Medal', inplace = True)
#Dropping unnecessary column
noc.drop('notes', axis = 1 , inplace = True)
#Dropping unnecessary columns
pop.drop(['Indicator Name', 'Indicator Code'], axis = 1, inplace = True)
#Dropping column with null values
pop.drop(pop.columns[-1], axis = 1, inplace = True)
#Merging columns for all year's populations into a single column and
#assigning each population its corresponding 'Year' value in the next column
pop = pd.melt(pop,
              id_vars = ['Country', 'Country Code'],
              var_name = 'Year',
              value_name = 'Population')
#Converting the 'Year' column to a numerical value
pop['Year'] = pd.to_numeric(pop['Year'])



#Merging name of country by country code
olympics = olympics.merge(noc, left_on = 'NOC', right_on = 'NOC', how = 'left')
print(olympics.loc[olympics['region'].isnull(),['NOC', 'Team']].drop_duplicates())
#Adding missing values by hand based off above null values
olympics['region'] = np.where(olympics['NOC']=='SGP', 'Singapore', olympics['region'])
olympics['region'] = np.where(olympics['NOC']=='ROT', 'Refugee Olympic Athletes', olympics['region'])
olympics['region'] = np.where(olympics['NOC']=='TUV', 'Tuvalu', olympics['region'])
#Drop unnecessary column
olympics.drop('Team', axis = 1, inplace = True)
#Renaming column to more easily identify
olympics.rename(columns = {'region': 'Team'}, inplace = True)



# Merge to get country code
olympics = olympics.merge(pop[['Country', 'Country Code']].drop_duplicates(), left_on = 'Team', right_on = 'Country', how = 'left')
#Merging population for each athlete by 'Country Code' and year of those Olympic Games
olympics = olympics.merge(pop, left_on = ['Country Code', 'Year'], right_on = ['Country Code', 'Year'], how = 'left')
#Drop unneccessary columns
olympics.drop(['Country_x', 'Country_y'], axis = 1, inplace = True)



#Identifying medal winners
olympics['Medal_Won'] = np.where(olympics.loc[:,'Medal']=='No Medal', 0, 1)



olympics.to_csv("Output.csv")



#Analysis below



#Medals won by year for each team
medal_tally_by_year = olympics.groupby(['Year','Team'])[['Medal_Won']].agg('sum').reset_index()
print(medal_tally_by_year.head())

#Total medals won for each team
medal_tally_pivot = pd.pivot_table(medal_tally_by_year,
                                   values = 'Medal_Won',
                                   index = 'Team',
                                   columns = 'Year',
                                   aggfunc = 'sum',
                                   margins = True).sort_values('All', ascending = False)[1:]
print(medal_tally_pivot.loc[:, 'All'].head())

#Best athletes in their sports
best_in_sport = olympics.groupby(['Team', 'Name', 'Sport'])['Medal_Won'].agg('sum').reset_index()
best_in_sport.sort_values(['Sport', 'Medal_Won'], ascending = [True, False], inplace = True)
did_win = best_in_sport['Medal_Won']>1
best_in_sport = best_in_sport[did_win]
print(best_in_sport.sort_values('Medal_Won', ascending = False).head())

#Maximum, minimum, average and standard deviation of height each year for each country
height_agg = olympics.groupby(['Team', 'Year'])[['Height']].agg(['max', 'min', np.mean, np.std])
print(height_agg.head())

#Maximum, minimum, average and standard deviation of weight each year for each country
weight_agg = olympics.groupby(['Team', 'Year'])[['Weight']].agg(['max', 'min', np.mean, np.std])
print(weight_agg.head())

#Maximum, minimum, average and standard deviation of age each year for each country
age_agg = olympics.groupby(['Team', 'Year'])[['Age']].agg(['max', 'min', np.mean, np.std])
print(age_agg.head())