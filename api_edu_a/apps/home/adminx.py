import xadmin
from xadmin import views

from home.models import Banner, Navigation


class BaseSetting(object):
    """xadmin的基本配置"""
    enable_themes = True  # 开启主题切换功能
    use_bootswatch = True


xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSettings(object):
    """xadmin的全局配置"""
    site_title = "二十四桥明月夜"  # 设置站点标题
    site_footer = "北京天安门有限公司"  # 设置站点的页脚
    menu_style = "accordion"  # 设置菜单折叠


xadmin.site.register(views.CommAdminView, GlobalSettings)


# 将banner注册到后台
class BannerInfo(object):
    list_display = ['title', "orders", "is_show"]


xadmin.site.register(Banner, BannerInfo)


class NavigationInfo(object):
    list_display = ['title', "orders", "is_show", 'position']


xadmin.site.register(Navigation, NavigationInfo)
