from django import template
import urllib.parse as urlparse

register = template.Library()

@register.filter(name='youtube_id')
def youtube_id(value):
    if not value:
        return ""
    
    url = urlparse.urlparse(value)
    if url.hostname == 'youtu.be':
        return url.path[1:]
    if url.hostname in ('www.youtube.com', 'youtube.com'):
        if url.path == '/watch':
            p = urlparse.parse_qs(url.query)
            return p.get('v', [None])[0]
        if url.path.startswith(('/embed/', '/v/')):
            return url.path.split('/')[2]
            
    if len(value) == 11:
        return value
        
    return ""