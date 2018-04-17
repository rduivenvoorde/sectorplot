from PyQt4.QtCore import QCoreApplication

# Evacuatie=rood
# Onmiddelijke evacuatie=rood
# Schuilen=geel
# Jodiumprofylaxe tot 18 jaar en zwangeren=blauw
# Jodiumprofylaxe volwassenen=licht blauw
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

    # NOTE colors are Web Named Colors from ColorZilla Color Picker firefox extension !
    COUNTER_MEASURES = [
            {'id': 100, 'text': tr('Evacuatie'), 'color': '#ff0000'},
            {'id' :110, 'text': tr('Onmiddelijke evacuatie'), 'color': '#ff0000'},

            {'id' :120, 'text': tr('Schuilen'), 'color': '#ffff00'},
            {'id' :130, 'text': tr('Jodiumprofylaxe tot 18 jaar en zwangeren'), 'color': '#0000ff'},
            {'id' :131, 'text': tr('Jodiumprofylaxe volwassenen'), 'color': '#add8e6'},
            {'id' :140, 'text': tr('Relocatie'), 'color': '#a9a9a9'},

            {'id' :220, 'text': tr('Landbouwmaatregelen'), 'color': '#006400'},
            {'id' :221, 'text': tr('Graasverbod'), 'color': '#006400'},
            {'id' :222, 'text': tr('Sluiten van kassen'), 'color': '#90ee90'},

            {'id' :330, 'text': tr('Voedselbeperking'), 'color': '#d3d3d3'},
            {'id' :331, 'text': tr('Drinkwaterbeperking'), 'color': '#d3d3d3'},
            {'id' :332, 'text': tr('Beregening verbod onbegroeid land/weiland'), 'color': '#d3d3d3'},
            {'id' :333, 'text': tr('Beregening verbod begroeid land/weiland'), 'color': '#d3d3d3'},
            {'id' :334, 'text': tr('Zuiveringsslib verbod'), 'color': '#d3d3d3'},

            {'id' :400, 'text': tr('Overige maatregelen'), 'color': '#d3d3d3'}
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

    def get(self,  id):
        text = ''
        for cm in self.COUNTER_MEASURES:
            if cm['id'] == int(id):
                text = cm['text']
                break
        return text

    def all(self):
        return self.COUNTER_MEASURES

    def list(self):
        list = []
        for cm in self.COUNTER_MEASURES:
            list.append([ cm['id'], cm['text'] ])
        return list


if __name__ == "__main__":

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
    print
    print cm.get(40)