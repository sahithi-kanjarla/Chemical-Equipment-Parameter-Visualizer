from django.urls import path
from .views import api_root, UploadCSVView, HistoryView, DatasetSummaryView

urlpatterns = [
    path('', api_root, name='api-root'),
    path('upload/', UploadCSVView.as_view(), name='upload-csv'),
    path('history/', HistoryView.as_view(), name='history'),
    path('summary/<int:pk>/', DatasetSummaryView.as_view(), name='summary'),
]
