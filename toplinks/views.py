from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from .models import tweetsDB, urlsDB
from decouple import config
from tld import get_tld
import tweepy
import requests
import re
import datetime
from collections import defaultdict
# Create your views here.

consumer_key = config('SOCIAL_AUTH_TWITTER_KEY')
consumer_secret = config('SOCIAL_AUTH_TWITTER_SECRET')


@login_required(login_url="/loginUser")
def home(request):
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user.username)
        social = user.social_auth.get(provider='twitter')

        token = social.extra_data['access_token']
        access_key = token["oauth_token"]
        access_secret = token["oauth_token_secret"]

        print("acess", consumer_key, consumer_secret, access_key, access_secret)

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_key, access_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)

        startDate = datetime.datetime.now() - datetime.timedelta(days=7)

        print("***********new stream started*******************")
        for tweet in tweepy.Cursor(api.home_timeline, tweet_mode="extended", monitor_rate_limit=True).items(20):
            print(tweet.created_at)
            if tweet.created_at > startDate:
                print("inside")
                if tweet.entities['urls']:
                    print(tweet.entities['urls'])
                    if not len(tweetsDB.objects.filter(tweet_id=tweet.id)):
                        print(tweet.id)
                        tweet_put = tweetsDB(
                            user=request.user.username, tweet_id=tweet.id, tweeted_user=tweet.user.screen_name, tweet_text=tweet.full_text, date_time=tweet.created_at)
                        tweet_put.save()
                        for url in tweet.entities['urls']:
                            domain_info = get_tld(
                                url['expanded_url'], as_object=True)
                            print(url)
                            url_put = urlsDB(
                                user=request.user.username, tweeted_user=tweet.user.screen_name, url=url['expanded_url'], domain=domain_info.fld)
                            url_put.save()
            else:
                break

        tweetDataBase = []
        user_dict = defaultdict()
        domain_dict = defaultdict()
        allUrls = []

        q1 = tweetsDB.objects.filter(user=request.user.username)
        for result in q1:
            if result.date_time.replace(tzinfo=None) > startDate.replace(tzinfo=None):
                tweetDataBase.append(
                    [result.tweeted_user, result.tweet_text, result.tweet_id])
        print(tweetDataBase)

        q2 = urlsDB.objects.filter(user=request.user.username)
        print(q2)
        for result in q2:
            user_dict[result.tweeted_user] = user_dict.get(
                result.tweeted_user, 0)+1
            domain_dict[result.domain] = domain_dict.get(result.domain, 0)+1
            allUrls.append(result.url)

        print(user_dict)
        max_url = 0
        max_url_user = []
        for k, v in user_dict.items():
            if v > max_url:
                max_url = v
                max_url_user = [k]
            elif v == max_url:
                max_url_user.append(k)
        print(max_url_user)
        # q3 = urlsDB.objects.all()
        # print(q3)

        print("***********new stream ended*******************")

    return render(request, 'home.html', {"tweetDataBase": tweetDataBase, "max_url_user": max_url_user, "max_url": max_url, "domains": domain_dict, "allUrls": allUrls})


def loginUser(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    else:
        return redirect("/")


def logoutUser(request):
    logout(request)
    return redirect(home)
