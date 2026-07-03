from django.contrib import admin
from .models import Movie, Genre, Watchlist, Season, Episode, Review


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'year', 'tier', 'release_date', 'views')
    list_filter = ('type', 'tier', 'featured')
    search_fields = ('title',)
    readonly_fields = ('views',)


admin.site.register(Genre)
admin.site.register(Watchlist)
admin.site.register(Season)
admin.site.register(Episode)
admin.site.register(Review)