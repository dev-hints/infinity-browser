from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

# Comprehensive tracker and ad-network blocklist
BLOCKLIST = {
    # Google advertising
    "doubleclick.net", "googleadservices.com", "googlesyndication.com",
    "googletagservices.com", "googletagmanager.com", "adservice.google.com",
    "ads.google.com", "adsystem.com", "pagead2.googlesyndication.com",

    # Facebook / Meta tracking
    "facebook.com/tr", "connect.facebook.net", "graph.facebook.com",
    "pixel.facebook.com",

    # Analytics & tracking
    "scorecardresearch.com", "analytics.yahoo.com", "mc.yandex.ru",
    "hotjar.com", "fullstory.com", "mouseflow.com", "crazyegg.com",
    "segment.com", "segment.io", "mixpanel.com", "amplitude.com",
    "heap.io", "clarity.ms", "optimizely.com", "quantserve.com",
    "quantcount.com", "newrelic.com", "nr-data.net", "bugsnag.com",

    # Advertising networks
    "ad-delivery.net", "ad.doubleclick.net", "ads.yahoo.com",
    "ads.twitter.com", "pubmatic.com", "openx.net", "openx.com",
    "rubiconproject.com", "appnexus.com", "adnxs.com",
    "criteo.com", "criteo.net", "taboola.com", "outbrain.com",
    "revcontent.com", "sharethrough.com", "teads.tv",
    "advertising.com", "adbrite.com", "media.net", "bidswitch.net",
    "indexexchange.com", "casalemedia.com", "sonobi.com",
    "districtm.net", "smartadserver.com", "33across.com",
    "triplelift.com", "yieldbot.com", "spotx.tv", "spotxchange.com",

    # Fingerprinting / supercookies
    "iovation.com", "threatmetrix.com", "sift.com", "signifyd.com",

    # Social media widgets (privacy risk)
    "platform.twitter.com", "widgets.pinterest.com",
    "disqus.com", "disquscdn.com",

    # CDN-delivered trackers
    "cdn.branch.io", "assets.adobedtm.com", "bat.bing.com",
    "analytics.tiktok.com", "log.pinterest.com",
}


class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocklist = BLOCKLIST
        self.blocked_count = 0

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        for domain in self.blocklist:
            if domain in url:
                info.block(True)
                self.blocked_count += 1
                return
