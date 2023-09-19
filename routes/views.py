# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""

from calendar import weekday
from flask import render_template, url_for, redirect, request, jsonify, current_app, g as app_ctx
from flask_login import login_required
import pandas as pd
import datetime
import time
import pytz
from pandas import DataFrame
from app import app, yHandler
from chart.compute import stat_to_score, roto_score_to_battle_score
from chart.radar_chart import league_radar_charts
from chart.bar_chart import league_bar_chart
import threading

# global variable to check progress in polling requests
PROGRESS_PERCENTAGE = -1
ANALYSIS_RESULT =  {}


def remove_trailing_zero(df):
    df1 = df.astype(str).replace(to_replace=r'\.0*$', value='', regex=True).replace('nan', '')
    return df1



# @app.before_request
# def logging_before():
#     # Store the start time for the request
#     app_ctx.start_time = time.perf_counter()


# @app.after_request
# def logging_after(response):
#     # Get total time in milliseconds
#     total_time = time.perf_counter() - app_ctx.start_time
#     time_in_ms = int(total_time * 1000)
#     # Log the time taken for the endpoint 
#     current_app.logger.info('%s ms %s %s %s', time_in_ms, request.method, request.path, dict(request.args))
#     return response

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@login_required
@app.route('/main')
def main():
    leagues = yHandler.get_leagues()
    return render_template('main.html', leagues = leagues) # should be error for no league

@login_required
@app.route('/<league_id>/polling', defaults={'week': None})
@app.route('/<league_id>/<int:week>/polling')
def analyze(league_id, week):
    global PROGRESS_PERCENTAGE # using a global variable defined on the top of this file

    # print('progress', PROGRESS_PERCENTAGE)
    if PROGRESS_PERCENTAGE == -1:  # not started yet
        PROGRESS_PERCENTAGE = 0

        def analyze(**kwargs):
            '''
            Given a leauge id and the week, retrieve the status from yahoo api and analyze the raw data then generate required data
            '''
            global PROGRESS_PERCENTAGE

            league_id = kwargs.get('league_id', '')
            week = kwargs.get('week', None)
            print(league_id, week)

            leagues = yHandler.get_leagues()

            # determine which week to analyze
            league_key = None
            league_name = None
            min_week = None
            max_week = None
            display_week = None
            for league in leagues:
                if (league_id == league['league_id']):
                    league_key = league['league_key']
                    league_name = league['name']
                    start_week = int(league['start_week'])
                    current_week = int(league['current_week'])

                    min_week = start_week # display in page
                    max_week = current_week # display in page
                    weekday = datetime.datetime.now(pytz.timezone('US/Pacific')).weekday()
                    if weekday <= 1:
                        max_week -= 1

                    if week is None or week < start_week or week > current_week:  # input (week) is not valid, use current week or the previous week 
                        display_week = current_week

                        # if it is first half week (Mon/Tue/Wed/Thu), display previous week as default
                        if weekday <= 3:
                            display_week -= 1
                    else: # input (week) is valid, use it
                        display_week = week
                    
                    break

            # error: didn't find the leauge id
            if (league_key is None):
                print('Error: league not found', league_key)
                return {}


            # get week status and total status for every team
            teams = yHandler.get_league_teams(league_key)
            stat_categories = yHandler.get_game_stat_categories()
            team_names = []
            week_stats = []
            total_stats = []
            stat_names = []
            sort_orders = []

            team_index = 0
            for team in teams:
                # also include team info in the team stats
                team_names.append(team['name'])

                team_key = team['team_key']
                week_stat, data_types, sort_orders = yHandler.get_team_stat(team_key, stat_categories, display_week)
                total_stat, data_types, sort_orders = yHandler.get_team_stat(team_key, stat_categories, 0)
                # print(week_stat)
                # print(total_stat)
                stat_names = week_stat.keys()
                # stat_values = week_stat.values()

                week_stats.append(week_stat)
                total_stats.append(total_stat)

                # update progress percentage, suppose after complete reading data from yahoo, the percentage is 90%.
                # the remaining 10% is for analyze
                team_index += 1
                PROGRESS_PERCENTAGE = int(90*team_index/len(teams))

            print('=== Analyzing data')

            # use a pandas dataframe to calculate ranking value
            week_df = pd.DataFrame(columns=stat_names, index=team_names)
            week_df.columns.name = 'Team Name'
            total_df = pd.DataFrame(columns=stat_names, index=team_names)
            total_df.columns.name = 'Team Name'

            idx = 0
            for team_name in team_names:
                team_stat = week_stats[idx]
                total_stat = total_stats[idx]
                idx += 1
                week_df.loc[team_name] = pd.Series(team_stat)
                total_df.loc[team_name] = pd.Series(total_stat)

            # print(data_types)
            week_df = week_df.astype(data_types)
            total_df = total_df.astype(data_types)
            PROGRESS_PERCENTAGE = 93

            week_score = stat_to_score(week_df, sort_orders)
            total_score = stat_to_score(total_df, sort_orders)
            battle_score = roto_score_to_battle_score(week_score)

            PROGRESS_PERCENTAGE = 95
            bar_chart = league_bar_chart(team_names, week_score['Total'], total_score['Total'], league_name, display_week)
            radar_charts = league_radar_charts(week_score, total_score, display_week)
            
            # format output
            week_score = remove_trailing_zero(week_score)
            total_score = remove_trailing_zero(total_score)
            battle_score = remove_trailing_zero(battle_score)
            PROGRESS_PERCENTAGE = 98

            global ANALYSIS_RESULT
            ANALYSIS_RESULT = {
                'leagues': leagues, # all leagues, used to fill the league list
                'league_id': league_id, # current leagues id
                'team_names': team_names,
                'display_week': display_week,
                'min_week': min_week,
                'max_week': max_week,
                'stat_names': stat_names,
                'week_stats': week_df,
                'total_stats':total_df,
                'week_score': week_score,
                'total_score': total_score,
                'battle_score': battle_score,
                'bar_chart': bar_chart,
                'radar_charts': radar_charts
            }

            PROGRESS_PERCENTAGE = 100


        # create a new thread to run the analysis work
        analyze_thread = threading.Thread(target=analyze, kwargs={
                    'league_id': league_id, 'week': week})
        analyze_thread.start()

        time.sleep(1) 

        return { 'status': 'initiated', 'progress':  PROGRESS_PERCENTAGE }, 200


    elif PROGRESS_PERCENTAGE == 100: # finished
        PROGRESS_PERCENTAGE = -1 # reset 

        return { 'status': 'finished' }, 200

    else:
        time.sleep(1)

        return { 'status': 'in progress', 'progress':  PROGRESS_PERCENTAGE}, 200



