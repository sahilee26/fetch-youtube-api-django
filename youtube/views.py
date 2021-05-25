from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.db.models import Q

from .models import YoutubeMetadata
import json
import requests
from django.core.paginator import Paginator
import time
from threading import Thread

# This function corresponds to the endpoint /youtube and returns the stored video data in a paginated response.
# The response is sorted in descending order of published datetime.
# This endpoint also supports a query parameter to facilitation pagination.
"""
Parameters
----------
page : int, optional
    The page number
"""
def index(request):
    response = []

    # Fetch objects from database in reverse chronological order and store them in data
    data = YoutubeMetadata.objects.all().order_by('-publishTimestamp')

    # Iterate over data and append information of each entry to the response JSON Array
    for i in data:
        entry = {}
        entry['title'] = i.title
        entry['description'] = i.description
        entry['publishedTimestamp'] = str(i.publishTimestamp)
        entry['thumbnailUrl'] = i.thumbnailUrl
        response.append(entry)

    # 10 responses in 1 page
    pageSize = 10
    paginator = Paginator(response, pageSize)

    # Get page parameter from query and render that particular page
    # Defaults to the 1st page
    page = request.GET.get('page', 1)
    finalResponse = paginator.get_page(page)
    template = loader.get_template('youtube/index.html')
    return HttpResponse(template.render({'data': finalResponse}, request))


# This function corresponds to the endpoint /youtube/search?keywords= and returns the video data that matches search query in a paginated response.
# The response is also sorted in descending order of published datetime and this endpoint also supports a query parameter to facilitation pagination.
"""
Parameters
----------
page : int, optional
    The page number
keywords: text
    search query to serach video data
"""
def searchres(request):
    response = []

    # Fetch objects from database in reverse chronological order and store them in data
    data = YoutubeMetadata.objects.all().order_by('-publishTimestamp')

    #Keywords
    keywords = request.GET.get('keywords', 'None')
    data=data.filter(Q(title__icontains=keywords) | Q(description__icontains=keywords))

    # Iterate over data and append information of each entry to the response JSON Array
    for i in data:
        entry = {}
        entry['title'] = i.title
        entry['description'] = i.description
        entry['publishedTimestamp'] = str(i.publishTimestamp)
        entry['thumbnailUrl'] = i.thumbnailUrl
        response.append(entry)

    # 10 responses in 1 page
    pageSize = 10
    paginator = Paginator(response, pageSize)

    # Get page parameter from query and render that particular page
    # Defaults to the 1st page
    page = request.GET.get('page', 1)
    finalResponse = paginator.get_page(page)
    template = loader.get_template('youtube/search.html')
    return HttpResponse(template.render({'data': finalResponse}, request))




# This is the main function which does the job of fetching videos' information asynchronously
def fetchVideos(searchQuery):
    # Read keys.json file and parse the keys
    json_data = open('./keys.json')
    secret_keys = json.load(json_data)

    # Make API Call every 25 seconds
    while(True):
        t = 1
        data = {}
        while('items' not in data):
            if('key' + str(t) in secret_keys['YOUTUBE_DATA_API_KEYS']):
                api_key = secret_keys['YOUTUBE_DATA_API_KEYS']['key' + str(t)]
            else:
                # This implies that none of the supplied API Keys have any quota left for today.
                break
            
            # Query parameters to pass along the GET Request
            queryArguments = {
                'order': 'date',
                'part': 'snippet',
                'maxResults': 25, # maxResults parameter specifies the maximum number of items that should be returned in the result set. Acceptable values are 0 to 50, inclusive. The default value is 5.
                'publishedAfter': '2000-04-04T15:51:12.000Z',
                'q': searchQuery, # Use searchQuery supplied as URL Parameter, defaults to "Friends"
                'type': 'video',
                'key': api_key
            }
            url = 'https://content.googleapis.com/youtube/v3/search'
            r = requests.get(url, params=queryArguments)
            data = r.json()
            # If current API Key does not give results, increment the index to facilitate looping over them
            t = t+1

        print("Data Fetched with search query {}".format(searchQuery) )
        # Store results in database
        for i in data['items']:
            
            entry = {}
            dbRow = YoutubeMetadata()
            dbRow.videoId = i['id']['videoId']
            dbRow.title = i['snippet']['title']
            dbRow.description = i['snippet']['description']
            dbRow.publishTimestamp = str(i['snippet']['publishedAt'])
            dbRow.thumbnailUrl = i['snippet']['thumbnails']['default']['url']
            dbRow.save()
        time.sleep(25)


# This function corresponds to the endpoint /youtube/startFetching and triggers a background asynchronous job to fetch videos

def startFetching(request):

    # Get searchQuery from URL Parameters, defaults to "Friends TV Show"
    searchQuery = request.GET.get("searchQuery", "Friends TV Show")

    # Create a thread to fetch the videos in parallel to other tasks
    # The Thread executes the fetchVideos function which fetches the required videos
    process = Thread(target=fetchVideos, args=(str(searchQuery),))
    process.start()
    response = {
        "success": True,
        "message": "A background asynchronorous job to fetch videos has been triggered."
    }
    return JsonResponse(response)