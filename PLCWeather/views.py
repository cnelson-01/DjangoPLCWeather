from datetime import datetime

from django.template import loader
from django.utils import timezone
import pytz
from django.shortcuts import render

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from PLCWeather.models import *
from django.db.models import Avg, AutoField, DateTimeField, BooleanField

hoursToGraph = 48

graphTemplate = '''
{ymax}|{row9}
      |{row8}
      |{row7}
      |{row6}
      |{row5}
      |{row4}
      |{row3}
      |{row2}
      |{row1}
{ymin}|{row0}
      |{xunderscores}
      |{xmin}{xspacing}{xmax}'''


def fillData(arrayOfFloats, maxTime, minTime):
    stripedNonInts = [a for a in arrayOfFloats if isinstance(a, float)]

    # mint = minTime.strftime("%H:%M")
    # maxt = maxTime.strftime("%H:%M")
    mint = str(hoursToGraph) + 'hrs'
    maxt = '  Now'

    rows = []
    for a in range(10):
        rows.append([' ' for b in range(hoursToGraph)])

    if len(stripedNonInts):
        maxy = max(stripedNonInts)
        miny = min(stripedNonInts)

        scaled = []
        if isinstance(maxy, float):
            if isinstance(miny, float):
                # scale y to 0-10
                for f in arrayOfFloats:
                    if isinstance(f, float):
                        if maxy - miny:
                            scaled.append(round(((f - miny) / (maxy - miny)) * 10))
                        else:
                            scaled.append(0)
                    else:
                        scaled.append('')
                for index, value in enumerate(scaled):
                    if value:
                        rows[value - 1][index] = '.'
                    elif value != '':
                        rows[value][index] = '.'
                return graphTemplate.format(ymax="{:6.2f}".format(maxy), ymin="{:6.2f}".format(miny), xmin=mint,
                                            xmax=maxt,
                                            row0=''.join(rows[0]),
                                            row1=''.join(rows[1]),
                                            row2=''.join(rows[2]),
                                            row3=''.join(rows[3]),
                                            row4=''.join(rows[4]),
                                            row5=''.join(rows[5]),
                                            row6=''.join(rows[6]),
                                            row7=''.join(rows[7]),
                                            row8=''.join(rows[8]),
                                            row9=''.join(rows[9]),
                                            xunderscores=''.join('_' for a in range(hoursToGraph)),
                                            xspacing=''.join(' ' for a in range(hoursToGraph - (5 * 2))),
                                            )
    # something went wrong send empty chart
    return graphTemplate.format(ymax="unk   ", ymin="unk   ", xmin=mint, xmax=maxt,
                                row0=''.join(rows[0]),
                                row1=''.join(rows[1]),
                                row2=''.join(rows[2]),
                                row3=''.join(rows[3]),
                                row4=''.join(rows[4]),
                                row5=''.join(rows[5]),
                                row6=''.join(rows[6]),
                                row7=''.join(rows[7]),
                                row8=''.join(rows[8]),
                                row9=''.join(rows[9]),
                                xunderscores=''.join('_' for a in range(hoursToGraph)),
                                xspacing=''.join(' ' for a in range(hoursToGraph - (5 * 2))),
                                )


def status(request):
    doAverage()
    # latest = timezone.now() - timezone.timedelta(minutes=1)
    # latest_stats = list(SystemStats.objects.order_by('-id'))[0]
    latest_stats = SystemStats.objects.last()
    latest_temps = TemperatureSensor.objects.last()

    currentPanelPower = "%.2f" % (latest_stats.panelCurrent * latest_stats.panelVoltage)
    currentBatteryVoltage = "%.2f" % latest_stats.batteryVoltage
    panelVoltage = "%.2f" % latest_stats.panelVoltage

    currentLoad = "%.2f" % latest_stats.loadCurrent

    caseTemp = "%.2f" % latest_stats.caseTemp
    lastCollectionTime = latest_stats.collectionTime
    weatherTemp = "%.2f" % latest_temps.tempInF

    pannelPowerGrid = []
    batteryVoltageGrid = []
    tempGrid = []
    for a in reversed(range(hoursToGraph)):
        powertmp = SystemStats.objects.order_by('-collectionTime').filter(collectionTime__range=(
            timezone.now() - timezone.timedelta(hours=a + 1), timezone.now() - timezone.timedelta(hours=a)))
        temp = TemperatureSensor.objects.order_by('-collectionTime').filter(collectionTime__range=(
            timezone.now() - timezone.timedelta(hours=a + 1), timezone.now() - timezone.timedelta(hours=a)))
        if len(powertmp):
            powerSum = sum([a.panelVoltage * a.panelCurrent for a in powertmp]) / len(powertmp)
            batteryVoltageGrid.append(sum([a.batteryVoltage for a in powertmp]) / len(powertmp))
            pannelPowerGrid.append(powerSum)
        else:
            pannelPowerGrid.append('')
            batteryVoltageGrid.append('')

        if len(temp):
            tempGrid.append(sum([a.tempInF for a in temp]) / len(temp))
        else:
            tempGrid.append("")

    context = {
        "panelVoltage": panelVoltage,
        'currentPanelPower': currentPanelPower,
        "currentBatteryVoltage": currentBatteryVoltage,
        "currentLoad": currentLoad,

        "caseTemp": caseTemp,
        "weatherTemp": weatherTemp,
        "lastCollectionTime": lastCollectionTime,

        "panelPowerGraph": fillData(pannelPowerGrid, timezone.now() - timezone.timedelta(hours=24),
                                    timezone.now()),
        "batteryPowerGraph": fillData(batteryVoltageGrid, timezone.now() - timezone.timedelta(hours=24),
                                      timezone.now()),
        "tempGraph": fillData(tempGrid, timezone.now() - timezone.timedelta(hours=24),
                              timezone.now()),
        "textWidth": str(85 / (2 * (hoursToGraph + 7)))
    }

    template = loader.get_template('status.html')

    return HttpResponse(template.render(context, request))


@csrf_exempt
def logTempData(request):
    tempSensor = TemperatureSensor()
    try:
        tempSensor.tempInF = request.POST["tempInF"]
        tempSensor.collectionTime = timezone.now()
        tempSensor.save()
    except Exception as e:
        print("error bad post temp sensor" + str(e))
    return HttpResponse("done")


def doAverage():
    sstats = SystemStats.objects.all().filter(isAverageValue=False)
    if len(sstats) > 60 * 60:
        ss = SystemStats()
        for f in SystemStats._meta.get_fields():
            if not isinstance(f, AutoField):
                if not isinstance(f, DateTimeField):
                    if not isinstance(f, BooleanField):
                        ss.__setattr__(f.attname, sstats.aggregate(Avg(f.attname))[f.attname + '__avg'])
        ss.collectionTime = sstats[0].collectionTime
        ss.isAverageValue = True
        ss.save()
    for s in sstats:
        s.delete()


@csrf_exempt
def logSystemStatus(request):
    ss = SystemStats()
    try:
        ss.panelVoltage = request.POST["panelVoltage"]
        ss.panelCurrent = request.POST["panelCurrent"]

        ss.batteryVoltage = request.POST["batteryVoltage"]

        ss.loadVoltage = request.POST["loadVoltage"]
        ss.loadCurrent = request.POST["loadCurrent"]

        ss.caseTemp = request.POST["caseTemp"]

        ss.collectionTime = timezone.now()

        ss.isAverageValue = False

        ss.save()

        doAverage()
    except Exception as e:
        print("error bad post system status " + str(e))
    return HttpResponse("done")
