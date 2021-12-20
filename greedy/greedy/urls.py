from django.urls import path

from game.views import RetrieveTreeData, InsertTreeData

urlpatterns = [
    path(r'v1/query/', RetrieveTreeData.as_view()),
    path(r'v1/insert/', InsertTreeData.as_view()),
]
