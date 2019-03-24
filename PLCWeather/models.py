from django.db import models


class TemperatureSensor(models.Model):
    tempInF = models.FloatField()
    collectionTime = models.DateTimeField('date/time collected')


class SystemStats(models.Model):
    panelVoltage = models.FloatField()
    panelCurrent = models.FloatField()

    batteryVoltage = models.FloatField()

    loadVoltage = models.FloatField()
    loadCurrent = models.FloatField()

    collectionTime = models.DateTimeField("date/time collected")
