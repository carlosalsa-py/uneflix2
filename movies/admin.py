from django.contrib import admin
from .models import Genre, Movie, Watchlist

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Watchlist)