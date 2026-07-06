from django.contrib import admin, messages
from django.shortcuts import render, redirect
from .models import Movie, Genre, Watchlist, Season, Episode, Review
import requests

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'year', 'tier', 'release_date', 'views', 'manual_magnet_status')
    list_filter = ('type', 'tier', 'featured')
    search_fields = ('title',)
    readonly_fields = ('views',)
    actions = ['seleccionar_stream_manual']

    def manual_magnet_status(self, obj):
        return "✅ Manual" if obj.manual_magnet else "❌ Auto"
    manual_magnet_status.short_description = "Magnet"

    @admin.action(description='Seleccionar stream manualmente (Torrentio)')
    def seleccionar_stream_manual(self, request, queryset):
        # 1. Validar que solo se haya seleccionado uno
        if queryset.count() > 1:
            self.message_user(request, "Por favor, selecciona solo una película a la vez.", messages.ERROR)
            return
        
        movie = queryset[0]

        # 2. Validar que tenga ID de IMDb
        if not movie.imdb_id:
            self.message_user(request, f"La película '{movie.title}' no tiene un ID de IMDb configurado.", messages.ERROR)
            return

        # 3. Si el usuario ya eligió un magnet (POST)
        if 'magnet_link' in request.POST:
            magnet = request.POST.get('magnet_link')
            movie.manual_magnet = magnet
            movie.save()
            self.message_user(request, f"Magnet configurado con éxito para: {movie.title}")
            return None # Vuelve a la lista del admin

        # 4. Buscar streams en Torrentio
        url = f"https://torrentio.strem.fun/stream/movie/{movie.imdb_id}.json"
        try:
            response = requests.get(url, timeout=5)
            streams = response.json().get('streams', [])
            
            # Pasamos 'opts' para que el template mantenga el estilo del admin
            return render(request, 'admin/select_stream.html', {
                'movie': movie,
                'streams': streams,
                'opts': self.model._meta,
                'title': f"Seleccionar Stream: {movie.title}"
            })
        except Exception as e:
            self.message_user(request, f"Error conectando con Torrentio: {e}", messages.ERROR)

admin.site.register(Genre)
admin.site.register(Watchlist)
admin.site.register(Season)
admin.site.register(Episode)
admin.site.register(Review)