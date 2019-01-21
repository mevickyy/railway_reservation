from rest_framework import serializers
from .models import BookedTicket, ManageSeats, Reservation, UpdateSeats
from django.conf import settings
from datetime import datetime
import datetime
import json
from json import loads, dumps
from .dbquery import DBquery


class ReservationSerializer(serializers.Serializer):
    pnr = serializers.CharField(required=False, max_length=250)

    def create(self, validated_data):
        result = Reservation.objects.create(pnr = validated_data['pnr'],
                                            created_date = datetime.datetime.now()
                                            )
        return result

class CancelTicketSerializer(serializers.Serializer):
    id = serializers.CharField(required = True)

    def update(self):
        idOfRACPerson = self.getRACorWaitingListsDetails(status = "RAC")  
        idOfWLPerson = self.getRACorWaitingListsDetails(status = "WL")
        result = BookedTicket.objects.filter(id=self.validated_data['id']).update(status="CNC")
        self.updateRACToConfirm(idOfRACPerson)
        self.updateWaitingListToRAC(idOfRACPerson, idOfWLPerson) 
        return result     

    def updateRACToConfirm(self, idOfRACPerson):
        confirmedUserBookedInfo = self.getUserBookedInfo(status="CNC", id = self.validated_data['id'])
        BookedTicket.objects.filter(id=idOfRACPerson).update(
                                    berth_preference = confirmedUserBookedInfo['berth_preference'],
                                    status = "CNF",
                                    coach = confirmedUserBookedInfo['coach'],
                                    seat_no = confirmedUserBookedInfo['seat_no']
                                    )

    def updateWaitingListToRAC(self, idOfRACPerson, idOfWLPerson):
        RACUserBookedInfo = self.getUserBookedInfo(status="CNF", id = idOfRACPerson)
        result = BookedTicket.objects.filter(id=idOfWLPerson).update(
                                    berth_preference = RACUserBookedInfo['berth_preference'],
                                    status = "RAC",
                                    coach = RACUserBookedInfo['coach'],
                                    seat_no = RACUserBookedInfo['seat_no']
                                    )
    
    def getRACorWaitingListsDetails(self, status):
        return DBquery(""" SELECT id
                                    FROM
                                        railway_reservation.booked_ticket
                                    WHERE status = {status} GROUP BY STATUS ORDER BY id ASC 
                                        """.format(status='"'+status+'"')).as_list()[0]

    def getUserBookedInfo(self, status, id):
        return DBquery(""" SELECT *
                                    FROM
                                        railway_reservation.booked_ticket
                                    WHERE id = {id} AND status = {status} 
                                        """.format(id = id, status='"'+status+'"')).as_dict()



class BookingTicketSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)  # Field name made lowercase.
    name = serializers.CharField(required=True, max_length=250)
    age = serializers.IntegerField(required=True)
    gender = serializers.CharField(required=True, max_length=250)
    berth_preference = serializers.CharField(required=False, max_length=250)
    pnr = serializers.CharField(required=False, max_length=250)
    status = serializers.CharField(required=False, max_length=250)
    created_date = serializers.DateTimeField(required=False, allow_null=True)
    coaches = ["s1", "s2", "s3", "s4"]
    berthPreferences = ["UB", "MB", "LB", "SUB"]


    def create(self, validated_data):
        coach_number = ""
        status = ""
        max_seat_count = 7
        seat_no = 7
        status_coach = False        
        BookingRAC = False
        if self.ticketStatus(status="RAC") >= 8:
            data = self.moveToWaitingList(status="WL")
            seat_no = data['seat_no']
            status = data['status']
            berth = data['berth']
            coach_number = data['coach_number']
        else:
            for compart in self.coaches:
                availableSeat = self.checkSeatsCount(compart, status="CNF")
                if availableSeat < max_seat_count:
                    status = "CNF"
                    coach_number = compart
                    seat_no = availableSeat + 1
                    berth = self.checkSeatBerthAvailable(compart, validated_data)
                    if berth == "child":
                        seat_no = 0
                        status = "child"
                    status_coach = True
                    if status_coach is True:
                        break
                else:    
                    if self.ticketStatus(status="CNF") >= 28:
                        availableSeatRAC = self.checkSeatsCount(compart, status="RAC")
                        if availableSeatRAC < 2:
                            status = "RAC"
                            coach_number = compart
                            seat_no = availableSeatRAC + max_seat_count + 1 
                            berth = "SLB" 
                            BookingRAC = True
                            if BookingRAC is True:
                                break
        if self.ticketStatus(status="WL") < 5:
            result = BookedTicket.objects.create(name=validated_data['name'],
                                          age=validated_data['age'],
                                          gender=validated_data['gender'],
                                          berth_preference = berth,
                                          status = status,
                                          pnr = self.context['pnr'],
                                          coach = coach_number,
                                          seat_no = seat_no,
                                          created_date = datetime.datetime.now()
                                          )
            return result
        else:
            raise serializers.ValidationError('No Tickets to book')

    def moveToWaitingList(self, status):
        data = {}
        if self.ticketStatus(status) < 5:
            data.update({
                "status": status,
                "coach_number": "",
                "seat_no": 0,
                "berth": "WL" 
            })
            return data
        raise serializers.ValidationError('Almost All Tickets are Full. No Tickets to book')

    def moveToRAC(self, compart, max_seat_count, status):
        data = {}
        availableSeatRAC = self.checkSeatsCount(compart, status)
        if availableSeatRAC < 2:
            data.update({
                "status": status,
                "coach_number": compart,
                "seat_no": availableSeatRAC + max_seat_count + 1,
                "berth": "SLB" 
            })
        return data

    def checkSeatsCount(self, coach, status):
        return DBquery(""" SELECT COUNT(*) AS seat_count
                                    FROM
                                        railway_reservation.booked_ticket
                                    WHERE status = {status} AND
                                        coach = {coach}""".format(status='"'+status+'"', coach='"'+coach+'"')).as_list()[0]
        
    def ticketStatus(self, status):
        return DBquery(""" SELECT COUNT(*) AS confirmation_count
                                    FROM
                                        railway_reservation.booked_ticket
                                    WHERE status = {status}""".format(status='"'+status+'"')).as_list()[0]

    def checkBerthPreference(self, coach, berth):
        return DBquery(""" SELECT COUNT(*) AS berth_count
                                    FROM
                                        railway_reservation.booked_ticket
                                    WHERE berth_preference = {berth} AND
                                        coach = {coach}""".format(berth='"'+berth+'"', coach='"'+coach+'"')).as_list()[0]

    def checkSeatBerthAvailable(self, coach, validated_data):
        seat = validated_data['berth_preference']
        if validated_data['age'] < 5:
            berth = "child"
            return berth
        else:
            if seat in self.berthPreferences:
                if self.checkBerthPreference(coach, seat) < 2 and seat != "SUB" :
                    berth = seat
                elif seat == "SUB" and self.checkBerthPreference(coach, "SUB") < 1:
                    berth = "SUB"
                elif self.checkBerthPreference(coach, "UB") < 2:
                    berth = "UB"
                elif self.checkBerthPreference(coach, "MB") < 2:
                    berth = "MB"
                elif self.checkBerthPreference(coach, "SUB") < 1:
                    berth = "SUB"
                elif self.checkBerthPreference(coach, "LB") < 2:
                    berth = "LB"
                else:
                    berth = ""
                return berth
            elif validated_data['age'] > 60 and validated_data['berth_preference'] == "NB" and self.checkBerthPreference(coach, "LB") < 2:
                berth = "LB"
                return berth
            elif validated_data['gender'] == "female" and validated_data['age'] > 5 and validated_data['berth_preference'] == "NB" and self.checkBerthPreference(coach, "LB") < 2:
                berth = "LB"
                return berth
            elif seat == "NB":
                if self.checkBerthPreference(coach, "UB") < 2:
                    berth = "UB"    
                elif self.checkBerthPreference(coach, "MB") < 2:
                    berth = "MB"
                elif self.checkBerthPreference(coach, "SUB") < 1:
                    berth = "SUB"
                elif self.checkBerthPreference(coach, "LB") < 2:
                    berth = "LB"
                else:
                    berth = ""
                return berth
            else:
                raise serializers.ValidationError('Input which you given for berth preference is wrong')