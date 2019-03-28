from datetime import datetime

from django.template import loader
from django.utils import timezone
import pytz
from django.shortcuts import render

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from PLCWeather.models import *

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
      |________________________
      |{xmin}            {xmax}'''


def fillData(arrayOf24Floats, maxTime, minTime):
    maxy = max(arrayOf24Floats)
    miny = min(arrayOf24Floats)

    mint = minTime.strftime("%H:%M")
    maxt = maxTime.strftime("%H:%M")

    rows = []
    for a in range(10):
        rows.append([' ' for b in range(24)])

    scaled = []
    if isinstance(maxy, float):
        if isinstance(miny, float):
            # scale y to 0-10
            for f in arrayOf24Floats:
                if maxy - miny:
                    scaled.append(round(((f - miny) / (maxy - miny)) * 10))
                else:
                    scaled.append(0)


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
                                )


def status(request):
    # latest = timezone.now() - timezone.timedelta(minutes=1)
    latest_stats = list(SystemStats.objects.order_by('-collectionTime'))[0]
    latest_temps = list(TemperatureSensor.objects.order_by('-collectionTime'))[0]

    currentPannelPower = "%.2f" % (latest_stats.panelCurrent * latest_stats.panelVoltage)
    currentBatteryVoltage = "%.2f" % latest_stats.batteryVoltage

    caseTemp = "%.2f" % latest_stats.caseTemp
    lastCollectionTime = str(latest_stats.collectionTime)
    weatherTemp = "%.2f" % latest_temps.tempInF

    pannelPowerGrid = []
    batteryVoltageGrid = []

    for a in range(24):
        powertmp = SystemStats.objects.order_by('-collectionTime').filter(collectionTime__range=(
            timezone.now() - timezone.timedelta(hours=a), timezone.now() - timezone.timedelta(hours=a + 1)))
        if len(powertmp):
            powerSum = round(sum([a.panelVoltage * a.panelPower for a in powertmp]) / len(powertmp))
            batteryVoltageGrid.append(round(sum([a.batteryVoltage for a in powertmp]) / len(powertmp)))
            pannelPowerGrid.append(powerSum)
        else:
            pannelPowerGrid.append('')
            batteryVoltageGrid.append('')

    context = {
        'currentPannelPower': currentPannelPower,
        "currentBatteryVoltage": currentBatteryVoltage,

        "caseTemp": caseTemp,
        "weatherTemp": weatherTemp,
        "lastCollectionTime": lastCollectionTime,

        "panelPowerGraph": fillData(pannelPowerGrid, timezone.now() - timezone.timedelta(hours=24),
                                    timezone.now()),
        "batteryPowerGraph": fillData(batteryVoltageGrid, timezone.now() - timezone.timedelta(hours=24),
                                      timezone.now())
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
