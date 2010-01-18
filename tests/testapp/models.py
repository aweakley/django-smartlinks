import re

from django.db import models
from django.template.defaultfilters import slugify

from smartlinks.utils import words2num

class PersonManager(models.Manager):
    def get_from_smartlink(self, link_text, disambiguator=None, arg=None):
        if disambiguator:
            # disambiguator has to be a number
            try:
                no = int(disambiguator)
            except ValueError:
                raise Person.DoesNotExist
            return self.model.objects.get(name__iexact=link_text, no=no)
        return self.model.objects.get(name__iexact=link_text)
        
    def smartlink_fallback(self, link_text, disambiguator=None, arg=None):
        return '<cite class="unresolved">%s</cite>' % link_text


class Person(models.Model):
    name = models.CharField(max_length=200)
    no = models.IntegerField(max_length=5)
    slug = models.SlugField(max_length=200, unique=True)
    
    objects = PersonManager()
        
    def smartlink(self, search_term):
        return '<a href="/person/%s/">%s</a>' % (self.slug, search_term)
    
    def save(self, force_insert=False):
        if not self.no:
            if not Person.objects.filter(name__iexact=self.name).count():
                self.no = 1
            else:
                self.no = Person.objects.filter(name__iexact=self.name).order_by('-no')[0].no + 1
        if not self.slug:
            self.slug = slugify(self.name + u" %s" % self.no)
        super(Person, self).save(force_insert=False)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.no)

class TitleManager(models.Manager):
    def get_from_smartlink(self, link_text, disambiguator=None, arg=None):
        year_pointer = re.compile(r"\(\s*(\d+)\s*\)")
        if disambiguator:
            # disambiguator has to be a number
            try:
                year = int(disambiguator)
            except ValueError:
                raise Title.DoesNotExist
            return self.model.objects.get(name__iexact=link_text, year=year)
        try:
            return self.model.objects.get(name__iexact=link_text)
        except (self.model.DoesNotExist, self.model.MultipleObjectsReturned), e:
            match = year_pointer.search(link_text)
            if match:
                return self.model.objects.get(name__iexact=link_text[:match.start()].strip(), year=match.group(1))
            raise e
        
    def smartlink_fallback(self, link_text, disambiguator=None, arg=None):
        return '<cite class="unresolved">%s</cite>' % link_text

class Title(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    year = models.IntegerField(max_length=10)
    director = models.ForeignKey(Person)
    
    objects = TitleManager()
    
    def get_absolute_url(self):
        return "/title/%s/" % self.slug
        
    def save(self, force_insert=False):
        if not self.slug:
            self.slug = slugify(self.name+u" (%s)" % self.year)
        super(Title, self).save(force_insert=False)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.year)
        
class ClipManager(models.Manager):
    def get_from_smartlink(self, link_text, disambiguator=None, arg=None):
        # disambiguator is used to distinguish movies from one another 
        matcher = re.compile(r"clip (?P<ClipNumber>.+?) (from|of) (?P<FilmName>.+)", re.IGNORECASE)
        m = matcher.match(link_text)
        
        if m:
            # Clip <number> of <film name>
            
            # first token has to be a movie identifier 
            # and the second one has to be a clip number
            number = m.group("ClipNumber")
            try:
                number = words2num(number)
            except ValueError:
                raise self.model.DoesNotExist
            try:
                film = Title.objects.get_from_smartlink(m.group("FilmName"), disambiguator=disambiguator)
            except (Title.DoesNotExist):
                raise self.model.DoesNotExist
            except (Title.MultipleObjectsReturned):
                raise self.model.MultipleObjectsReturned
            return self.model.objects.get(film=film, number=number)
            
            
        # otherwise we shall hope that film is defined through the argument passed to the filter
        if arg:
            if link_text.lower().startswith("clip "):
                link_text = link_text[len("clip "):]
            try:
                link_text = words2num(link_text)
            except ValueError:
                raise self.model.DoesNotExist
            return self.model.objects.get(film=arg, number=link_text)
        else:
            raise self.model.DoesNotExist
        
    def get_from_smartembed(self, slug, disambiguator, arg=None):
        try:
            film = Title.objects.get(slug__iexact=slug)
        except (Title.DoesNotExist):
            raise self.model.DoesNotExist
        except (Title.MultipleObjectsReturned):
            raise self.model.MultipleObjectsReturned
        return self.model.objects.get(film=film, number=disambiguator)

class Clip(models.Model):
    film = models.ForeignKey(Title)
    number = models.IntegerField(max_length=10)
    keyframe = models.CharField(max_length=100, blank=True, null=True)
    video = models.CharField(max_length=100, blank=True, null=True)
    
    objects = ClipManager() 
    
    def get_video(self):
        return '<embed type="video">%s</embed>' % self.video
        
    def get_keyframe(self):
        return '<img src="%s" />' % self.keyframe
    
    def smartlink(self, search_term):
        return '<a href="%sclip/%s/">%s</a>' % (self.film.get_absolute_url(), self.number, search_term)