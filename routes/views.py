# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""

from flask import render_template, url_for, redirect, make_response, request
from flask_login import login_required, current_user
import pandas as pd
import datetime
import time
import pytz
from calendar import weekday
from pandas import DataFrame
import os
import matplotlib.pyplot as plt
from pandas.plotting import table 

from app import app, yHandler
from chart.compute import stat_to_score, roto_score_to_battle_score
from chart.radar_chart import league_radar_charts, next_matchup_radar_charts
from chart.bar_chart import league_bar_chart



g_result =  {
     'leagues': None,
     'stat_categories': None,
     'current_league': {}
}


def remove_trailing_zero(df):
    df1 = df.astype(str).replace(to_replace=r'\.0*$', value='', regex=True).replace('nan', '')
    return df1


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


def get_stat_categories():
    global g_result
    stat_categories = []
    if 'stat_categories' in g_result and g_result['stat_categories'] is not None:
        stat_categories = g_result['stat_categories']
    else:
        stat_categories = yHandler.get_game_stat_categories()
        g_result['stat_categories'] = stat_categories

    return stat_categories


def get_leagues():
    global g_result
    leagues = []
    if 'leagues' in g_result and g_result['leagues'] is not None:
        leagues = g_result['leagues']
    else:
        leagues = yHandler.get_leagues()
        g_result['leagues'] = leagues

    return leagues


def get_league_teams(league_id):
    global g_result

    teams = []
    if 'current_league' in g_result and g_result['current_league'] is not None and 'teams' in g_result['current_league'] and g_result['current_league']['teams'] is not None:
        teams = g_result['current_league']['teams']
    else:
        leagues = get_leagues()
        for league in leagues:
            if (league_id == league['league_id']):
                league_key = league['league_key']
                teams = yHandler.get_league_teams(league_key)
                g_result['current_league']['teams'] = teams
                break

    return teams

