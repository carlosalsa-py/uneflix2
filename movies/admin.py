from django.contrib import admin
from .models import Movie, Genre, Watchlist, Season, Episode, Review

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Watchlist)
admin.site.register(Season)
admin.site.register(Episode)
admin.site.register(Review)