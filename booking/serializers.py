from rest_framework import serializers
from .models import BookedTicket, ManageSeats, Reservation, UpdateSeats
from django.conf import settings
from datetime import datetime
import datetime
import json
from json import loads, dumps
from .dbquery import DBquery

CORS_HEADERS = {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Origin, Content-Type, X-Auth-Token'}

class PNRTicketSerializer(serializers.Serializer):
    pnr = serializers.CharField(required=False, max_length=250)

    def get(self):
        return DBquery(""" SELECT *
                                    FROM
                                        railway_reservation.booked_ticket  WHERE pnr = {pnr}""".format(pnr='"'+self.validated_data['pnr']+'"')).as_dicts()

class ReservationSerializer(serializers.Serializer):
    pnr = serializers.CharField(required=False, max_length=250)

    def create(self, validated_data):
        result = Reservation.objects.create(pnr = validated_data['pnr'],
                                            created_date = datetime.datetime.now()
                                            )
        return result

class PrintBookedTicketSerializer(serializers.Serializer):
    pnr = serializers.CharField(required=False, max_length=250)
    def get(self):
        return DBquery(""" SELECT *
                                    FROM
                                        railway_reservation.booked_ticket """).as_dicts()

class PrintAvailableTicketSerializer(serializers.Serializer):
    coaches = ["s1", "s2", "s3", "s4"]
    berthPreferences = ["UB", "MB", "LB", "SUB"]

    def get(self):
        seats = {}
        for coach in self.coaches:
            result = DBquery(""" SELECT COUNT(*) AS seat_count
                                        FROM
                                            railway_reservation.booked_ticket
                                        WHERE coach = {coach} AND status = "CNF" or status = "WL" or status= "RAC" """.format(coach='"'+coach+'"')).as_list()[0]
            seats.update({coach: 9 - result}) 
        return seats

class CancelTicketSerializer(serializers.Serializer):
    id = serializers.CharField(required = True)

    def update(self):
        if BookedTicket.objects.filter(id=self.validated_data['id']).filter(status="CNC").count() < 1:
            if BookedTicket.objects.filter(id=self.validated_data['id']).filter(status="RAC").count() > 0:
                RACInfo = self.checkRACorWLTicketToCancel(id = self.validated_data['id'], status="RAC")
                if RACInfo['status'] == "RAC":
                    BookedTicket.objects.filter(id=self.validated_data['id']).update(status="CNC")
                    if BookedTicket.objects.filter(status="WL").count() > 0:
                        idOfWLPerson = self.getRACorWaitingListsDetails(status = "WL")
                        self.updateWLTicket(self.validated_data['id'], idOfWLPerson) 
            elif BookedTicket.objects.filter(id=self.validated_data['id']).filter(status="WL").count() > 0:
                WLInfo = self.checkRACorWLTicketToCancel(id = self.validated_data['id'], status="WL")
                if WLInfo['status'] == "WL":
                    BookedTicket.objects.filter(id=self.validated_data['id']).update(status="CNC")
            elif BookedTicket.objects.filter(id=self.validated_data['id']).filter(status="child").count() > 0:
                childInfo = self.checkRACorWLTicketToCancel(id = self.validated_data['id'], status="child")
                if childInfo['status'] == "child":
                    BookedTicket.objects.filter(id=self.validated_data['id']).update(status="CNC")
            else:
                result = BookedTicket.objects.filter(id=self.validated_data['id']).update(status="CNC")
                if BookedTicket.objects.filter(status="RAC").count() > 0:
                    idOfRACPerson = self.getRACorWaitingListsDetails(status = "RAC")
                    self.updateRACToConfirm(idOfRACPerson)
                if BookedTicket.objects.filter(status="WL").count() > 0:
                    idOfWLPerson = self.getRACorWaitingListsDetails(status = "WL")
                    self.updateWaitingListToRAC(idOfRACPerson, idOfWLPerson) 
                return result
        else:
            raise serializers.ValidationError("The Ticket was already Cancelled.")   

    def updateWLTicket(self, idOfRACPerson, idOfWLPerson):
        RACUserBookedInfo = self.getUserBookedInfo(status="CNC", id = idOfRACPerson)
        result = BookedTicket.objects.filter(id=idOfWLPerson).update(
                                    berth_preference = RACUserBookedInfo['berth_preference'],
                                    status = "RAC",
                                    coach = RACUserBookedInfo['coach'],
                                    seat_no = RACUserBookedInfo['seat_no']
                                    )

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

    def checkRACorWLTicketToCancel(self, id, status):
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

    def validate(self, data):
        cleaned_data = super(BookingTicketSerializer, self).validate(data)
        if self.ticketStatus(status="WL") == 5:
            raise serializers.ValidationError({"error":"All Tickets are Filled."})
        return cleaned_data

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
                    # coach_number = compart
                    seat_no = availableSeat + 1
                    seatAvailability = self.checkSeatBerthAvailable(compart, validated_data)
                    coach_number = seatAvailability['coach']
                    berth = seatAvailability['berth']
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
        # else:
            # return {'err': "ddff"}
            # raise serializers.ValidationError('No Tickets to book')

    def moveToWaitingList(self, status):
        data = {"seat_no": 0, "status": "",}
        if self.ticketStatus(status) < 5:
            data.update({
                "status": status,
                "coach_number": "",
                "seat_no": 0,
                "berth": "WL" 
            })
        return data
        # raise serializers.ValidationError('All Tickets are Full. No Tickets to book')

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
                                    WHERE berth_preference = {berth} AND status = {status} AND
                                        coach = {coach}""".format(berth='"'+berth+'"', coach='"'+coach+'"', status='"CNF"')).as_list()[0]

    def checkSeatBerthAvailable(self, coach, validated_data):
        data = {}
        seat = validated_data['berth_preference']
        if validated_data['age'] < 5:
            data.update({
                "coach": coach,
                "berth": "child"
            })  
            return data
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
                data.update({
                    "coach": coach,
                    "berth": berth
                })  
                return data
            # elif validated_data['age'] > 60 and validated_data['berth_preference'] == "NB" and self.checkBerthPreference(coach, "LB") < 2:
            #     berth = "LB"
            #     return berth
            elif validated_data['age'] > 60 and validated_data['berth_preference'] == "NB":
                for compart in self.coaches:
                    if self.checkBerthPreference(compart, "LB") < 2:
                        data.update({
                        "coach": compart,
                        "berth": "LB"
                        })  
                        return data
                    else:
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
                        data.update({
                        "coach": coach,
                        "berth": berth
                        })  
                        return data
            elif validated_data['gender'] == "female" and validated_data['age'] > 5 and validated_data['berth_preference'] == "NB":
                for compart in self.coaches:
                        if self.checkBerthPreference(compart, "LB") < 2:
                            data.update({
                            "coach": compart,
                            "berth": "LB"
                            })  
                            return data
                        else:
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
                            data.update({
                            "coach": coach,
                            "berth": berth
                            })  
                            return data
               
            # elif validated_data['gender'] == "female" and validated_data['age'] > 5 and validated_data['berth_preference'] == "NB" and self.checkBerthPreference(coach, "LB") < 2:
            #     berth = "LB"
            #     return berth
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
                data.update({
                "coach": coach,
                "berth": berth
                })  
                return data
            else:
                raise serializers.ValidationError('Input which you given for berth preference is wrong')