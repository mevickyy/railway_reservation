from django.shortcuts import render
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import BookedTicket, ManageSeats, Reservation, UpdateSeats
from django.http import Http404, HttpResponse, JsonResponse
from .serializers import BookingTicketSerializer, ReservationSerializer, CancelTicketSerializer, PrintBookedTicketSerializer, PrintAvailableTicketSerializer, PNRTicketSerializer
import json
from json import loads, dumps
import uuid
from .dbquery import DBquery


CORS_HEADERS = {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Origin, Content-Type, X-Auth-Token'}
# Create your views here.
class BookTicket(APIView):
    """
    BOOK TICKETS.
    """
    def post(self, request, *args, **kwargs):
        pnr = uuid.uuid4().hex[:6].upper()
        serializer = BookingTicketSerializer(data=request.data, context={'request_length':len(request.data), 'pnr': pnr}, many=True)
        if serializer.is_valid():
            serializer.save()
            self.updateReservation(pnr)
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED, headers=CORS_HEADERS)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST,
            headers=CORS_HEADERS)

    def options(self, request, *args, **kwargs):
        return Response({"msg": "ok"}, status=200,
            headers=CORS_HEADERS)

    def updateReservation(self, pnr):
        serializer = ReservationSerializer(data={"pnr":pnr})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED, headers=CORS_HEADERS)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST, headers=CORS_HEADERS)

    def get(self, request, *args, **kwargs):
        return HttpResponse("Success")

class CancelTicket(APIView):
    """
    CANCEL TICKETS.
    """
    def options(self, request, *args, **kwargs):
        return Response({"msg": "ok"}, status=200,
            headers=CORS_HEADERS)

    def get_object(self, pk):
        try:
           return BookedTicket.objects.get(pk=pk)
        except BookedTicket.DoesNotExist:
           raise Http404

    def put(self, request, pk):
        self.get_object(pk)
        serializer = CancelTicketSerializer(data = {"id": pk})
        if serializer.is_valid():
            serializer.update()
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PrintBookedTicket(APIView):
    """
    PRINT BOOKED TICKETS.
    """
    def options(self, request, *args, **kwargs):
        return Response({"msg": "ok"}, status=200,
            headers=CORS_HEADERS)

    def get(self, request):
        # import ipdb;ipdb.set_trace()
        serializer = PrintBookedTicketSerializer(data = request.GET)
        if serializer.is_valid():
            result = serializer.get()
            return Response(result, status=status.HTTP_201_CREATED, headers=CORS_HEADERS)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST, headers=CORS_HEADERS)


class PrintAvailableTicket(APIView):
    """
    PRINT AVAILABLE TICKETS.
    """
    def options(self, request, *args, **kwargs):
        return Response({"msg": "ok"}, status=200,
            headers=CORS_HEADERS)

    def get(self, request):
        serializer = PrintAvailableTicketSerializer(data = request.GET)
        if serializer.is_valid():
            result = serializer.get()
            return Response(result, status=status.HTTP_201_CREATED, headers=CORS_HEADERS)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST, headers=CORS_HEADERS)

class SearchPNRTickets(APIView):
    def options(self, request, *args, **kwargs):
        return Response({"msg": "ok"}, status=200,
            headers=CORS_HEADERS)

    def get(self, request):
        import ipdb;ipdb.set_trace()
        # BookingTicketSerializer.objects.filter(pnr=)
        # serializer = PNRTicketSerializer(data = request.GET)
        # if serializer.is_valid():
        #     result = serializer.get()
        #     return Response(result, status=status.HTTP_201_CREATED, headers=CORS_HEADERS)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST, headers=CORS_HEADERS)

    