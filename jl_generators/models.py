# jl_generators/models.py
from django.db import models

class Generator(models.Model):
    slug = models.SlugField(primary_key=True)
    title = models.CharField(max_length=250)
    enabled = models.BooleanField(default=True)
    schedule_cron = models.CharField(max_length=100, blank=True)  # optional (Doku, nicht ausführen)
    output_dir = models.CharField(max_length=500, blank=True)
    symbol_image = models.ImageField(upload_to="generator_icons/", blank=True, null=True)

    def __str__(self): return self.slug

class Run(models.Model):
    generator = models.ForeignKey(Generator, on_delete=models.CASCADE, related_name="runs")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[("success","success"),("error","error")])
    triples = models.IntegerField(default=0)
    artifact_ttl = models.URLField(blank=True)
    log = models.TextField(blank=True)  # traceback / messages

class Artifact(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="artifacts")
    path = models.CharField(max_length=500)
    url = models.URLField(blank=True)

class Config(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
