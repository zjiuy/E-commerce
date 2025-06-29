"""
URL configuration for Travel_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#主路由配置文件，不处理用户具体路由，只做请求的分发，即分布式请求处理。具体的请求由各自应用进行处理
from django.contrib import admin #站点
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

from app import views

urlpatterns = [
    path('admin/', admin.site.urls),   #django后台 站点管理
    path('app/',include('app.urls')), #app应用
    path('', views.home, name='home'),  # 添加根 URL 路由，指向 home 视图
    # path('',include('app.urls'))
]

urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

admin.site.site_title = '电商数据分析系统管理端'  # 修改SimpleUI后台管理系统的网站标签页名称
admin.site.site_header = '电商数据分析系统管理端'  # 修改SimpleUI后台管理系统的网站名称：显示在登录页和首页