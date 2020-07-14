import json
import requests
import time
import datetime
import RPi.GPIO as GPIO

# set GPIO numbering mode and define output pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(37, GPIO.OUT)  # white light 1
GPIO.setup(38, GPIO.OUT)  # white light 2
GPIO.setup(40, GPIO.OUT)  # orange light

# start up test
GPIO.output(37, False)
time.sleep(0.1)
GPIO.output(38, False)
time.sleep(0.1)
GPIO.output(40, False)
time.sleep(0.1)

GPIO.output(40, True)
print("40 on")
time.sleep(0.5)

GPIO.output(37, True)
print("37 on")
time.sleep(0.5)

GPIO.output(38, True)
print("38 on")
time.sleep(0.5)

GPIO.output(37, False)
print("37 off")
time.sleep(0.5)

GPIO.output(38, False)
print("38 off")
time.sleep(0.5)

GPIO.output(40, False)
print("40 off")
time.sleep(0.5)

# function for calculating the time difference between now and the next transition and sleep for that duration
def sleepTillNextTrans(period):
    timeTillNextTrans = schedule[period].replace(tzinfo=None) - now
    print('sleep: ' + str(timeTillNextTrans.seconds) + ' seconds')
    print()
    sleepBuffer = 5
    time.sleep((timeTillNextTrans.seconds + sleepBuffer))

# function for calculating lighting schedule
def calculate_schedule(date):
    Latitude = 30.678637
    Longitude = -106.927596
    API_URL = 'https://api.sunrise-sunset.org/json?lat=' + str(Latitude) + '&lng=' + str(Longitude) + '&date=' + date + '&formatted=0'
    response = requests.get(API_URL)
    j = json.loads(response.text)
    day_length = j['results']['day_length']
    day_segment = int(day_length / 5)
    sunrise = datetime.datetime.strptime(j['results']['sunrise'], '%Y-%m-%dT%H:%M:%S%z')
    my_dict = {"twilight_begin": datetime.datetime.strptime(j['results']['civil_twilight_begin'], '%Y-%m-%dT%H:%M:%S%z'),
               "sunrise": datetime.datetime.strptime(j['results']['sunrise'], '%Y-%m-%dT%H:%M:%S%z'),
               "morning": sunrise + datetime.timedelta(0, day_segment * 1),
               "afternoon": sunrise + datetime.timedelta(0, day_segment * 4),
               "sunset": datetime.datetime.strptime(j['results']['sunset'], '%Y-%m-%dT%H:%M:%S%z'),
               "twilight_end": datetime.datetime.strptime(j['results']['civil_twilight_end'], '%Y-%m-%dT%H:%M:%S%z'), }
    print()
    print('twilight_begin:  ' + str(my_dict['twilight_begin']))
    print('sunrise:         ' + str(my_dict['sunrise']))
    print('morning:         ' + str(my_dict['morning']))
    print('afternoon:       ' + str(my_dict['afternoon']))
    print('sunset:          ' + str(my_dict['sunset']))
    print('twilight_end:    ' + str(my_dict['twilight_end']))
    print()
    return my_dict

schedule = calculate_schedule('today')

# Turn lights on and off based on the time
try:
    while True:
        now = datetime.datetime.now()
        print(now)
        # twilight_end - all off; get new schedule and sleep until tomorrow twilight begin
        if now > schedule['twilight_end'].replace(tzinfo=None):
            GPIO.output(37, False)
            GPIO.output(38, False)
            GPIO.output(40, False)
            print("all off")
            tomorrow = datetime.datetime(now.year, now.month, (now.day + 1))
            schedule = calculate_schedule(str(tomorrow.date()))
            print("Get ready for a new day!")
            sleepTillNextTrans('twilight_begin')
        # sunset - 1 orange
        elif now > schedule['sunset'].replace(tzinfo=None):
            GPIO.output(37, False)
            GPIO.output(38, False)
            GPIO.output(40, True)
            print("sunset")
            sleepTillNextTrans('twilight_end')
        # afternoon - 1 orange 1 white
        elif now > schedule['afternoon'].replace(tzinfo=None):
            GPIO.output(37, False)
            GPIO.output(38, True)
            GPIO.output(40, True)
            print("afternoon")
            sleepTillNextTrans('sunset')
        # morning - all on
        elif now > schedule['morning'].replace(tzinfo=None):
            GPIO.output(37, True)
            GPIO.output(38, True)
            GPIO.output(40, True)
            print("morning")
            sleepTillNextTrans('afternoon')
        # sunrise - 1 white 1 orange
        elif now > schedule['sunrise'].replace(tzinfo=None):
            GPIO.output(37, True)
            GPIO.output(38, False)
            GPIO.output(40, True)
            print("sunrise")
            sleepTillNextTrans('morning')
        # twilight_begin - 1 orange
        elif now > schedule['twilight_begin'].replace(tzinfo=None):
            GPIO.output(37, False)
            GPIO.output(38, False)
            GPIO.output(40, True)
            print("twilight_begin")
            sleepTillNextTrans('sunrise')
        else:
            print('Somthing went wrong, there is no match\n')
            time.sleep(120)

finally:
    # cleanup the GPIO before finishing :)
    GPIO.output(37, False)
    time.sleep(0.1)
    GPIO.output(38, False)
    time.sleep(0.1)
    GPIO.output(40, False)
    time.sleep(0.1)
    GPIO.cleanup()
