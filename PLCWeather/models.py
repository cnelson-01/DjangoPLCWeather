from django.db import models


class TemperatureSensor(models.Model):
    name = models.CharField(max_length=20)
    tempInF = models.FloatField()
    collectionTime = models.DateTimeField('date/time collected')
    isAverageValue = models.BooleanField()


class SystemStats(models.Model):
    panelVoltage = models.FloatField()
    panelCurrent = models.FloatField()

    batteryVoltage = models.FloatField()

    loadVoltage = models.FloatField()
    loadCurrent = models.FloatField()

    caseTemp = models.FloatField()

    collectionTime = models.DateTimeField("date/time collected")

    isAverageValue = models.BooleanField()
