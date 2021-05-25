from django.db import models

class YoutubeMetadata(models.Model):
	videoId = models.CharField(max_length=200, primary_key=True)
	title = models.CharField(max_length=200)
	description = models.CharField(max_length=200)
	publishTimestamp = models.DateTimeField('Publish Timestamp')
	thumbnailUrl = models.CharField(max_length=200)

	class Meta:
	    indexes = [
	        models.Index(fields=['-publishTimestamp'])
	    ]