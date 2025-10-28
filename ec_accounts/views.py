from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Account, Entry
from .serializers import AccountSerializer, EcAccountEntrySerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class EcAccountEntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.prefetch_related('lines__account').all()
    serializer_class = EcAccountEntrySerializer

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        entry = self.get_object()
        # marcar como anulado; para contabilidad real convendría crear asiento de reversión
        entry.voided = True
        entry.save()
        return Response({'status': 'voided'})
