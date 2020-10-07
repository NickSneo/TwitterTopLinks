from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required

# importing models
from .models import tweetsDB, urlsDB

# importing decouple python library for environment variables and hiding secret_api_keys
from decouple import config

# tld - top level domain (python library for extracting domain name)
from tld import get_tld

# tweepy - Python library for accessing the Twitter API
import tweepy

# importing python's built-in modules
import requests
import re
import datetime
from collections import defaultdict


# Set your consumer_key and consumer_secret of twitter api in .env file in root directory
consumer_key = config('SOCIAL_AUTH_TWITTER_KEY')
consumer_secret = config('SOCIAL_AUTH_TWITTER_SECRET')


@login_required(login_url="/loginUser")
def home(request):
    # show home page only when user is authenticated
    if request.user.is_authenticated:
        # get the autheticated user's screen name(username)
        user = User.objects.get(username=request.user.username)
        social = user.social_auth.get(provider='twitter')

        # get the authenticated user's access token's to extract tweets from his home timeline
        token = social.extra_data['access_token']
        access_key = token["oauth_token"]
        access_secret = token["oauth_token_secret"]

        # setting up tweepy (using twitter api keys and user's acess token)
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_key, access_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)

        # startDate = last 7 days from today
        startDate = datetime.datetime.now() - datetime.timedelta(days=7)

        ############# Logic for extracting tweets thorugh twitter api and storing relevant info in Database Starts Here #############

        # twitter api call to get user's home timeline tweets and other info using tweepy
        # use of extended tweet mode to get full text from the tweets
        # monitoring api call rate limit so that it wont exceed twitter's max-call-limit
        # more detail about json response can be found here - https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/overview/tweet-object

        for tweet in tweepy.Cursor(api.home_timeline, tweet_mode="extended", monitor_rate_limit=True).items(100):
            # getting tweets from last 7 days
            if tweet.created_at > startDate:
                # to check if tweet's body contain any url or link
                # if user shared no link in his tweet than tweet.entities['urls'] becomes false
                if tweet.entities['urls']:
                    # it may happend that current tweet is already in our database so we wont save it again
                    # it will remove the scope for duplicate tweets getting saved in database
                    # to chek this I used tweet's unique id
                    if not len(tweetsDB.objects.filter(tweet_id=tweet.id)):

                        # saving this tweet in our database
                        # authenticated user's name, tweet id, user who tweeted, tweet's text and time when this tweet was created
                        # is stored in our tweetsDB (tweets database)
                        tweet_put = tweetsDB(
                            user=request.user.username, tweet_id=tweet.id, tweeted_user=tweet.user.screen_name, tweet_text=tweet.full_text, date_time=tweet.created_at)
                        tweet_put.save()

                        # now as a tweet can contain many links/url
                        # so we will iterate through this list of urls
                        # and store them in our urlsDB (urls database)
                        for url in tweet.entities['urls']:
                            url_put = urlsDB(
                                user=request.user.username, tweeted_user=tweet.user.screen_name, url=url['expanded_url'], )
                            url_put.save()
            else:
                break

        ############# Logic for extracting tweets thorugh twitter api and storing relevant info in Database Ends Here #############

        # Datastructure to store and pass relevant info to home template
        # list to store tweeted user's name, tweet id, and tweet text
        tweetDataBase = []

        # dictionary to store user as key and calculating the frequency of links shared by him/her
        user_dict = defaultdict()

        # dictionary to store domain name as key and calculating the frequency each domain
        domain_dict = defaultdict()

        ############# queries to get info from database starts here ##########################

        # query to get tweets from our tweetDB
        # only those tweets will be extracted which are linked to our Authenticated user's profile(home timeline)
        # suppose many users and client use our webapp then it is important to extract data only from our
        # autheticated user's profile
        q1 = tweetsDB.objects.filter(user=request.user.username)
        # extracting those tweets only which were created in last 7 days
        # and appending it to tweetDataBase list
        # then we will pass this to our home.html template
        for result in q1:
            if result.date_time.replace(tzinfo=None) > startDate.replace(tzinfo=None):
                tweetDataBase.append(
                    [result.tweeted_user, result.tweet_text, result.tweet_id])

        # query to get urls from our urlDB
        # only those urls will be extracted which are linked to our Authenticated user's profile(home timeline)
        # and shared by the authenticated user or his/her friends
        # understanding the above comment and its importance is very crucial
        # suppose many users and client use our webapp then it is important to extract data only from our
        # autheticated user's profile
        q2 = urlsDB.objects.filter(user=request.user.username)

        # processing the query to get the user and his frequqncy of links/urls shared
        # also processing the domain name and its frequency
        # and storing them in user_dict and domain_dict respectively
        for result in q2:
            user_dict[result.tweeted_user] = user_dict.get(
                result.tweeted_user, 0)+1
            domain_name = get_tld(
                result.url, as_object=True).fld
            domain_dict[domain_name] = domain_dict.get(domain_name, 0)+1

        ############## sql queries endd here #########################################

        # logic to get the list of user's who tweeted most links/urls
        # from our user_dict
        # it is important to note that it can happen that many users shared equal no. of max ulrs/links
        # so in this case will make a list of all these users,
        # storing these users' name in max_url_user list
        # storing the count of max urls shared in max_url_count variable
        max_url_count = 0
        max_url_user = []
        for k, v in user_dict.items():
            if v > max_url_count:
                max_url_count = v
                max_url_user = [k]
            elif v == max_url_count:
                max_url_user.append(k)

        # finally passing all these variable to our home.html template

    return render(request, 'home.html', {"tweetDataBase": tweetDataBase, "max_url_user": max_url_user, "max_url": max_url_count, "domains": domain_dict})


# function to handle login request
def loginUser(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    else:
        return redirect("/")


# function to handle logout request
def logoutUser(request):
    logout(request)
    return redirect(home)
