from PyQt4.QtCore import QCoreApplication

# Evacuatie=rood
# Onmiddelijke evacuatie=rood
# Schuilen=geel
# Jodiumprofylaxe tot 18 jaar en zwangeren=blauw
# Jodiumprofylaxe tot 40 jaar en zwangeren=licht blauw
# Relocatie=donker grijs
#
# Landbouwmaatregelen=donker groen
# Graasverbod=donker groen
# Sluiten van kassen=licht groen
#
# Voedselbeperking=licht grijs
# Drinkwaterbeperking=licht grijs
# Beregening verbod onbegroeid land/weiland=licht grijs
# Beregening verbod begroeid land/weiland=licht grijs
# Zuiveringsslib verbod=licht grijs
#
# Overige maatregelen zijn vrije tekst en hebben standaard kleur licht grijs.

class CounterMeasures():

    # noinspection PyMethodMayBeStatic
    def tr(message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SectorPlot', message)

    COUNTER_MEASURES = [
            {'id': 10, 'text': tr('Evacuatie')},
            {'id' :11, 'text': tr('Onmiddelijke evacuatie')},

            {'id' :12, 'text': tr('Schuilen')},
            {'id' :13, 'text': tr('Jodiumprofylaxe tot 18 jaar en zwangeren')},
            {'id' :14, 'text': tr('Jodiumprofylaxe tot 40 jaar en zwangeren')},
            {'id' :15, 'text': tr('Relocatie')},

            {'id' :20, 'text': tr('Landbouwmaatregelen')},
            {'id' :21, 'text': tr('Graasverbod')},
            {'id' :22, 'text': tr('Sluiten van kassen')},

            {'id' :30, 'text': tr('Voedselbeperking')},
            {'id' :31, 'text': tr('Drinkwaterbeperking')},
            {'id' :32, 'text': tr('Beregening verbod onbegroeid land/weiland')},
            {'id' :33, 'text': tr('Beregening verbod begroeid land/weiland')},
            {'id' :34, 'text': tr('Zuiveringsslib verbod')},

            {'id' :40, 'text': tr('Overige maatregelen')}
    ]

    def __str__(self):
        return unicode(self.COUNTER_MEASURES)

    def keys(self):
        keys = []
        for cm in self.COUNTER_MEASURES:
            keys.append(cm['id'])
        return keys

    def values(self):
        values = []
        for cm in self.COUNTER_MEASURES:
            values.append(cm['text'])
        return values

    def all(self):
        return self.COUNTER_MEASURES

    def list(self):
        list = []
        for cm in self.COUNTER_MEASURES:
            list.append([ cm['id'], cm['text'] ])
        return list


# test

cm = CounterMeasures()
print cm
print
print cm.keys()
print
for m in cm.all():
    print "%i %s" % (m['id'], m['text'])
print
print cm.list()