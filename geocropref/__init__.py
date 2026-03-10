def classFactory(iface):
    from .main_plugin import GeoCropRefPlugin
    return GeoCropRefPlugin(iface)