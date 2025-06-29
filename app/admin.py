from django.contrib import admin
from .models import User, TravelInfo


class CustomUserAdmin(admin.ModelAdmin):  # 改为继承 ModelAdmin
    list_display = ('username', 'sex', 'address', 'createTime')
    search_fields = ('username', 'address')
    list_filter = ('sex', 'createTime')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('sex', 'address', 'avatar', 'textarea')}),
    )


class TravelInfoAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'province', 'price', 'score')
    list_editable = ('level', 'price')
    search_fields = ('title', 'province')
    list_filter = ('level', 'province')
    list_per_page = 20

    fieldsets = (
        ('基本信息', {'fields': ('title', 'level', 'price', 'cover')}),
        ('详情信息', {'fields': ('province', 'detailAddress', 'detailIntro')}),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(TravelInfo, TravelInfoAdmin)