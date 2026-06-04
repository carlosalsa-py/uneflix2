from django.db import models
from django.conf import settings
from embed_video.fields import EmbedVideoField

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
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    featured = models.BooleanField(default=False)
    backdrop = models.ImageField(upload_to='backdrops/', blank=True, null=True)
    director = models.CharField(max_length=200, blank=True, null=True)
    cast = models.TextField(blank=True, null=True)
    rotten_tomatoes_url = models.URLField(blank=True, null=True)
    imdb_url = models.URLField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True, help_text="Duración en minutos")
    trailer_url = models.URLField(blank=True, null=True, help_text="Pega cualquier enlace de YouTube aquí")

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
    
class Season(models.Model):
    series = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='seasons')
    number = models.IntegerField()

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"{self.series.title} - Temporada {self.number}"

class Episode(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    number = models.IntegerField()
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='episodes/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"T{self.season.number}E{self.number} - {self.title}"