def get_league_info(league_id, week):
    global g_result
    leagues = get_leagues()

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

            start_date = datetime.datetime.strptime(league['start_date'], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(league['end_date'], '%Y-%m-%d').date()
            today = datetime.datetime.now(pytz.timezone('US/Pacific')).date()

            start_week = int(league['start_week'])
            end_week = int(league['end_week'])
            current_week = int(league['current_week'])

            min_week = start_week # display in page
            max_week = current_week # display in page
            app.logger.debug('league name: {}'.format(league_name))
            app.logger.debug('start week: {}'.format(start_week))
            app.logger.debug('current week: {}'.format( current_week))
            app.logger.debug('end week: {}'.format(end_week ))
            weekday = today.weekday()
            if weekday <= 1 and today < end_date:
                max_week -= 1

            if week is None or week < start_week or week > current_week:  # input (week) is not valid, use current week or the previous week 
                display_week = current_week

                # if it is first half week (Mon/Tue/Wed/Thu), display previous week as default
                if weekday <= 3:
                    display_week -= 1
            else: # input (week) is valid, use it
                display_week = week

            predict_week = current_week + 1
            # if it is Monday, set predict week to current week
            # because this is used for research the matchup
            if weekday < 1:
                predict_week -= 1
            if predict_week > end_week:
                predict_week = end_week


            app.logger.debug('min week: {}'.format(min_week))
            app.logger.debug('max week: {}'.format(max_week))
            app.logger.debug('display week: {}'.format(display_week))
            app.logger.debug('predict week: {}'.format(predict_week))
            
            break

    
    # output to global
    g_result['current_league']['league_id'] = league_id
    g_result['current_league']['league_name'] = league_name
    g_result['current_league']['min_week'] = min_week
    g_result['current_league']['max_week'] = max_week
    g_result['current_league']['display_week'] = display_week
    g_result['current_league']['predict_week'] = predict_week

    return league_id, league_name, min_week, max_week, display_week, predict_week

@app.route('/main')
@login_required
def main():
    leagues = get_leagues()
    return render_template('main.html', leagues = leagues) # should be error for no league

@app.route('/<league_id>/<int:week>/start')
@login_required
def start(league_id, week):
    global g_result

    g_result['current_league'] = {
        'league_id': None,
        'league_name': None,
        'teams': None,
        'min_week': None,
        'max_week': None,
        'display_week': None,
        'stat_names': None,
        'data_types' : None,
        'sort_orders':None,
        'week_stats': None,
        'total_stats': None,
        'week_stats_df': None,
        'total_stats_df': None,
        'week_score_df': None,
        'total_score_df': None,
        'battle_score_df': None,
        'week_bar_chart': None,
        'total_bar_chart': None,
        'radar_charts': None   
    }

    get_league_info(league_id, week)

    app.logger.debug('current league data')
    app.logger.debug(g_result['current_league'])

    return { 'status': 'success' }, 200

@app.route('/<league_id>/teams')
@login_required
def leaguge_teams(league_id):

    teams =  get_league_teams(league_id)
    team_ids = list(map(lambda x: x['team_id'], teams))
        
    return { 'team_ids': team_ids }, 200 

@app.route('/stat/<league_id>/<int:week>/<team_id>')
@login_required
def team_stat(league_id, week, team_id):
    global g_result
    teams =  get_league_teams(league_id)
    stat_categories = get_stat_categories()
    team_names = []
    week_stats = []
    total_stats = []
    stat_names = []
    sort_orders = []

    team_index = 0
    for team in teams:
        if (team_id == team['team_id']):

            if 'current_league' not in g_result or g_result['current_league'] is None:
                g_result['current_league'] = {}

            # get current week stat
            team_key = team['team_key']
            week_stat, data_types, sort_orders, point = yHandler.get_team_stat(team_key, stat_categories, week)

            if 'week_stats' not in g_result['current_league'] or g_result['current_league']['week_stats'] is None:
                g_result['current_league']['week_stats'] = []
            g_result['current_league']['week_stats'].append(week_stat)

            if 'week_points' not in g_result['current_league'] or g_result['current_league']['week_points'] is None:
                g_result['current_league']['week_points'] = []
            g_result['current_league']['week_points'].append(point)

            g_result['current_league']['stat_names'] = week_stat.keys()
            g_result['current_league']['data_types'] = data_types
            g_result['current_league']['sort_orders'] = sort_orders

            # get total stat
            if 'total_stats' not in g_result['current_league'] or g_result['current_league']['total_stats'] is None:
                g_result['current_league']['total_stats'] = []

            total_stat, data_types, sort_orders = yHandler.get_team_stat(team_key, stat_categories, 0)
            g_result['current_league']['total_stats'].append(total_stat)

            break


    return { 'status': 'success' }, 200


@app.route('/<league_id>/<int:week>/analyze')
@login_required
def analyze(league_id, week):
    global g_result

    league_name = g_result['current_league']['league_name']
    stat_names = g_result['current_league']['stat_names']
    week_stats = g_result['current_league']['week_stats']
    week_points = g_result['current_league']['week_points']
    total_stats = g_result['current_league']['total_stats']
    data_types = g_result['current_league']['data_types']
    sort_orders = g_result['current_league']['sort_orders']
    teams = g_result['current_league']['teams']
    team_names = list(map(lambda x: x['name'], teams))

    predict_week = g_result['current_league']['predict_week']
    next_matchups = yHandler.get_league_matchup(teams, week)

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

    week_df = week_df.astype(data_types)
    total_df = total_df.astype(data_types)


    week_score = stat_to_score(week_df, sort_orders)
    total_score = stat_to_score(total_df, sort_orders)
    battle_score = roto_score_to_battle_score(week_score, week_points)

    # bar_chart = league_bar_chart(team_names, week_score['Total'], total_score['Total'], league_name, week)
    # radar_charts = league_radar_charts(week_score, total_score, week)

    # # format output
    # week_score = remove_trailing_zero(week_score)
    # total_score = remove_trailing_zero(total_score)
    # battle_score = remove_trailing_zero(battle_score)

    g_result['current_league']['week_stats_df'] = week_df
    g_result['current_league']['total_stats_df'] = total_df
    g_result['current_league']['week_score_df'] = week_score
    g_result['current_league']['total_score_df'] = total_score
    g_result['current_league']['battle_score_df'] = battle_score

    g_result['current_league']['next_matchups'] = next_matchups
    # g_result['current_league']['bar_chart'] = bar_chart
    # g_result['current_league']['radar_charts'] = radar_charts

    app.logger.debug(' Week {} stats'.format(week))
    app.logger.debug('\t'+ week_df.to_string().replace('\n', '\n\t'))
    app.logger.debug(' Week {} scores'.format(week))
    app.logger.debug('\t'+ week_score.to_string().replace('\n', '\n\t'))
    app.logger.debug(' Week {} batter score'.format(week))
    app.logger.debug('\t'+ battle_score.to_string().replace('\n', '\n\t'))
    app.logger.debug(' Total stats')
    app.logger.debug('\t'+ total_df.to_string().replace('\n', '\n\t'))
    app.logger.debug(' Total stats')
    app.logger.debug('\t'+ total_score.to_string().replace('\n', '\n\t'))


    return { 'status': 'success' }, 200

@app.route('/<league_id>/<int:week>/chart')
@login_required
def chart(league_id, week):
    global g_result

    league_name = g_result['current_league']['league_name']
    week_score = g_result['current_league']['week_score_df']
    total_score = g_result['current_league']['total_score_df']
    battle_score = g_result['current_league']['battle_score_df']
    next_matchups = g_result['current_league']['next_matchups']
    predict_week = g_result['current_league']['predict_week']
    teams = g_result['current_league']['teams']
    team_names = list(map(lambda x: x['name'], teams))

    week_bar_chart = league_bar_chart(week_score, '{} 战力榜 - Week {}'.format(league_name, week))
    total_bar_chart = league_bar_chart(total_score, '{} 战力榜 - Total'.format(league_name))
    radar_charts = league_radar_charts(week_score, total_score, week)
    next_matchup_charts = next_matchup_radar_charts(total_score, next_matchups, predict_week)

    # format output
    week_score = remove_trailing_zero(week_score)
    total_score = remove_trailing_zero(total_score)
    battle_score = remove_trailing_zero(battle_score)

    g_result['current_league']['week_score_df'] = week_score
    g_result['current_league']['total_score_df'] = total_score
    g_result['current_league']['battle_score_df'] = battle_score
    g_result['current_league']['week_bar_chart'] = week_bar_chart
    g_result['current_league']['total_bar_chart'] = total_bar_chart
    g_result['current_league']['radar_charts'] = radar_charts
    g_result['current_league']['next_matchup_charts'] = next_matchup_charts

    return { 'status': 'success' }, 200


@app.route('/<league_id>', defaults={'week': None})
@app.route('/<league_id>/<int:week>')
@login_required
def showresult(league_id, week):
    global g_result
    
    team_number = len(g_result['current_league']['teams'])
    tie_score = len(g_result['current_league']['stat_names']) / 2

    # green background
    style_top = 'background: linear-gradient(90deg, #5fba7d 100.0%, transparent 100.0%)'

    # red background
    style_bottom = 'background: linear-gradient(90deg, #d65f5f 100.0%, transparent 100.0%)'

    # highligh max and min
    week_score = g_result['current_league']['week_score_df'].style.apply(
    lambda x: [ style_top if float(value) == 1 else
          (style_bottom if float(value) == team_number else 
        '') for value in x])
    # highlight max and min
    total_score = g_result['current_league']['total_score_df'].style.apply(
    lambda x: [ style_top if float(value) == 1 else
          (style_bottom if float(value) == team_number else 
        '') for value in x])
    
    # make the table pretty with different background color for win/lose/tie
    battle_score = g_result['current_league']['battle_score_df'].style.apply(
    lambda x: [ '' if value=='' else
        (style_top if float(value) < tie_score else
          (style_bottom if float(value) > tie_score else 
           'background-color: #ffffd9')) for value in x])

    return render_template('league.html',
        leagues = g_result['leagues'],
        current_league_id=g_result['current_league']['league_id'],
        current_week=g_result['current_league']['display_week'],
        min_week = g_result['current_league']['min_week'],
        max_week = g_result['current_league']['max_week'],
        week_stats=g_result['current_league']['week_stats_df'],
        total_stats=g_result['current_league']['total_stats_df'],
        week_rank = week_score,
        total_rank = total_score,
        battle_score= battle_score,
        week_bar_chart = g_result['current_league']['week_bar_chart'],
        total_bar_chart = g_result['current_league']['total_bar_chart'],
        radar_charts = g_result['current_league']['radar_charts'],
        next_matchup_charts = g_result['current_league']['next_matchup_charts'] )

