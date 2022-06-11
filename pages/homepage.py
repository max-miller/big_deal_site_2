import dash
from dash import Dash, dcc, html

welcome_text_1 = '''Short answer: yes.'''
welcome_text_2 = ['''
Welcome to is climate change a big deal, a site dedicated to climate change related visualizations. I wrote about the
original impetus behind the project in a ''', html.A('blog post here.',
href='https://medium.com/a-big-deal/is-climate-change-a-big-deal-a-case-study-for-practical-data-science-28700eafaa0a'),
''' Over time, the project has grown to include a handful of visualization projects. The first is the city climate dashboard
which tracks average maximum, average minimum and number of days over 90 across most major American cities.
Perhaps unsurprisingly, most have gotten warmer in recent years, but it's noisy data, is it possible that the 'trends'
seen are really just artifacts, the results of randomness? Probably not.''']

welcome_text_3 = ['''The next dashboard tries to estimate the energy transition in broad strokes. If the power mix
of the future will largely be wind and solar, how will we handle the large seasonal swings in output? How does the
electrification of things like home heating or transportation affect the situation? You'll notice that if you model future
demand to include home and commercial heating (which is currently mostly provided by gas furnaces) that the yearly
peaks in demand are in the winter, exactly when output from solar is at its lowest. Partly this is meant to demonstrate
the need to develop long term storage solutions, but more than anything it shows just how much growth in renewables
are needed. Solar and wind have grown substantially in the last decade, but they represent only around 10% of total
power generation, and electric demand will go up as home furnaces are replaced by heat pumps and gas powered carvs by
EVs.''']

layout = html.Div([
                    html.H1('Is Climate Change a Big Deal'),
                    html.P(welcome_text_1),
                    html.P(welcome_text_2),
                    html.P(welcome_text_3),
])
