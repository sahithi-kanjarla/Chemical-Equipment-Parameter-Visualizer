from django.urls import path
from .views import api_root, UploadCSVView, HistoryView, DatasetSummaryView, ReportView

urlpatterns = [
    path('', api_root, name='api-root'),
    path('upload/', UploadCSVView.as_view(), name='upload-csv'),
    path('history/', HistoryView.as_view(), name='history'),
    path('summary/<int:pk>/', DatasetSummaryView.as_view(), name='summary'),
]


urlpatterns = [
    path('', api_root, name='api-root'),
    path('upload/', UploadCSVView.as_view(), name='upload-csv'),
    path('history/', HistoryView.as_view(), name='history'),
    path('summary/<int:pk>/', DatasetSummaryView.as_view(), name='summary'),
    path('report/<int:pk>/', ReportView.as_view(), name='report'),  # <- new
]

# api/urls.py
from .views import ReportFromSummaryView
# ... existing urlpatterns ...
urlpatterns += [
    path('report-from-summary/', ReportFromSummaryView.as_view(), name='report-from-summary'),
]
