import os
from PyQt6.QtWebEngineCore import QWebEngineUrlSchemeHandler, QWebEngineUrlScheme, QWebEngineUrlRequestJob
from PyQt6.QtCore import QBuffer, QByteArray


def register_infinity_scheme():
    """Call this BEFORE QApplication is created."""
    scheme = QWebEngineUrlScheme(b"infinity")
    scheme.setFlags(
        QWebEngineUrlScheme.Flag.SecureScheme |
        QWebEngineUrlScheme.Flag.LocalScheme |
        QWebEngineUrlScheme.Flag.LocalAccessAllowed |
        QWebEngineUrlScheme.Flag.CorsEnabled
    )
    QWebEngineUrlScheme.registerScheme(scheme)


class InfinitySchemeHandler(QWebEngineUrlSchemeHandler):
    """Handles infinity://newtab → serves new_tab.html content."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_dir = os.path.dirname(os.path.abspath(__file__))

    def requestStarted(self, job: QWebEngineUrlRequestJob):
        url = job.requestUrl()
        host = url.host()  # e.g. "newtab"

        if host == "newtab":
            html_path = os.path.join(self._base_dir, "new_tab.html")
            try:
                with open(html_path, "rb") as f:
                    data = f.read()
            except FileNotFoundError:
                job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
                return

            buf = QBuffer(parent=self)
            buf.setData(QByteArray(data))
            buf.open(QBuffer.OpenModeFlag.ReadOnly)
            job.reply(b"text/html", buf)
        else:
            job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
