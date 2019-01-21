from __future__ import unicode_literals
from django.db import models


class BookedTicket(models.Model):
    name = models.CharField(max_length=250)
    age = models.IntegerField()
    gender = models.CharField(max_length=250)
    berth_preference = models.CharField(max_length=250, blank=True)
    coach = models.CharField(max_length=250)    
    seat_no = models.IntegerField()
    status = models.CharField(max_length=250)
    pnr = models.CharField(max_length=250)
    created_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'booked_ticket'


class ManageSeats(models.Model):
    coach = models.CharField(max_length=250)
    available_seats = models.IntegerField()
    total_seats = models.IntegerField()
    ub = models.IntegerField()
    mb = models.IntegerField()
    lb = models.IntegerField()
    sub = models.IntegerField()
    slb = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'manage_seats'


class Reservation(models.Model):
    pnr = models.CharField(max_length=250)
    created_date = models.DateTimeField()
    modified_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'reservation'


class UpdateSeats(models.Model):
    seat_id = models.IntegerField()
    coach = models.CharField(max_length=250)
    berth_preference = models.CharField(max_length=250)

    class Meta:
        managed = False
        db_table = 'update_seats'
