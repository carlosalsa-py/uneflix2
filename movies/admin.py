from django.contrib import admin
from .models import Genre, Movie, Watchlist, Season, Episode

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Watchlist)
admin.site.register(Season)
admin.site.register(Episode)