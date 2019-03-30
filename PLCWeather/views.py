from datetime import datetime

from django.template import loader
from django.utils import timezone
import pytz
from django.shortcuts import render

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from PLCWeather.models import *

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
    maxy = max([a for a in arrayOfFloats if isinstance(a, float)])
    miny = min([a for a in arrayOfFloats if isinstance(a, float)])

    # mint = minTime.strftime("%H:%M")
    # maxt = maxTime.strftime("%H:%M")
    mint = str(hoursToGraph) + 'hrs'
    maxt = '  Now'

    rows = []
    for a in range(10):
        rows.append([' ' for b in range(hoursToGraph)])

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
            return graphTemplate.format(ymax="{:6.2f}".format(maxy), ymin="{:6.2f}".format(miny), xmin=mint, xmax=maxt,
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
    # latest = timezone.now() - timezone.timedelta(minutes=1)
    latest_stats = list(SystemStats.objects.order_by('-collectionTime'))[0]
    latest_temps = list(TemperatureSensor.objects.order_by('-collectionTime'))[0]

    currentPanelPower = "%.2f" % (latest_stats.panelCurrent * latest_stats.panelVoltage)
    currentBatteryVoltage = "%.2f" % latest_stats.batteryVoltage
    panelVoltage = "%.2f" % latest_stats.panelVoltage

    caseTemp = "%.2f" % latest_stats.caseTemp
    lastCollectionTime = str(latest_stats.collectionTime)
    weatherTemp = "%.2f" % latest_temps.tempInF

    pannelPowerGrid = []
    batteryVoltageGrid = []

    for a in reversed(range(hoursToGraph)):
        powertmp = SystemStats.objects.order_by('-collectionTime').filter(collectionTime__range=(
            timezone.now() - timezone.timedelta(hours=a + 1), timezone.now() - timezone.timedelta(hours=a)))
        if len(powertmp):
            powerSum = sum([a.panelVoltage * a.panelCurrent for a in powertmp]) / len(powertmp)
            batteryVoltageGrid.append(sum([a.batteryVoltage for a in powertmp]) / len(powertmp))
            pannelPowerGrid.append(powerSum)
        else:
            pannelPowerGrid.append('')
            batteryVoltageGrid.append('')

    context = {
        "panelVoltage": panelVoltage,
        'currentPanelPower': currentPanelPower,
        "currentBatteryVoltage": currentBatteryVoltage,

        "caseTemp": caseTemp,
        "weatherTemp": weatherTemp,
        "lastCollectionTime": lastCollectionTime,

        "panelPowerGraph": fillData(pannelPowerGrid, timezone.now() - timezone.timedelta(hours=24),
                                    timezone.now()),
        "batteryPowerGraph": fillData(batteryVoltageGrid, timezone.now() - timezone.timedelta(hours=24),
                                      timezone.now()),
        "textWidth": str(100 / (2 * (hoursToGraph + 7)))
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

        ss.save()
    except Exception as e:
        print("error bad post system status " + str(e))
    return HttpResponse("done")
