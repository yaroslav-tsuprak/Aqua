import logging
from AquaUtil import AquaUtil
from Database import Database
from StepperMotor import StepperMotor
import RPi.GPIO as GPIO


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("aqua.log"),
        logging.StreamHandler()
    ]
)

# Time parameters
_reset_time1 = 0
_reset_time2 = 1
lighting_enabled = True
lighting_start_hours = 9
lighting_stop_hours = 18
lighting_start_minutes = 0
lighting_gpio = 17
oxygen_enabled = True
oxygen_start_hours = 9
oxygen_stop_hours = 22
oxygen_start_minutes = 0
oxygen_gpio = 27
feeding_enabled = True
_feeding_start_hours = 9
_feeding_stop_hours = 22
_feeding_second_hour = 0
_feeding_number_of = 2
feeding_gpio = 22
# Stepper Motor
in1_gpio = 10
in2_gpio = 9
in3_gpio = 11
in4_gpio = 8
stepper_delay = 0.005
steps = 1024
# Flags
log_enabled = True
debug = True
gpio_support = True
food = False
light = False
oxygen = False
feeding_first_state = False
reset_parameters = False
# Get BD connection
connect = Database()
utils = AquaUtil()
__gpio = GPIO

if gpio_support:
    __gpio.setmode(__gpio.BCM)
    # Off
    __gpio.setup(lighting_gpio, __gpio.IN)
    __gpio.setup(oxygen_gpio, __gpio.IN)
    __gpio.setup(feeding_gpio, __gpio.IN)
    __gpio.setup(in1_gpio, __gpio.IN)
    __gpio.setup(in2_gpio, __gpio.IN)
    __gpio.setup(in3_gpio, __gpio.IN)
    __gpio.setup(in4_gpio, __gpio.IN)


motor = StepperMotor(__gpio, in1_gpio, in2_gpio, in3_gpio, in4_gpio, stepper_delay)

def reset_all_parameters():
    global connect
    global food
    global _feeding_start_hours
    global _feeding_stop_hours
    global _feeding_second_hour
    global feeding_first_state
    global _feeding_number_of
    if log_enabled:
        logging.info("Configuring all parameters...")
    count = connect.select_from_db()
    # Если не кормили еще не разу
    if count == 0:
        # Если должны кормить всего 1 раз
        if _feeding_number_of == 2:
            _feeding_second_hour = utils.getSecondHours(_feeding_start_hours, _feeding_stop_hours)
    elif count == 1:
        if _feeding_number_of == 1:
            # Откормили на сегодня
            food = True
        elif _feeding_number_of == 2:
            _feeding_second_hour = utils.getSecondHours(_feeding_start_hours, _feeding_stop_hours)
            # Покормили только один раз и надо еще один
            feeding_first_state = True
    elif count == 2:
        # Откормили на сегодня
        food = True
    logging.info("First feeding start time at: " + str(_feeding_start_hours))
    if _feeding_number_of > 1:
        logging.info("Second feeding start time at: " + str(_feeding_second_hour))
    # End of reset_all_parameters()


def start_feeding(count):
    if gpio_support:
        if log_enabled:
            logging.info("Starting feeding #" + str(count))
        motor.start(steps)
    connect.save_to_db()
    # End of start_feeding()


def change_state_gpio(_gpio_number, state):
    global __gpio
    if state:
        __gpio.setup(_gpio_number, __gpio.OUT)
        __gpio.output(_gpio_number, True)
    elif not state:
        __gpio.output(_gpio_number, False)
        __gpio.setup(_gpio_number, __gpio.IN)
    # End of change_state_gpio()


logging.info("= Starting Aqua Control Center =")
reset_all_parameters()

while True:
    if lighting_enabled:
        lighting_timer = utils.checkTime(lighting_start_hours, lighting_stop_hours, lighting_start_minutes)
        # Disable lighting
        if light and not lighting_timer:
            if log_enabled:
                logging.info("Lighting - Disabled")
            if gpio_support:
                # Начался новый цикл и нам надо сбросить флаг для ночного сброса параметров
                reset_parameters = False
                # Выключаем GPIO
                change_state_gpio(lighting_gpio, False)
            lighting_timer = False
            light = False
        # Enable lighting
        elif not light and lighting_timer:
            if log_enabled:
                logging.info("Lighting - Enabled")
            if gpio_support:
                # Включаем GPIO
                change_state_gpio(lighting_gpio, True)
            light = True
    else:
        logging.info("Lighting is disabled in config")
    if oxygen_enabled:
        oxygen_timer = utils.checkTime(oxygen_start_hours, oxygen_stop_hours, oxygen_start_minutes)
        # Disable oxygen
        if oxygen and not oxygen_timer:
            if log_enabled:
                logging.info("Oxygen - Disabled")
            if gpio_support:
                # Выключаем GPIO
                change_state_gpio(oxygen_gpio, False)
            oxygen_timer = False
            oxygen = False
        # Enable oxygen
        elif not oxygen and oxygen_timer:
            if log_enabled:
                logging.info("Oxygen - Enabled")
            if gpio_support:
                # Включаем GPIO
                change_state_gpio(oxygen_gpio, True)
            oxygen = True
    else:
        logging.info("Oxygen is disabled in config")
    if feeding_enabled:
        if not food:
            if utils.checkTimeForFeeding(_feeding_start_hours, _feeding_stop_hours):
                if utils.checkHour(_feeding_start_hours) and not feeding_first_state:
                    start_feeding(1)
                    # Выставляем флаг откормлено 1 раз
                    feeding_first_state = True
                    if debug:
                        logging.info("feeding_first_state set to: True")
                elif utils.checkHour(_feeding_second_hour):
                    start_feeding(2)
                    # Выставляем флаг откормлено на сегодня
                    food = True
                    if debug:
                        logging.info("food set to: True")
        else:
            if utils.checkHour(_reset_time1) and not reset_parameters:
                reset_parameters = True
                if debug:
                    logging.info("reset_parameters set to: True")
                reset_all_parameters()
            elif utils.checkHour(_reset_time2) and reset_parameters:
                reset_parameters = False
                food = False
                if debug:
                    logging.debug("reset_parameters set to: False")
                    logging.debug("food set to: False")
    else:
        logging.info("Feeding is disabled in config")