@login_required
@app.route('/<league_id>', defaults={'week': None})
@app.route('/<league_id>/<int:week>')
def showresult(league_id, week):
    global ANALYSIS_RESULT
    
    team_number = len(ANALYSIS_RESULT['team_names'])
    tie_score = len(ANALYSIS_RESULT['stat_names']) / 2

    style_top = 'background: linear-gradient(90deg, #5fba7d 100.0%, transparent 100.0%)'
    style_bottom = 'background: linear-gradient(90deg, #d65f5f 100.0%, transparent 100.0%)'

    # highligh max and min
    week_score = ANALYSIS_RESULT['week_score'].style.apply(
    lambda x: [ style_top if float(value) == 1 else
          (style_bottom if float(value) == team_number else 
        '') for value in x])
    # highlight max and min
    total_score = ANALYSIS_RESULT['total_score'].style.apply(
    lambda x: [ style_top if float(value) == 1 else
          (style_bottom if float(value) == team_number else 
        '') for value in x])
    
    # make ithe table pretty with different background color for win/lose/tie
    battle_score = ANALYSIS_RESULT['battle_score'].style.apply(
    lambda x: [ '' if value=='' else
        (style_top if float(value) < tie_score else
          (style_bottom if float(value) > tie_score else 
           'background-color: #ffffd9')) for value in x])

    return render_template('league.html',
        leagues = ANALYSIS_RESULT['leagues'],
        current_league_id=ANALYSIS_RESULT['league_id'],
        current_week=ANALYSIS_RESULT['display_week'],
        min_week = ANALYSIS_RESULT['min_week'],
        max_week = ANALYSIS_RESULT['max_week'],
        week_stats=ANALYSIS_RESULT['week_stats'],
        total_stats=ANALYSIS_RESULT['total_stats'],
        week_rank = week_score,
        total_rank = total_score,
        battle_score= battle_score,
        bar_chart = ANALYSIS_RESULT['bar_chart'],
        radar_charts = ANALYSIS_RESULT['radar_charts'] )


@login_required
@app.route('/<league_key>/<team_id>')
def team(lid, tid):
    pass
