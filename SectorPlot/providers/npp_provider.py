from PyQt4.QtCore import QUrl, QCoreApplication
from PyQt4.QtNetwork import QNetworkRequest
from functools import partial
from provider_base import ProviderConfig, ProviderBase, ProviderResult
import json


class NPPConfig(ProviderConfig):
    def __init__(self):
        ProviderConfig.__init__(self)
        self.url = None


class NPPProvider(ProviderBase):

    def __init__(self, config):
        ProviderBase.__init__(self, config)

    def _data_retrieved(self, reply):
        result = ProviderResult()
        if reply.error():
            result.set_error(reply.error(), reply.url().toString(), 'NPP REST/File provider')
        # elif reply.attribute(QNetworkRequest.RedirectionTargetAttribute) is not None:  # \
        #     #    and type(reply.attribute(QNetworkRequest.RedirectionTargetAttribute)) == QUrl:
        #     # !! We are being redirected
        #     # http://stackoverflow.com/questions/14809310/qnetworkreply-and-301-redirect
        #     print reply.attribute(QNetworkRequest.RedirectionTargetAttribute).toString()
        #     url = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)  # returns a QUrl
        #     print type(url)
        #     print url.toString()
        #     if url.isValid():  # which is valid contains the new url
        #         # find it and get it
        #         self.config.url = url.toString()
        #         self.get_data()
        #     # delete this reply, else timeouts on Windows
        #     reply.deleteLater()
        #     # return without emitting 'finished'
        #     return
        else:
            print reply.url()
            content = unicode(reply.readAll())
            print content
            result.set_data(json.loads(content), reply.url())
        self.finished.emit(result)
        self.ready = True
        reply.deleteLater()  # else timeouts on Windows

    def get_data(self, path=None):
        if path is not None:
            request = QUrl(self.config.url + path)
        else:
            request = QUrl(self.config.url)
        reply = self.network_manager.get(QNetworkRequest(request))
        reply.finished.connect(partial(self._data_retrieved, reply))

        # this part is needed to be sure we do not return immidiatly
        while not reply.isFinished():
            QCoreApplication.processEvents()
