import datetime

from django.db import models
from django.contrib.auth.models import User

class EcAccount(models.Model):
    name = models.CharField(
            max_length=50,
            unique=True,
            )

    def __str__(self) -> str:
        return self.name


class DailyEntry(models.Model):
    created = models.DateTimeField(default=datetime.datetime.now())
    employee = models.ForeignKey(
                User,
                on_delete=models.PROTECT,
                related_name="daily_entry",
                )
    ec_account = models.ManyToManyField(EcAccount, through="EcAccountEntry")

    def __str__(self) -> str:
        return self.created.strftime("%d %B %Y %H:%M:%S %z")

class EcAccountEntry(models.Model):
    daily_entry = models.ForeignKey(
            DailyEntry,
            on_delete=models.CASCADE,
            )
    ec_account = models.ForeignKey(
            EcAccount,
            on_delete=models.CASCADE,
            )
    class AccountType(models.TextChoices):
        CREDIT = "CR", "Credit"
        DEBTOR = "DE", "Debit"

    type = models.CharField(
            max_length=2,
            choices=AccountType.choices,
            default=AccountType.CREDIT,
            )

    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "daily_entry", "ec_account", "type" ], name = "unique_daily_account_entry")
        ]

    def __str__(self) -> str:
        return str(self.ec_account) + " " + str(self.daily_entry)
