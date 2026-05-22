from django.db import models
from django.conf import settings

class Genre(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class Movie(models.Model):
    MOVIE = 'movie'
    SERIES = 'series'
    TYPE_CHOICES = [
        (MOVIE, 'Película'),
        (SERIES, 'Serie'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    year = models.IntegerField()
    poster = models.ImageField(upload_to='posters/')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=MOVIE)
    genres = models.ManyToManyField(Genre)
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    featured = models.BooleanField(default=False)
    backdrop = models.ImageField(upload_to='backdrops/', blank=True, null=True)
    

    def __str__(self):
        return self.title
    
class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"