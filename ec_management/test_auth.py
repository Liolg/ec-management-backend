import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_data_api_requires_authentication(unauthenticated_api_client):
    response = unauthenticated_api_client.get(reverse('account-list'))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_token_endpoints_remain_public(unauthenticated_api_client, django_user_model):
    django_user_model.objects.create_user(username='jwt-user', password='jwt-password')

    obtain = unauthenticated_api_client.post(
        reverse('token_obtain_pair'),
        {'username': 'jwt-user', 'password': 'jwt-password'},
        format='json',
    )
    refresh = unauthenticated_api_client.post(
        reverse('token_refresh'),
        {'refresh': obtain.data['refresh']},
        format='json',
    )

    assert obtain.status_code == status.HTTP_200_OK
    assert refresh.status_code == status.HTTP_200_OK
