from urllib import parse
from django.db import models
from django.core.exceptions import ValidationError


class Video(models.Model):
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=400)
    notes = models.TextField(blank=True, null=True)
    video_id = models.CharField(max_length=40, unique=True)

    def save(self, *args, **kwargs):
        # checks for valid URL with an ID
        # extract the ID + prevent save if invalid or ID not found
        try:
            url_components = parse.urlparse(self.url)
            if url_components.scheme != "https" or url_components.netloc != "www.youtube.com" or url_components.path != "/watch":
                raise ValidationError(f"Invalid YouTube URL {self.url}")

            query_string = url_components.query
            if not query_string:
                raise ValidationError(f"Invalid YouTube URL {self.url}")
            parameters = parse.parse_qs(query_string, strict_parsing=True)
            parameter_list = parameters.get("v")
            if not parameter_list:  # empty string, empty list
                raise ValidationError(f"Invalid YouTube URL parameters {self.url}")
            self.video_id = parameter_list[0]
        except ValueError as e:
            raise ValidationError(f"Unable to parse URL {self.url}") from e

        super().save(*args, **kwargs)

    def __str__(self):
        # string displayed in admin console/when printing model object
        # can return any useful string here. try to truncate to max 200 chars
        return f"ID: {self.pk}, Name: {self.name}, URL: {self.url},\
            Video ID: {self.video_id}, Notes: {self.notes}"
